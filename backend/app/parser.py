"""
parser.py — Cisco IOS-XE config parser (CiscoConfParse2 wrapper)

Parses a plain-text `show running-config` into 15 structured parameter groups.
Output format: {"groups": [{"name": str, "params": [ {...} ]}]}
This raw format is consumed by transform.py, which converts it into the
NetBox-ready model used by netbox_push.py.
"""
from ciscoconfparse2 import CiscoConfParse


def _mask_to_prefix(mask: str) -> int:
    """Convert dotted-decimal mask (255.255.255.0) to prefix length (24)."""
    try:
        return sum(bin(int(o)).count("1") for o in mask.split("."))
    except Exception:
        return 32


def _interface_type(name: str) -> str:
    """Best-effort NetBox interface type from IOS-XE interface name."""
    n = name.lower()
    if "tengig" in n or "te" in n[:2]:
        return "10gbase-x-sfpp"
    if "gig" in n or n.startswith("gi"):
        return "1000base-t"
    if "loopback" in n or n.startswith("lo"):
        return "virtual"
    if "vlan" in n:
        return "virtual"
    if "tunnel" in n:
        return "virtual"
    if "port-channel" in n or n.startswith("po"):
        return "lag"
    return "other"


class CiscoParser:
    def __init__(self, config_text: str):
        self.parse = CiscoConfParse(config_text.splitlines(), syntax="ios")
        self.text = config_text

    # ── individual extractors ───────────────────────────────────────────
    def device_identity(self):
        params = []
        hn = self.parse.find_objects(r"^hostname\s+")
        if hn:
            params.append({"key": "hostname", "value": hn[0].text.split()[1]})
        dom = self.parse.find_objects(r"^ip domain.?name\s+")
        if dom:
            params.append({"key": "domain_name", "value": dom[0].text.split()[-1]})
        ver = self.parse.find_objects(r"^version\s+")
        if ver:
            params.append({"key": "ios_version", "value": ver[0].text.split()[-1]})
        return params

    def vrfs(self):
        out = []
        for obj in self.parse.find_objects(r"^(ip\s+)?vrf\s+definition|^ip\s+vrf\s+"):
            name = obj.text.split()[-1]
            rd = None
            for c in obj.children:
                if "rd " in c.text:
                    rd = c.text.strip().split()[-1]
            out.append({"name": name, "rd": rd})
        return out

    def vlans(self):
        out = []
        for obj in self.parse.find_objects(r"^vlan\s+\d+"):
            vid = obj.text.split()[1]
            name = None
            for c in obj.children:
                if c.text.strip().startswith("name "):
                    name = c.text.strip().split(maxsplit=1)[1]
            out.append({"vid": vid, "name": name or f"VLAN{vid}"})
        return out

    def interfaces(self):
        out = []
        for obj in self.parse.find_objects(r"^interface\s+"):
            name = obj.text.split(maxsplit=1)[1]
            entry = {
                "name": name,
                "type": _interface_type(name),
                "enabled": True,
                "description": None,
                "ip": None,
                "mode": None,
                "access_vlan": None,
            }
            for c in obj.children:
                t = c.text.strip()
                if t.startswith("description "):
                    entry["description"] = t.split(maxsplit=1)[1]
                elif t.startswith("ip address ") and "dhcp" not in t:
                    parts = t.split()
                    if len(parts) >= 4:
                        entry["ip"] = f"{parts[2]}/{_mask_to_prefix(parts[3])}"
                elif t == "shutdown":
                    entry["enabled"] = False
                elif t.startswith("switchport mode "):
                    entry["mode"] = t.split()[-1]
                elif t.startswith("switchport access vlan "):
                    entry["access_vlan"] = t.split()[-1]
            out.append(entry)
        return out

    def _raw_block(self, regex):
        """Return list of full text blocks matching a top-level regex."""
        blocks = []
        for obj in self.parse.find_objects(regex):
            lines = [obj.text] + [c.text for c in obj.children]
            blocks.append("\n".join(lines))
        return blocks

    # ── config-context (textual) groups ────────────────────────────────
    def context_groups(self):
        ctx = {}
        ctx["routing"] = self._raw_block(
            r"^router\s+(ospf|eigrp|bgp|rip)|^ip\s+route\s+"
        )
        ctx["dhcp"] = self._raw_block(r"^ip\s+dhcp\s+")
        ctx["acls"] = self._raw_block(r"^(ip\s+)?access-list|^access-list\s+")
        ctx["nat"] = self._raw_block(r"^ip\s+nat\s+")
        ctx["snmp"] = self._raw_block(r"^snmp-server\s+")
        ctx["ntp"] = self._raw_block(r"^ntp\s+")
        ctx["logging"] = self._raw_block(r"^logging\s+")
        ctx["aaa"] = self._raw_block(
            r"^aaa\s+|^tacacs.?server|^radius.?server|^username\s+"
        )
        ctx["crypto"] = self._raw_block(r"^crypto\s+")
        ctx["qos"] = self._raw_block(r"^(class-map|policy-map)\s+")
        ctx["lines"] = self._raw_block(r"^line\s+")
        # drop empty
        return {k: v for k, v in ctx.items() if v}

    # ── top-level ───────────────────────────────────────────────────────
    def parse_all(self):
        return {
            "identity": self.device_identity(),
            "vrfs": self.vrfs(),
            "vlans": self.vlans(),
            "interfaces": self.interfaces(),
            "context": self.context_groups(),
        }
