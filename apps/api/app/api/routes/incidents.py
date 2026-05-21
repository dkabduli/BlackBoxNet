import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.device import Device
from app.models.event import Event
from app.models.config import ConfigDiff
from app.models.incident import Incident, IncidentEvent, IncidentAffectedDevice
from app.services.correlation_engine import CorrelationEngine

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("")
async def list_incidents(
    scenario_id: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = select(Incident)
    if scenario_id:
        query = query.where(Incident.scenario_id == scenario_id)
    if status:
        query = query.where(Incident.status == status)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.order_by(Incident.start_time.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    incidents = result.scalars().all()

    items = []
    for inc in incidents:
        evt_count_result = await db.execute(
            select(func.count()).where(IncidentEvent.incident_id == inc.id)
        )
        event_count = evt_count_result.scalar()

        dev_count_result = await db.execute(
            select(func.count()).where(IncidentAffectedDevice.incident_id == inc.id)
        )
        affected_count = dev_count_result.scalar()

        root_device = None
        if inc.root_device_id:
            rd_result = await db.execute(
                select(Device).where(Device.id == inc.root_device_id)
            )
            rd = rd_result.scalar_one_or_none()
            if rd:
                root_device = {"id": str(rd.id), "hostname": rd.hostname}

        items.append({
            "id": str(inc.id),
            "scenario_id": inc.scenario_id,
            "title": inc.title,
            "start_time": inc.start_time.isoformat(),
            "end_time": inc.end_time.isoformat() if inc.end_time else None,
            "status": inc.status,
            "affected_scope": inc.affected_scope,
            "root_device": root_device,
            "summary": inc.summary,
            "suspicion_summary": inc.suspicion_summary,
            "event_count": event_count,
            "affected_device_count": affected_count,
            "created_at": inc.created_at.isoformat(),
        })

    return {"data": items, "meta": {"total": total, "limit": limit, "offset": offset}}


@router.get("/{incident_id}")
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    root_device = None
    if incident.root_device_id:
        rd_result = await db.execute(
            select(Device).where(Device.id == incident.root_device_id)
        )
        rd = rd_result.scalar_one_or_none()
        if rd:
            root_device = {"id": str(rd.id), "hostname": rd.hostname,
                          "vendor": rd.vendor, "role": rd.role}

    ad_result = await db.execute(
        select(IncidentAffectedDevice).where(IncidentAffectedDevice.incident_id == incident.id)
    )
    affected_devs = ad_result.scalars().all()

    affected_devices = []
    for ad in affected_devs:
        dev_result = await db.execute(select(Device).where(Device.id == ad.device_id))
        dev = dev_result.scalar_one_or_none()
        if dev:
            affected_devices.append({
                "device_id": str(dev.id),
                "hostname": dev.hostname,
                "impact_level": ad.impact_level,
            })

    ie_result = await db.execute(
        select(IncidentEvent).where(IncidentEvent.incident_id == incident.id)
    )
    incident_events = ie_result.scalars().all()
    event_ids = [ie.event_id for ie in incident_events]

    by_type: dict[str, int] = {}
    if event_ids:
        events_result = await db.execute(
            select(Event).where(Event.id.in_(event_ids))
        )
        events = events_result.scalars().all()
        for e in events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1

    return {
        "data": {
            "id": str(incident.id),
            "scenario_id": incident.scenario_id,
            "title": incident.title,
            "start_time": incident.start_time.isoformat(),
            "end_time": incident.end_time.isoformat() if incident.end_time else None,
            "status": incident.status,
            "affected_scope": incident.affected_scope,
            "root_device": root_device,
            "summary": incident.summary,
            "suspicion_summary": incident.suspicion_summary,
            "affected_devices": affected_devices,
            "event_summary": {"total": len(event_ids), "by_type": by_type},
            "created_at": incident.created_at.isoformat(),
            "updated_at": incident.updated_at.isoformat(),
        }
    }


@router.get("/{incident_id}/timeline")
async def get_incident_timeline(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    ie_result = await db.execute(
        select(IncidentEvent).where(IncidentEvent.incident_id == incident_id)
    )
    incident_events = ie_result.scalars().all()
    ie_map = {ie.event_id: ie for ie in incident_events}

    event_ids = list(ie_map.keys())
    if not event_ids:
        return {"data": {"incident_id": str(incident_id), "events": [], "meta": {}}}

    events_result = await db.execute(
        select(Event).where(Event.id.in_(event_ids)).order_by(Event.timestamp)
    )
    events = events_result.scalars().all()

    timeline_events = []
    for event in events:
        ie = ie_map.get(event.id)
        dev_result = await db.execute(
            select(Device).where(Device.id == event.device_id)
        )
        device = dev_result.scalar_one_or_none()

        config_diff_data = None
        if event.related_config_diff_id:
            diff_result = await db.execute(
                select(ConfigDiff).where(ConfigDiff.id == event.related_config_diff_id)
            )
            diff = diff_result.scalar_one_or_none()
            if diff:
                summary_text = ""
                if diff.semantic_summary:
                    parts = []
                    for s in diff.semantic_summary:
                        parts.append(s.get("reason", ""))
                    summary_text = "; ".join(parts)

                config_diff_data = {
                    "diff_id": str(diff.id),
                    "summary": summary_text,
                    "suspicion_level": diff.suspicion_level,
                }

        timeline_events.append({
            "id": str(event.id),
            "device_id": str(event.device_id),
            "device_hostname": device.hostname if device else "unknown",
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "severity": event.severity,
            "title": event.title,
            "description": event.description,
            "config_diff": config_diff_data,
            "is_primary_cause": ie.is_primary_cause if ie else False,
            "relevance_score": float(ie.relevance_score) if ie else 1.0,
            "metadata": event.metadata_ or {},
        })

    meta = {}
    if timeline_events:
        meta = {
            "total_events": len(timeline_events),
            "time_span": {
                "start": timeline_events[0]["timestamp"],
                "end": timeline_events[-1]["timestamp"],
            },
        }

    return {"data": {"incident_id": str(incident_id), "events": timeline_events, "meta": meta}}


@router.get("/{incident_id}/correlation")
async def get_incident_correlation(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    correlation = CorrelationEngine(db)
    data = await correlation.get_correlation_data(incident_id)
    if not data:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"data": data}
