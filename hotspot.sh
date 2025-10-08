#!/bin/bash

# # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Termux Hotspot with TTL 65 Bypass                 #
# by Jules                                          #
#                                                   #
# IMPORTANT: This script requires a rooted device.  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # #

# --- Configuration ---
# - Network interface for mobile data (find with `ifconfig` or `ip a`)
#   Common values: rmnet_data0, rmnet_data1, wlan0 (if using Wi-Fi as source)
IN_IFACE="rmnet_data0"

# - Network interface for the hotspot
#   Common values: wlan0, wlan1
OUT_IFACE="wlan0"

# - Hotspot IP address and subnet
HOTSPOT_IP="192.168.43.1"
SUBNET="192.168.43.0/24"
DHCP_RANGE="192.168.43.10,192.168.43.50,12h"

# - Hotspot SSID and password
SSID="TermuxHotspot"
PASSWORD="password"

# - Hostapd configuration file path
HOSTAPD_CONF="/data/data/com.termux/files/usr/etc/hostapd.conf"
DNSMASQ_CONF="/data/data/com.termux/files/usr/etc/dnsmasq.conf"

# --- Helper Functions ---

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log "ERROR: This script must be run as root."
        exit 1
    fi
}

check_internet() {
    log "Checking for internet connectivity..."
    if ping -c 1 8.8.8.8 > /dev/null; then
        log "Internet connection found."
        return 0
    else
        log "WARNING: No internet connection."
        return 1
    fi
}

# --- Hotspot Functions ---

create_configs() {
    log "Creating configuration files..."
    # hostapd.conf
    cat > "$HOSTAPD_CONF" <<EOF
interface=$OUT_IFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

    # dnsmasq.conf
    cat > "$DNSMASQ_CONF" <<EOF
interface=$OUT_IFACE
dhcp-range=$DHCP_RANGE
dhcp-option=3,$HOTSPOT_IP
dhcp-option=6,$HOTSPOT_IP
server=8.8.8.8
log-queries
log-dhcp
listen-address=127.0.0.1,$HOTSPOT_IP
EOF
    log "Configuration files created."
}

start_hotspot() {
    log "Starting hotspot..."
    check_internet

    # Bring down interface to be safe
    ip link set dev "$OUT_IFACE" down

    # Configure the hotspot interface
    ip addr flush dev "$OUT_IFACE"
    ip addr add "$HOTSPOT_IP/24" dev "$OUT_IFACE"
    ip link set dev "$OUT_IFACE" up

    # Configure routing and firewall rules
    log "Setting up iptables rules..."
    iptables -F
    iptables -t nat -F
    iptables -t mangle -F
    iptables -t nat -A POSTROUTING -o "$IN_IFACE" -j MASQUERADE
    iptables -A FORWARD -i "$OUT_IFACE" -o "$IN_IFACE" -j ACCEPT
    iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

    # TTL Bypass
    log "Applying TTL 65 bypass..."
    iptables -t mangle -A PREROUTING -i "$OUT_IFACE" -j TTL --ttl-set 65

    # Enable IP forwarding
    sysctl -w net.ipv4.ip_forward=1 > /dev/null

    # Start services
    log "Starting dnsmasq and hostapd..."
    dnsmasq -C "$DNSMASQ_CONF" &
    hostapd "$HOSTAPD_CONF" &

    log "Hotspot started successfully."
}

stop_hotspot() {
    log "Stopping hotspot..."

    # Kill services
    pkill hostapd
    pkill dnsmasq

    # Flush iptables
    log "Flushing iptables rules..."
    iptables -F
    iptables -t nat -F
    iptables -t mangle -F

    # Disable IP forwarding
    sysctl -w net.ipv4.ip_forward=0 > /dev/null

    # Bring down hotspot interface
    ip addr flush dev "$OUT_IFACE"
    ip link set dev "$OUT_IFACE" down

    log "Hotspot stopped."
}

# --- Main Logic ---

trap stop_hotspot EXIT

check_root
create_configs

while true; do
    if ! pgrep -f "hostapd $HOSTAPD_CONF" > /dev/null; then
        log "Hotspot is not running. Starting it..."
        stop_hotspot # Clean up any previous state
        sleep 1
        start_hotspot
    else
        log "Hotspot is running."
    fi

    if ! check_internet; then
        log "Internet connection lost. Restarting hotspot to re-establish..."
        stop_hotspot
        sleep 5
        start_hotspot
    fi

    sleep 60 # Check every 60 seconds
done