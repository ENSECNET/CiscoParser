#!/usr/bin/env bash
###############################################################################
# lxc-deploy.sh — ENSECNET CiscoParser, thin Proxmox LXC + Docker deployer
#
# Pattern: minimal Debian 12 LXC -> install Docker -> git clone -> compose up.
# No heredoc-embedded app code. The app lives in git; the LXC just runs it.
#
# Run on the Proxmox node:
#   bash lxc-deploy.sh
###############################################################################
set -euo pipefail

REPO_URL="https://github.com/ensecnet/CiscoParser.git"
TEMPLATE="debian-12-standard"   # minimal Debian; smallest reliable base for Docker

C='\033[0;36m'; G='\033[0;32m'; Y='\033[1;33m'; W='\033[1;37m'; N='\033[0m'
info(){ echo -e "${C}[INFO]${N} $1"; }
ok(){   echo -e "${G}[OK]${N}   $1"; }
ask(){  read -rp "$(echo -e "${C}$1${N} [${W}$2${N}]: ")" _r; echo "${_r:-$2}"; }

echo -e "${W}ENSECNET CiscoParser — LXC + Docker deployer${N}"

CTID=$(ask "Container ID" "$(pvesh get /cluster/nextid 2>/dev/null || echo 320)")
HOST=$(ask "Hostname" "ciscoparser")
STORAGE=$(ask "Storage" "local-zfs")
DISK=$(ask "Disk (GB)" "12")
RAM=$(ask "RAM (MB)" "2048")
CORES=$(ask "CPU cores" "2")
BRIDGE=$(ask "Bridge" "vmbr1")
VLAN=$(ask "VLAN tag (empty=none)" "200")
IPCFG=$(ask "IP (CIDR or 'dhcp')" "192.168.200.237/24")
GW=$(ask "Gateway" "192.168.200.1")
WEB_PORT=$(ask "Web port" "8080")
NB_URL=$(ask "NetBox URL" "http://192.168.200.236:8080")

# locate a debian-12 template
TPL=$(pveam available --section system 2>/dev/null | awk '/'"$TEMPLATE"'/{print $2}' | head -1)
LOCAL_TPL=$(pveam list local 2>/dev/null | awk '/'"$TEMPLATE"'/{print $1}' | head -1)
if [[ -z "$LOCAL_TPL" ]]; then
  info "Downloading template $TPL …"
  pveam download local "$TPL"
  LOCAL_TPL="local:vztmpl/$TPL"
fi
ok "Template: $LOCAL_TPL"

# build net string
NET="name=eth0,bridge=${BRIDGE}"
[[ -n "$VLAN" ]] && NET="${NET},tag=${VLAN}"
if [[ "$IPCFG" == "dhcp" ]]; then NET="${NET},ip=dhcp"
else NET="${NET},ip=${IPCFG},gw=${GW}"; fi

info "Creating LXC $CTID …"
pct create "$CTID" "$LOCAL_TPL" \
  --hostname "$HOST" --cores "$CORES" --memory "$RAM" \
  --rootfs "${STORAGE}:${DISK}" --net0 "$NET" \
  --features nesting=1 --unprivileged 1 --onboot 1 --start 1
sleep 5
ok "LXC created and started"

info "Installing Docker inside LXC …"
pct exec "$CTID" -- bash -c '
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl git >/dev/null
  install -m0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin >/dev/null
  systemctl enable --now docker
'
ok "Docker installed"

info "Cloning repo and starting stack …"
pct exec "$CTID" -- bash -c "
  cd /opt && git clone $REPO_URL ciscoparser && cd ciscoparser
  cp .env.example .env
  sed -i 's#^NETBOX_URL=.*#NETBOX_URL=$NB_URL#' .env
  sed -i 's#^WEB_PORT=.*#WEB_PORT=$WEB_PORT#' .env
  docker compose up -d --build
"
ok "Stack up"

IP_SHOW="${IPCFG%%/*}"
[[ "$IPCFG" == "dhcp" ]] && IP_SHOW=$(pct exec "$CTID" -- hostname -I | awk '{print $1}')
echo
ok "ENSECNET CiscoParser running"
echo -e "  Web UI : ${W}http://${IP_SHOW}:${WEB_PORT}${N}"
echo -e "  Update : ${W}pct exec $CTID -- bash -c 'cd /opt/ciscoparser && git pull && docker compose up -d --build'${N}"
