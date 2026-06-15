# Architecture & Notes

## Data flow

```
.cfg ──► parser.py ──► transform.py ──► netbox_push.py ──► NetBox
```

- **parser.py** — CiscoConfParse2 wrapper. Native objects (hostname, VRFs, VLANs,
  interfaces + IP) are extracted as structured fields; everything else (routing,
  DHCP, ACLs, NAT, SNMP, NTP, logging, AAA, crypto, QoS, lines) is captured as
  textual config-context blocks.
- **transform.py** — reshapes raw parser output into the canonical NetBox model.
  This layer exists because the parser and the pusher use different shapes; without
  it the push produces an empty device.
- **netbox_push.py** — pynetbox. Auto-creates prerequisites and sets device_type /
  role / site (NetBox's three required device fields). IPs arrive already in CIDR.

## Why this base image choice

- Docker images on **Alpine** — real size win (~50–60 MB backend, ~25 MB frontend).
  Multi-stage build compiles wheels with `build-base`; the runtime stage stays slim.
- LXC host on **Debian 12 minimal** — Docker runs without the cgroupv2/OpenRC
  friction you hit running Docker on an Alpine LXC.

## Known gotchas

| Issue | Fix |
|-------|-----|
| NetBox 4.5+ "Invalid v1 token" | Create token, copy the **full** key at creation — shown once. |
| Device push 400 "field required" | Prerequisites auto-created in `netbox_push.py`. |
| IP rejected by IPAM | Parser already converts mask → CIDR prefix. |
| Docker on Alpine LXC flaky | Use Debian 12 LXC (default in `lxc-deploy.sh`). |
