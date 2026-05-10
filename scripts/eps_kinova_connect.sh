#!/usr/bin/env bash
# =====================================================================
#  eps_kinova_connect.sh
#
#  Purpose:
#    This script AUTOMATES the network configuration required to
#    connect the PC to the REAL Kinova Gen3 robot controller.
#
#    Steps performed:
#      1) Disable firewall (ufw) to avoid blocked packets
#      2) Configure a static IP for the selected network interface
#      3) Ping the robot to verify the connection
#      4) Source ROS environments
#      5) Launch eps_kinova.launch.py (real robot bringup)
#
#  Why this script exists:
#    Many students struggle with:
#      - Finding the correct interface name (IFACE)
#      - Assigning the correct IP to the PC
#      - Forgetting to flush/reset IP addresses
#      - Forgetting to source ROS environments
#
#    This script eliminates all mistakes and does everything automatically.
# =====================================================================

set -e
# "set -e" means:
#   If ANY command fails, the script stops immediately.
#   This prevents the robot bringup from running with wrong settings.

# ---------------------------------------------------------------------
# CONFIGURATION VARIABLES
# Students only need to edit IFACE.
# ---------------------------------------------------------------------

ROBOT_IP="192.168.1.10"       # IP address of the Kinova controller
IFACE="enxf8e43bb862b5"       # Network interface connected to the robot (edit this!)
HOST_IP="192.168.1.11"        # Static IP to assign to the PC
WS="$HOME/clearpath_ws"       # Path to the ROS workspace

# ---------------------------------------------------------------------
# 1) Disable the firewall
#
# Why?
#   Some Linux firewalls block ping or UDP packets,
#   which prevents ROS2 discovery from working properly.
# ---------------------------------------------------------------------
echo "[EPS] 🔐 Disabling firewall (ufw)..."
sudo ufw disable || true
# "|| true" prevents script from stopping if ufw is already disabled.

# ---------------------------------------------------------------------
# 2) Configure the selected network interface
#
# Steps:
#   - Remove old IP settings
#   - Bring the interface up
#   - Assign our static IP (HOST_IP)
#
# Why?
#   The robot uses a fixed subnet: 192.168.1.x
#   The PC MUST also be in that subnet to communicate.
# ---------------------------------------------------------------------
echo "[EPS] 🌐 Configuring interface $IFACE to $HOST_IP/24 ..."
sudo ip addr flush dev $IFACE          # Remove old IPs
sudo ip link set $IFACE up             # Enable interface
sudo ip addr add $HOST_IP/24 dev $IFACE  # Assign new IP
ip addr show $IFACE | grep "inet" || true
# Shows IP to confirm configuration worked.

# ---------------------------------------------------------------------
# 3) Ping the robot to ensure communication works
#
# Why?
#   If ping fails:
#      → launch file will NOT work
#      → robot controller cannot be reached
# ---------------------------------------------------------------------
echo "[EPS] 📡 Pinging robot at $ROBOT_IP ..."
if ping -c 3 $ROBOT_IP > /dev/null 2>&1; then

  echo "[EPS] ✅ Connection successful! Kinova robot is reachable at $ROBOT_IP."
  echo "[EPS] 🌟 Status: The network link is active and communication is verified."
  echo "[EPS] 🚀 Proceeding with Kinova bringup..."

  # -------------------------------------------------------------------
  # 4) Source ROS environments
  #
  # Why?
  #   The launch file requires:
  #       - ROS2 environment variables
  #       - Workspace build environment (install/setup.bash)
  #
  # If this is missing, ROS2 will say:
  #      "package not found" or "command not found"
  # -------------------------------------------------------------------
  echo "[EPS] 🧠 Loading ROS environment..."
  source /opt/ros/jazzy/setup.bash
  source "$WS/install/setup.bash"

  # -------------------------------------------------------------------
  # 5) Launch the real robot bringup
  #
  # This starts:
  #   - Kortex driver
  #   - Motion command routing
  #   - Joint trajectory controllers
  #
  # After launching, MoveIt can communicate with the real arm.
  # -------------------------------------------------------------------
  echo "[EPS] ▶️ Launching eps_bringup/eps_kinova.launch.py ..."
  ros2 launch eps_bringup eps_kinova.launch.py

else
  # -------------------------------------------------------------------
  # Ping FAILED → Something is wrong with the network setup
  # -------------------------------------------------------------------
  echo "[ERROR] ❌ Connection failed: Unable to reach $ROBOT_IP."
  echo "[ERROR] Please check the LAN cable, IP settings, and power of the robot."
  exit 1
fi
