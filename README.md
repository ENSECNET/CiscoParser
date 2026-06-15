# ENSECNET · CiscoParser

Parse a Cisco IOS-XE `running-config` into a structured **NetBox** digital model —
documenting your network from the device's own source of truth instead of by hand.

Standalone web application: FastAPI backend + static frontend, packaged as Docker
Compose, deployed on Proxmox as a single minimal LXC. Pairs with a standalone NetBox
deployment as one of the doors data comes in through.

> A running device already knows everything about itself. CiscoParser turns that
> knowledge into a model you can see, search and keep. See
> [`docs/why-and-what.md`](docs/why-and-what.md).

```
Cisco IOS-XE .cfg ──► parse ──► transform ──► NetBox (DCIM / IPAM + config context)
```

## What it extracts

| Native NetBox objects                 | Config context (textual)             |
|---------------------------------------|--------------------------------------|
| Device, interfaces, IP addresses, VLANs, VRFs | routing, DHCP, ACLs, NAT, SNMP, NTP, logging, AAA, crypto, QoS, lines |

## Stack

| Layer    | Tech                                                | Image |
|----------|-----------------------------------------------------|-------|
| Backend  | Python 3.12 · FastAPI · CiscoConfParse2 · pynetbox  | `python:3.12-alpine` (multi-stage) |
| Frontend | Static HTML/JS served by Nginx                      | `nginx:alpine` |
| Host     | Debian 12 minimal LXC on Proxmox + Docker           | — |

Smallest reliable base: Alpine for the Docker images (real size win), Debian 12
minimal for the LXC host (Docker runs without cgroup/OpenRC quirks).

## Repo layout

```
CiscoParser/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile          multi-stage alpine
│   ├── requirements.txt
│   └── app/
│       ├── main.py         FastAPI endpoints
│       ├── parser.py       CiscoConfParse2 → structured groups
│       ├── transform.py    parser output → NetBox model
│       └── netbox_push.py  pynetbox push (auto prerequisites)
├── frontend/
│   ├── Dockerfile          nginx alpine
│   ├── nginx.conf          serves UI, proxies /api → backend
│   └── src/index.html
├── deploy/
│   └── lxc-deploy.sh       thin Proxmox deployer
└── docs/
    ├── why-and-what.md     what it does and why it helps
    └── architecture.md     data flow, base-image rationale, gotchas
```

## Deploy on Proxmox

```bash
curl -fsSL https://raw.githubusercontent.com/TencoNemaStrach/CiscoParser/main/deploy/lxc-deploy.sh -o lxc-deploy.sh
bash lxc-deploy.sh
```

Creates a Debian 12 LXC, installs Docker, clones this repo, runs
`docker compose up -d --build`. Open `http://<lxc-ip>:8080`.

## Run on any Docker host

```bash
cp .env.example .env        # optionally set NETBOX_URL / NETBOX_TOKEN
docker compose up -d --build
# UI: http://localhost:8080
```

## Update

```bash
pct exec <CTID> -- bash -c 'cd /opt/ciscoparser && git pull && docker compose up -d --build'
```

## API

| Method | Endpoint               | Purpose                     |
|--------|------------------------|-----------------------------|
| GET    | `/api/health`          | liveness                    |
| POST   | `/api/test-connection` | verify NetBox URL + token   |
| POST   | `/api/parse`           | upload `.cfg`, return model |
| POST   | `/api/parse-text`      | parse raw text body         |
| POST   | `/api/push`            | push model to NetBox        |

## NetBox notes

- NetBox 4.5+ tokens are shown **once** at creation — copy the full key.
- Prerequisites (Manufacturer `Cisco`, a default Device Type, Role `Router`, Site
  `ENSECNET-Lab`) are auto-created on first push, so it never fails on required
  fields.

## Public web edition

A zero-install converter (Cloudflare Worker) lives in a separate repo,
**CiscoParserWeb** — paste a config, get the model + downloadable NetBox JSON, no
credentials ever leave your machine.

---

ENSECNET · *dobrá infraštruktúra nie je vidieť — jej absencia áno.*
