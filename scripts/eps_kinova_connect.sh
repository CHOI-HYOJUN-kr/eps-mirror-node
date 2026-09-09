#!/usr/bin/env bash
# September 2026 maintenance: read-only connectivity preflight.
# Does not configure interfaces, change firewall rules, or launch robot motion.
set -euo pipefail

if [[ -z "${ROBOT_IP:-}" ]]; then
  echo 'Set ROBOT_IP to the controller address for your own environment.' >&2
  exit 2
fi
if [[ ! "$ROBOT_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo 'ROBOT_IP must be an IPv4 address.' >&2
  exit 2
fi
IFS=. read -r -a octets <<< "$ROBOT_IP"
for octet in "${octets[@]}"; do
  if (( ${#octet} > 3 )) || (( 10#$octet > 255 )); then
    echo 'IPv4 octet out of range.' >&2
    exit 2
  fi
done
command -v ip >/dev/null
command -v ping >/dev/null
ip -br address
ping -c 3 -W 2 "$ROBOT_IP"
echo 'Host reachability check only; this does not verify ROS2 or robot readiness.'
