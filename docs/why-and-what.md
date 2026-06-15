# What CiscoParser does — and why it helps you document a network

## The problem

A running network device knows everything about itself. Its `running-config` is the
single most authoritative description of how it is set up: which interfaces exist,
what addresses they carry, which VLANs and VRFs are defined, how it routes, who it
authenticates against, where it sends logs.

But that knowledge lives only on the device — as flat text, in a vendor dialect, on
hundreds of boxes. The moment you want a *picture* of the network — an inventory, an
IPAM, a diagram, an audit — you are stuck retyping what the devices already know.
Manual documentation drifts the day it is written; the config keeps changing, the
spreadsheet does not.

## What CiscoParser does

CiscoParser closes that gap. You give it a Cisco IOS-XE `running-config`. It returns
a **structured digital model** of the device, and (on-prem) writes that model
straight into **NetBox** — the open-source source-of-truth for DCIM and IPAM.

It reads the config the way an engineer reads it: it understands the hierarchical
parent/child structure (`interface → ip address → shutdown`), not just lines of
text. From one config it extracts:

| Captured as native NetBox objects | Captured as config context (textual) |
|-----------------------------------|--------------------------------------|
| Device name + platform            | Routing (OSPF / EIGRP / BGP / static) |
| Interfaces (type, description, state) | DHCP pools                        |
| IP addresses (mask → CIDR)        | ACLs, NAT                            |
| VLANs                             | SNMP, NTP, logging                   |
| VRFs                              | AAA / TACACS+ / RADIUS / users       |
|                                   | Crypto / PKI, QoS, line config       |

The split is deliberate: things NetBox models natively become real objects you can
query, filter and relate; everything else is preserved verbatim as **config
context** attached to the device, so nothing is lost.

## Why it is useful

- **Inventory without typing.** Point it at a config dump and the device, its
  interfaces, addresses and VLANs appear in NetBox. Repeat per device to build the
  inventory from ground truth.
- **IPAM that matches reality.** Addresses come from the config, not from memory, so
  your IPAM reflects what the device is actually using.
- **Documentation that can be re-run.** When a config changes, re-parse it. The
  model is regenerated from the device, not maintained by hand — it cannot silently
  drift.
- **Audit and review.** A normalized, structured view makes it easy to compare
  devices, spot the interface with no description, the VLAN defined but unused, the
  ACL that does not belong.
- **A foundation for everything downstream.** Once the network lives in NetBox as
  structured data, diagrams, compliance checks, automation and change tracking all
  have something to read from.

## Where it fits

CiscoParser is an **import / documentation** tool, not a configuration manager. It
takes the device's own truth and turns it into a model you can see, search and keep.
It pairs naturally with a standalone NetBox deployment: NetBox is the store,
CiscoParser is one of the doors data comes in through.

## Two editions

- **CiscoParser (on-prem)** — FastAPI + Docker on a Proxmox LXC. Parses and pushes
  directly into your NetBox over the local network.
- **CiscoParser Web (Cloudflare)** — a public, zero-install converter. Paste or
  upload a config, get the structured model and a downloadable NetBox-ready JSON
  plus an import snippet you run against your own NetBox. Nothing is stored, no
  credentials leave your machine.
