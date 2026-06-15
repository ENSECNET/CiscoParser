<div align="center">

# CiscoParser

**Web-based application for network documentation**

Import Cisco switches and routers into NetBox — straight from their `running-config`.

[![Docs](https://img.shields.io/badge/📖_Documentation-View_full_docs-0bb3a0?style=for-the-badge)](https://ensecnet.github.io/CiscoParser/)
[![License](https://img.shields.io/badge/License-Apache_2.0-131c2b?style=for-the-badge)](LICENSE)
[![Web edition](https://img.shields.io/badge/Web_edition-CiscoParserWeb-2ea043?style=for-the-badge)](https://github.com/TencoNemaStrach/CiscoParserWeb)

</div>

---

> ### 📖 [**Read the full documentation →**](https://ensecnet.github.io/CiscoParser/)
>
> What the parser does, why it helps you document a network, what it extracts,
> architecture and deployment — published as a documentation site with sidebar
> navigation. This README is the summary.

---

A running device already knows everything about itself. CiscoParser turns that
knowledge into a structured **NetBox** model you can see, search and keep — instead
of documenting the network by hand.

```
Cisco IOS-XE .cfg ──► parse ──► transform ──► NetBox (DCIM / IPAM + config context)
```

Standalone web application: FastAPI backend + static frontend, packaged as Docker
Compose, deployed on Proxmox as a single minimal LXC. Companion to a standalone
NetBox deployment.

## What it extracts

| Native NetBox objects | Config context (textual) |
|---|---|
| Device, interfaces, IP addresses, VLANs, VRFs | routing, DHCP, ACLs, NAT, SNMP, NTP, logging, AAA, crypto, QoS, lines |

## Stack

| Layer | Tech | Image |
|---|---|---|
| Backend | Python 3.12 · FastAPI · CiscoConfParse2 · pynetbox | `python:3.12-alpine` (multi-stage) |
| Frontend | Static HTML/JS via Nginx | `nginx:alpine` |
| Host | Debian 12 minimal LXC on Proxmox + Docker | — |

## Deploy on Proxmox

```bash
curl -fsSL https://raw.githubusercontent.com/TencoNemaStrach/CiscoParser/main/deploy/lxc-deploy.sh -o lxc-deploy.sh
bash lxc-deploy.sh
# open http://<lxc-ip>:8080
```

## Run on any Docker host

```bash
cp .env.example .env        # optionally set NETBOX_URL / NETBOX_TOKEN
docker compose up -d --build
```

## Editions

- **CiscoParser** (this repo) — on-prem, live NetBox push over the local network.
- **[CiscoParserWeb](https://github.com/TencoNemaStrach/CiscoParserWeb)** — public
  Cloudflare Worker; paste a config, download the model + a generated import script.
  Nothing stored, no credentials leave your machine.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

---

<div align="center">
ENSECNET · <em>dobrá infraštruktúra nie je vidieť — jej absencia áno.</em>
</div>
