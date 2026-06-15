"""
transform.py — Parser output → NetBox-ready model

The parser emits a raw {identity, vrfs, vlans, interfaces, context} structure.
This module reshapes it into the canonical model that netbox_push.py expects:

{
  "name": str,
  "platform": str | None,
  "interfaces": [ {name, type, enabled, description, address} ],
  "vrfs":  [ {name, rd} ],
  "vlans": [ {vid, name} ],
  "config_context": { ... textual blocks ... }
}
"""


def _identity_dict(identity_list):
    return {item["key"]: item["value"] for item in identity_list}


def transform(parsed: dict) -> dict:
    ident = _identity_dict(parsed.get("identity", []))

    interfaces = []
    for intf in parsed.get("interfaces", []):
        interfaces.append(
            {
                "name": intf["name"],
                "type": intf["type"],
                "enabled": intf["enabled"],
                "description": intf.get("description"),
                "address": intf.get("ip"),  # already CIDR or None
                "mode": intf.get("mode"),
                "access_vlan": intf.get("access_vlan"),
            }
        )

    return {
        "name": ident.get("hostname", "unknown-device"),
        "platform": ident.get("ios_version"),
        "domain_name": ident.get("domain_name"),
        "interfaces": interfaces,
        "vrfs": parsed.get("vrfs", []),
        "vlans": parsed.get("vlans", []),
        "config_context": parsed.get("context", {}),
    }
