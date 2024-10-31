#!/bin/bash

if ip link show can0 > /dev/null 2>&1; then
    ip link set can0 down
    ip link set can0 txqueuelen 1000
    ip link set can0 up type can bitrate 1000000 dbitrate 5000000 fd on
    echo "CANFD interface setup completed."
else
    echo "CAN interface not found. Please check your USB-CAN device connection."
fi