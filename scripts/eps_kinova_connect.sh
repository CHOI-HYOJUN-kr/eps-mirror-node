#!/usr/bin/env bash
# =====================================================================
#  eps_kinova_connect.sh
#
#  Purpose:
#    This script automates the network setup required to connect
#    the PC to the physical Kinova Gen3 robot controller.
#
#    Steps performed:
#      1) Optionally disable firewall (ufw)
#      2) Configure a static IP for the selected network interface
#      3) Ping the robot to verify the connection
#      4) Source ROS 2 environments
#      5) Launch eps_kinova.launch.py (real robot bringup)
#
#  Why this script exists:
#    During the project, repeated setup mistakes happened around:
#      - Finding the correct network interface name
#      - Assigning the correct static IP to the PC
#      - Forgetting to flush/reset old IP addresses
#      - Forgetting to source the ROS 2 workspace
#
#    This script reduces those repeated mistakes by putting the steps
#    into one reproducible command.
# =====================================================================

set -e

# ---------------------------------------------------------------------
# CONFIGURATION VARIABLES
#
# Edit these values for your own setup.
# You can also override them from the terminal, for example:
#
#   IFACE=enp3s0 bash scripts/eps_kinova_connect.sh
#
# ---------------------------------------------------------------------

ROBOT_IP="${ROBOT_IP:-192.168.1.10}"     # Kinova controller IP
HOST_IP="${HOST_IP:-192.168.1.11}"       # Static IP to assign to this PC
IFACE="${IFACE:-}"                       # Network interface connected to the robot
WS="${WS:-$HOME/clearpath_ws}"           # ROS 2 workspace path
DISABLE_UFW="${DISABLE_UFW:-true}"       # Set to false if you do not want to disable ufw

# ---------------------------------------------------------------------
# Check required input
# ---------------------------------------------------------------------

if [ -z "$IFACE" ]; then
  echo "[ERROR] Network interface is not set."
  echo
  echo "Available interfaces:"
  ip -br link
  echo
  echo "Run again with the correct interface, for example:"
  echo "  IFACE=enp3s0 bash scripts/eps_kinova_connect.sh"
  exit 1
fi

# ---------------------------------------------------------------------
# 1) Optionally disable the firewall
#
# Why?
#   Some Linux firewall settings can block ping or ROS 2 discovery.
# ---------------------------------------------------------------------

if [ "$DISABLE_UFW" = "true" ]; then
  echo "[EPS] Disabling firewall (ufw)..."
  sudo ufw disable || true
else
  echo "[EPS] Skipping firewall change."
fi

# ---------------------------------------------------------------------
# 2) Configure the selected network interface
#
# The robot and the PC must be on the same subnet.
# Example:
#   Robot: 192.168.1.10
#   PC:    192.168.1.11
# ---------------------------------------------------------------------

echo "[EPS] Configuring interface $IFACE to $HOST_IP/24 ..."
sudo ip addr flush dev "$IFACE"
sudo ip link set "$IFACE" up
sudo ip addr add "$HOST_IP/24" dev "$IFACE"

echo "[EPS] Current IP setting for $IFACE:"
ip addr show "$IFACE" | grep "inet" || true

# ---------------------------------------------------------------------
# 3) Ping the robot to verify communication
# ---------------------------------------------------------------------

echo "[EPS] Pinging robot at $ROBOT_IP ..."
if ping -c 3 "$ROBOT_IP" > /dev/null 2>&1; then
  echo "[EPS] Connection successful. Kinova robot is reachable at $ROBOT_IP."
else
  echo "[ERROR] Connection failed: unable to reach $ROBOT_IP."
  echo "[ERROR] Check the LAN cable, robot power, IP settings, and interface name."
  exit 1
fi

# ---------------------------------------------------------------------
# 4) Source ROS 2 environments
# ---------------------------------------------------------------------

echo "[EPS] Loading ROS 2 environment..."
source /opt/ros/jazzy/setup.bash

if [ ! -f "$WS/install/setup.bash" ]; then
  echo "[ERROR] Workspace setup file not found: $WS/install/setup.bash"
  echo "[ERROR] Check the WS variable or build the workspace first."
  exit 1
fi

source "$WS/install/setup.bash"

# ---------------------------------------------------------------------
# 5) Launch the real robot bringup
#
# This starts:
#   - Kortex driver
#   - MirrorNode v2
#   - Real Kinova command routing
# ---------------------------------------------------------------------

echo "[EPS] Launching eps_bringup/eps_kinova.launch.py ..."
ros2 launch eps_bringup eps_kinova.launch.py
