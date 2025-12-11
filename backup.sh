#!/bin/bash
# Daily backup to /root/backups/
mkdir -p /root/backups
cp contracts.db /root/backups/contracts_$(date +%Y%m%d_%H%M%S).db
echo "Backup created at /root/backups/"
