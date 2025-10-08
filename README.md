# Termux Hotspot Script

This script allows you to create a Wi-Fi hotspot from your Termux terminal, with a TTL bypass to help with carrier rate limits.

## Features

*   **Easy Configuration**: All settings are at the top of the `hotspot.sh` script.
*   **TTL 65 Bypass**: Helps to avoid data throttling from your mobile provider when tethering.
*   **Auto-Restart**: The script monitors the hotspot and restarts it if it goes down.
*   **Internet Check**: It periodically checks for an internet connection and restarts the hotspot if connectivity is lost.

## Prerequisites

1.  **Rooted Android Device**: This is essential. The script needs root access to manage network interfaces and `iptables`.
2.  **Termux**: You must have Termux installed on your device.
3.  **Required Packages**: You'll need `hostapd`, `dnsmasq`, and `net-tools` (for `ifconfig`).

## Setup Instructions

1.  **Install Packages**:
    Open Termux and run:
    ```bash
    pkg install -y hostapd dnsmasq net-tools
    ```

2.  **Configure the Script**:
    Open the `hotspot.sh` script and edit the configuration section at the top:
    *   `IN_IFACE`: Your mobile data interface. Find this by running `su -c ifconfig` or `su -c ip a` in Termux. Common names are `rmnet_data0` or `rmnet_data1`.
    *   `OUT_IFACE`: Your Wi-Fi interface. Usually `wlan0`.
    *   `SSID`: The name of your Wi-Fi network.
    *   `PASSWORD`: The password for your Wi-Fi network (must be at least 8 characters).

3.  **Make the Script Executable**:
    ```bash
    chmod +x hotspot.sh
    ```

## How to Run

1.  **Start the Hotspot**:
    Run the script as root:
    ```bash
    su -c ./hotspot.sh
    ```
    The script will create the necessary configuration files, start the hotspot, and begin monitoring it. You will see log messages in your terminal.

2.  **Stop the Hotspot**:
    Simply press `Ctrl + C` in the Termux session where the script is running. The script will automatically clean up the hotspot configuration and stop the services.

## Disclaimer

*   This script modifies your system's network settings. Use it at your own risk.
*   Bypassing tethering restrictions may be against your mobile carrier's terms of service. Be aware of the potential consequences.
*   The effectiveness of the TTL bypass can vary depending on your carrier.