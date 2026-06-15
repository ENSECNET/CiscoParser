"""
netbox_push.py — Push the NetBox-ready model into NetBox via pynetbox.

Handles the two deployment-era fixes:
  1. Device create requires device_type, role, site -> ensured/auto-created.
  2. IP addresses arrive as CIDR (mask->prefix done in parser).

Prerequisites (Manufacturer / Device Type / Role / Site) are auto-created
with sensible defaults if missing, so a first push never 400s on
"field required".
"""
import pynetbox


DEFAULTS = {
    "manufacturer": ("Cisco", "cisco"),
    "device_type": ("ESR-6300-CON-K9", "esr-6300-con-k9"),
    "role": ("Router", "router"),
    "site": ("ENSECNET-Lab", "ensecnet-lab"),
}


class NetBoxPusher:
    def __init__(self, url: str, token: str, verify_ssl: bool = False):
        self.nb = pynetbox.api(url, token=token)
        self.nb.http_session.verify = verify_ssl

    # ── prerequisite helpers ────────────────────────────────────────────
    def _ensure_manufacturer(self):
        name, slug = DEFAULTS["manufacturer"]
        obj = self.nb.dcim.manufacturers.get(slug=slug)
        return obj or self.nb.dcim.manufacturers.create(name=name, slug=slug)

    def _ensure_device_type(self, manufacturer):
        model, slug = DEFAULTS["device_type"]
        obj = self.nb.dcim.device_types.get(slug=slug)
        return obj or self.nb.dcim.device_types.create(
            manufacturer=manufacturer.id, model=model, slug=slug
        )

    def _ensure_role(self):
        name, slug = DEFAULTS["role"]
        obj = self.nb.dcim.device_roles.get(slug=slug)
        return obj or self.nb.dcim.device_roles.create(
            name=name, slug=slug, color="2196f3"
        )

    def _ensure_site(self):
        name, slug = DEFAULTS["site"]
        obj = self.nb.dcim.sites.get(slug=slug)
        return obj or self.nb.dcim.sites.create(name=name, slug=slug, status="active")

    def _ensure_device(self, model: dict):
        existing = self.nb.dcim.devices.get(name=model["name"])
        if existing:
            return existing
        mfr = self._ensure_manufacturer()
        dtype = self._ensure_device_type(mfr)
        role = self._ensure_role()
        site = self._ensure_site()
        return self.nb.dcim.devices.create(
            name=model["name"],
            device_type=dtype.id,
            role=role.id,
            site=site.id,
            status="active",
        )

    # ── child object creation ───────────────────────────────────────────
    def _push_vlans(self, model, site):
        for v in model.get("vlans", []):
            if not self.nb.ipam.vlans.get(vid=v["vid"], site_id=site.id):
                self.nb.ipam.vlans.create(
                    vid=int(v["vid"]), name=v["name"], site=site.id, status="active"
                )

    def _push_vrfs(self, model):
        for vrf in model.get("vrfs", []):
            if not self.nb.ipam.vrfs.get(name=vrf["name"]):
                self.nb.ipam.vrfs.create(name=vrf["name"], rd=vrf.get("rd"))

    def _push_interfaces(self, model, device):
        for intf in model.get("interfaces", []):
            existing = self.nb.dcim.interfaces.get(
                device_id=device.id, name=intf["name"]
            )
            if existing:
                iface = existing
            else:
                iface = self.nb.dcim.interfaces.create(
                    device=device.id,
                    name=intf["name"],
                    type=intf["type"],
                    enabled=intf["enabled"],
                    description=intf.get("description") or "",
                )
            addr = intf.get("address")
            if addr and not self.nb.ipam.ip_addresses.get(address=addr):
                ip = self.nb.ipam.ip_addresses.create(
                    address=addr,
                    status="active",
                    assigned_object_type="dcim.interface",
                    assigned_object_id=iface.id,
                )
                # set as primary if it's the first usable IPv4
                if not device.primary_ip4:
                    device.primary_ip4 = ip.id
                    device.save()

    def _push_config_context(self, model, device):
        ctx = model.get("config_context", {})
        if not ctx:
            return
        # store as local config context data on the device
        device.local_context_data = ctx
        device.save()

    # ── top-level ───────────────────────────────────────────────────────
    def push(self, model: dict) -> dict:
        device = self._ensure_device(model)
        site = self._ensure_site()
        self._push_vlans(model, site)
        self._push_vrfs(model)
        self._push_interfaces(model, device)
        self._push_config_context(model, device)
        return {
            "device": device.name,
            "device_id": device.id,
            "interfaces": len(model.get("interfaces", [])),
            "vlans": len(model.get("vlans", [])),
            "vrfs": len(model.get("vrfs", [])),
            "url": f"{self.nb.base_url.replace('/api', '')}/dcim/devices/{device.id}/",
        }
