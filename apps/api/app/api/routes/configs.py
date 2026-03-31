import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.device import Device
from app.models.config import ConfigVersion, ConfigDiff

router = APIRouter(prefix="/api/devices", tags=["configs"])


@router.get("/{device_id}/config/versions")
async def get_config_versions(
    device_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    cv_result = await db.execute(
        select(ConfigVersion)
        .where(ConfigVersion.device_id == device_id)
        .order_by(ConfigVersion.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    versions = cv_result.scalars().all()

    return {
        "data": [
            {
                "id": str(v.id),
                "device_id": str(v.device_id),
                "timestamp": v.timestamp.isoformat(),
                "git_commit_hash": v.git_commit_hash,
                "config_hash": v.config_hash,
                "config_path": v.config_path,
                "config_size_bytes": v.config_size_bytes,
            }
            for v in versions
        ],
        "meta": {"total": len(versions), "limit": limit, "offset": offset},
    }


@router.get("/{device_id}/config/diff/{diff_id}")
async def get_config_diff(
    device_id: uuid.UUID,
    diff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(ConfigDiff).where(ConfigDiff.id == diff_id, ConfigDiff.device_id == device_id)
    )
    diff = result.scalar_one_or_none()
    if not diff:
        raise HTTPException(status_code=404, detail="Config diff not found")

    dev_result = await db.execute(select(Device).where(Device.id == device_id))
    device = dev_result.scalar_one_or_none()

    prev_version = None
    if diff.previous_config_version_id:
        pv_result = await db.execute(
            select(ConfigVersion).where(ConfigVersion.id == diff.previous_config_version_id)
        )
        pv = pv_result.scalar_one_or_none()
        if pv:
            prev_version = {
                "id": str(pv.id),
                "timestamp": pv.timestamp.isoformat(),
                "git_commit_hash": pv.git_commit_hash,
            }

    cv_result = await db.execute(
        select(ConfigVersion).where(ConfigVersion.id == diff.current_config_version_id)
    )
    curr_version_obj = cv_result.scalar_one_or_none()
    curr_version = None
    if curr_version_obj:
        curr_version = {
            "id": str(curr_version_obj.id),
            "timestamp": curr_version_obj.timestamp.isoformat(),
            "git_commit_hash": curr_version_obj.git_commit_hash,
        }

    summary_parts = []
    if diff.semantic_summary:
        for s in diff.semantic_summary:
            summary_parts.append(s.get("reason", ""))

    return {
        "data": {
            "id": str(diff.id),
            "device_id": str(diff.device_id),
            "device_hostname": device.hostname if device else None,
            "timestamp": diff.timestamp.isoformat(),
            "previous_version": prev_version,
            "current_version": curr_version,
            "diff_text": diff.diff_text,
            "lines_added": diff.lines_added,
            "lines_removed": diff.lines_removed,
            "lines_changed": diff.lines_changed,
            "semantic_summary": diff.semantic_summary or [],
            "suspicion_level": diff.suspicion_level,
            "summary": "; ".join(summary_parts) if summary_parts else None,
            "config_source": (curr_version_obj.metadata_ or {}).get("config_source") if curr_version_obj else "simulation",
            "redacted": bool((curr_version_obj.metadata_ or {}).get("redacted")) if curr_version_obj else False,
        }
    }


@router.get("/{device_id}/config/content")
async def get_config_content(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    from app.main import get_config_git_service

    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    cv_result = await db.execute(
        select(ConfigVersion)
        .where(ConfigVersion.device_id == device_id)
        .order_by(ConfigVersion.timestamp.desc())
        .limit(1)
    )
    latest_cv = cv_result.scalar_one_or_none()

    content = ""
    if latest_cv:
        git_service = get_config_git_service()
        content = git_service.get_config_at_commit(
            device.hostname, latest_cv.git_commit_hash
        ) or ""

    return {
        "data": {
            "device_id": str(device.id),
            "hostname": device.hostname,
            "version_id": str(latest_cv.id) if latest_cv else None,
            "timestamp": latest_cv.timestamp.isoformat() if latest_cv else None,
            "git_commit_hash": latest_cv.git_commit_hash if latest_cv else None,
            "content": content,
        }
    }
