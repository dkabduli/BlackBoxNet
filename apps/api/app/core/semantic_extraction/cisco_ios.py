import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SemanticChange:
    change_type: str
    entity: str
    action: str
    details: dict[str, Any]
    suspicion_level: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_type": self.change_type,
            "entity": self.entity,
            "action": self.action,
            "details": self.details,
            "suspicion_level": self.suspicion_level,
            "reason": self.reason,
        }


class CiscoIOSExtractor:
    PATTERNS = {
        "acl_extended": re.compile(
            r"^access-list\s+(\d+)\s+(permit|deny)\s+(ip|tcp|udp|icmp)\s+(.+)$"
        ),
        "interface_acl": re.compile(
            r"^\s+ip\s+access-group\s+(\S+)\s+(in|out)$"
        ),
        "interface_ip": re.compile(
            r"^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)"
        ),
        "hostname": re.compile(r"^hostname\s+(\S+)$"),
        "interface_start": re.compile(r"^interface\s+(\S+)$"),
        "description": re.compile(r"^\s+description\s+(.+)$"),
    }

    def extract_changes(
        self, diff_text: str, old_config: str, new_config: str
    ) -> list[SemanticChange]:
        changes: list[SemanticChange] = []

        old_data = self._parse_config(old_config)
        new_data = self._parse_config(new_config)

        changes.extend(self._compare_acls(old_data, new_data))
        changes.extend(self._compare_interface_acls(old_data, new_data))
        changes.extend(self._compare_interface_ips(old_data, new_data))
        changes.extend(self._compare_ospf_timers(old_config, new_config))
        changes.extend(self._compare_route_maps(old_config, new_config))
        changes.extend(self._compare_stp_priority(old_config, new_config))

        if old_data.get("hostname") != new_data.get("hostname"):
            if old_data.get("hostname") and new_data.get("hostname"):
                changes.append(self._create_hostname_change(old_data, new_data))

        return changes

    def _parse_config(self, config: str) -> dict[str, Any]:
        data: dict[str, Any] = {"hostname": None, "acls": {}, "interfaces": {}}
        current_interface = None

        for line in config.split("\n"):
            line = line.rstrip()

            m = self.PATTERNS["hostname"].match(line)
            if m:
                data["hostname"] = m.group(1)
                continue

            m = self.PATTERNS["interface_start"].match(line)
            if m:
                current_interface = m.group(1)
                data["interfaces"][current_interface] = {}
                continue

            if line.strip() == "!" or line.strip() == "":
                current_interface = None
                continue

            if current_interface:
                m = self.PATTERNS["interface_acl"].match(line)
                if m:
                    data["interfaces"][current_interface]["acl"] = m.group(1)
                    data["interfaces"][current_interface]["acl_direction"] = m.group(2)
                    continue

                m = self.PATTERNS["interface_ip"].match(line)
                if m:
                    data["interfaces"][current_interface]["ip"] = m.group(1)
                    data["interfaces"][current_interface]["netmask"] = m.group(2)
                    continue

                m = self.PATTERNS["description"].match(line)
                if m:
                    data["interfaces"][current_interface]["description"] = m.group(1)
                    continue

            m = self.PATTERNS["acl_extended"].match(line)
            if m:
                acl_num = m.group(1)
                action = m.group(2)
                protocol = m.group(3)
                rest = m.group(4)

                if acl_num not in data["acls"]:
                    data["acls"][acl_num] = []

                data["acls"][acl_num].append(
                    {
                        "action": action,
                        "protocol": protocol,
                        "params": rest,
                        "line": line,
                    }
                )

        return data

    def _compare_acls(
        self, old_data: dict, new_data: dict
    ) -> list[SemanticChange]:
        changes: list[SemanticChange] = []

        for acl_num in new_data["acls"]:
            if acl_num not in old_data["acls"]:
                changes.append(
                    self._create_acl_change(
                        acl_num, new_data["acls"][acl_num], "added"
                    )
                )

        for acl_num in old_data["acls"]:
            if acl_num not in new_data["acls"]:
                changes.append(
                    self._create_acl_change(
                        acl_num, old_data["acls"][acl_num], "removed"
                    )
                )

        for acl_num in new_data["acls"]:
            if acl_num in old_data["acls"]:
                if old_data["acls"][acl_num] != new_data["acls"][acl_num]:
                    changes.append(
                        self._create_acl_change(
                            acl_num,
                            new_data["acls"][acl_num],
                            "modified",
                            old_rules=old_data["acls"][acl_num],
                        )
                    )

        return changes

    def _create_acl_change(
        self,
        acl_num: str,
        rules: list[dict],
        action: str,
        old_rules: list[dict] | None = None,
    ) -> SemanticChange:
        has_deny_before_permit = False
        denied_subnet = None

        for i, rule in enumerate(rules):
            if rule["action"] == "deny":
                for later_rule in rules[i + 1 :]:
                    if later_rule["action"] == "permit":
                        has_deny_before_permit = True
                        parts = rule["params"].split()
                        if len(parts) >= 2:
                            denied_subnet = self._wildcard_to_cidr(parts[0], parts[1])
                        break

        suspicion_level = "low"
        reason = f"ACL {acl_num} {action}"

        if has_deny_before_permit and denied_subnet:
            suspicion_level = "high"
            reason = f"Deny rule added before permit affecting subnet {denied_subnet}"
        elif action == "added":
            suspicion_level = "medium"
            reason = f"New ACL {acl_num} created"
        elif action == "removed":
            suspicion_level = "medium"
            reason = f"ACL {acl_num} removed"

        details: dict[str, Any] = {
            "acl_number": acl_num,
            "rules": [r["line"] for r in rules],
            "has_deny_before_permit": has_deny_before_permit,
            "denied_subnet": denied_subnet,
        }

        if old_rules:
            details["old_rules"] = [r["line"] for r in old_rules]

        return SemanticChange(
            change_type="ACL_MODIFIED",
            entity=f"access-list {acl_num}",
            action=action,
            details=details,
            suspicion_level=suspicion_level,
            reason=reason,
        )

    def _wildcard_to_cidr(self, ip: str, wildcard: str) -> str:
        wildcard_to_prefix = {
            "0.0.0.0": "32",
            "0.0.0.255": "24",
            "0.0.255.255": "16",
            "0.255.255.255": "8",
        }
        prefix = wildcard_to_prefix.get(wildcard, "??")
        return f"{ip}/{prefix}"

    def _compare_interface_acls(
        self, old_data: dict, new_data: dict
    ) -> list[SemanticChange]:
        changes: list[SemanticChange] = []

        for interface in new_data["interfaces"]:
            old_acl = old_data["interfaces"].get(interface, {}).get("acl")
            new_acl = new_data["interfaces"][interface].get("acl")

            if old_acl != new_acl:
                if old_acl and new_acl:
                    action = "modified"
                elif new_acl:
                    action = "added"
                else:
                    action = "removed"

                changes.append(
                    SemanticChange(
                        change_type="INTERFACE_ACL_BINDING",
                        entity=interface,
                        action=action,
                        details={
                            "interface": interface,
                            "old_acl": old_acl,
                            "new_acl": new_acl,
                            "direction": new_data["interfaces"][interface].get(
                                "acl_direction", "in"
                            ),
                        },
                        suspicion_level="medium",
                        reason=f"ACL binding changed on {interface}",
                    )
                )

        return changes

    def _compare_interface_ips(
        self, old_data: dict, new_data: dict
    ) -> list[SemanticChange]:
        changes: list[SemanticChange] = []

        for interface in new_data["interfaces"]:
            old_ip = old_data["interfaces"].get(interface, {}).get("ip")
            new_ip = new_data["interfaces"][interface].get("ip")

            if old_ip != new_ip and new_ip:
                changes.append(
                    SemanticChange(
                        change_type="INTERFACE_IP_CHANGE",
                        entity=interface,
                        action="modified",
                        details={
                            "interface": interface,
                            "old_ip": old_ip,
                            "new_ip": new_ip,
                        },
                        suspicion_level="medium",
                        reason=f"IP address changed on {interface}",
                    )
                )

        return changes

    def _create_hostname_change(
        self, old_data: dict, new_data: dict
    ) -> SemanticChange:
        return SemanticChange(
            change_type="HOSTNAME_CHANGE",
            entity="system",
            action="modified",
            details={
                "old_hostname": old_data.get("hostname"),
                "new_hostname": new_data.get("hostname"),
            },
            suspicion_level="low",
            reason="Hostname changed",
        )

    def _compare_ospf_timers(self, old_config: str, new_config: str) -> list[SemanticChange]:
        changes: list[SemanticChange] = []
        hello_re = re.compile(r"ip ospf hello-interval\s+(\d+)", re.M)
        dead_re = re.compile(r"ip ospf dead-interval\s+(\d+)", re.M)
        old_hello = hello_re.findall(old_config)
        new_hello = hello_re.findall(new_config)
        old_dead = dead_re.findall(old_config)
        new_dead = dead_re.findall(new_config)
        if new_hello and (not old_hello or old_hello != new_hello):
            changes.append(
                SemanticChange(
                    change_type="OSPF_TIMER_MISMATCH",
                    entity="ospf-interface",
                    action="modified",
                    details={
                        "hello_interval": new_hello[-1],
                        "dead_interval": new_dead[-1] if new_dead else None,
                        "peer_default_hello": "10",
                        "peer_default_dead": "40",
                    },
                    suspicion_level="critical",
                    reason="OSPF hello/dead timer mismatch between adjacent peers",
                )
            )
        return changes

    def _compare_route_maps(self, old_config: str, new_config: str) -> list[SemanticChange]:
        changes: list[SemanticChange] = []
        if "set community none" in new_config and "set community no-export" in old_config:
            changes.append(
                SemanticChange(
                    change_type="BGP_COMMUNITY_STRIPPED",
                    entity="EXPORT-OUT",
                    action="modified",
                    details={"removed_community": "no-export"},
                    suspicion_level="critical",
                    reason="route-map removed no-export community from eBGP export",
                )
            )
        return changes

    def _compare_stp_priority(self, old_config: str, new_config: str) -> list[SemanticChange]:
        changes: list[SemanticChange] = []
        prio_re = re.compile(r"spanning-tree vlan \d+ priority (\d+)", re.M)
        old_p = prio_re.findall(old_config)
        new_p = prio_re.findall(new_config)
        if new_p and (not old_p or (new_p[-1] == "0" and old_p[-1] != "0")):
            changes.append(
                SemanticChange(
                    change_type="STP_PRIORITY_SUBVERSION",
                    entity="spanning-tree",
                    action="modified",
                    details={"new_priority": new_p[-1], "old_priority": old_p[-1] if old_p else None},
                    suspicion_level="critical",
                    reason="Bridge priority subversion may trigger rogue root election",
                )
            )
        return changes
