# Troubleshooting Guide

**Version**: 1.0
**Last Updated**: 2025-01-18
**Purpose**: Common issues, causes, and fixes for Pi-hole Network Manager

---

## Overview

This document provides troubleshooting guidance for common issues encountered when using the Pi-hole Network Manager. For ultra-compact knowledge base format, see `.claude/knowledge/troubleshooting.kd`.

---

## Setup and Permission Issues

### Permission Denied

**Symptom**: Commands fail with permission denied

**Cause**: Sudoers not configured or user not in pihole-manager group

**Fix**:
```bash
# On the Pi, check group membership
groups
# Should include "pihole-manager"

# If missing, add user to group
sudo usermod -aG pihole-manager $USER

# Logout and login to apply changes
exit

# If still failing, re-run setup
sudo /opt/pihole-network-manager/pi-setup/initial-setup.sh
```

**Severity**: High

---

### Sudo Password Prompt

**Symptom**: Sudo prompts for password when running Pi-hole commands

**Cause**: User not in pihole-manager group or sudoers not configured

**Fix**:
```bash
# On the Pi, test passwordless sudo
sudo -n pihole status

# Check group membership
groups

# Logout and login if group is present
exit

# If still failing, check sudoers file
sudo cat /etc/sudoers.d/pihole-manager
```

**Severity**: Medium

---

### Setup Not Complete

**Symptom**: Application shows "setup not complete" error

**Cause**: initial-setup.sh not run

**Fix**:
```bash
# On the Pi, run setup
sudo /opt/pihole-network-manager/pi-setup/initial-setup.sh

# Verify setup complete
cat /opt/pihole-manager/state.json
# Should show: {"setup_complete": true}
```

**Severity**: Critical

---

### Command Not Found

**Symptom**: "pihole: command not found"

**Cause**: Pi-hole not installed

**Fix**:
```bash
# On the Pi, install Pi-hole
curl -sSL https://install.pi-hole.net | sudo bash

# Verify installation
pihole status
```

**Severity**: Critical

---

## Pi-hole Issues

### Gravity Rebuild Timeout

**Symptom**: Gravity rebuild takes too long or times out

**Cause**: Large blocklist profile or slow Raspberry Pi

**Fix**:
1. Switch to smaller blocklist profile (Light or Moderate)
2. Increase timeout in code
3. Wait for operation to complete

**Severity**: Low

---

### DNS Queries Not Resolving

**Symptom**: Network devices cannot resolve DNS queries

**Cause**: Pi-hole FTL service is down

**Fix**:
```bash
ssh pi@pihole.local "sudo systemctl restart pihole-FTL"
```

**Severity**: Critical

---

### Blocking Too Aggressive

**Symptom**: Legitimate websites are blocked

**Cause**: Aggressive blocklist profile is too restrictive

**Fix**:
1. Switch to Moderate or Light profile
2. Whitelist specific domains via management tool
3. Use Pi-hole web UI to verify blocklists

**Severity**: Medium

---

### Gravity Database Corruption

**Symptom**: Gravity database errors, queries failing

**Cause**: Power failure or disk error

**Fix**:
```bash
ssh pi@pihole.local "sudo pihole -r --reconfigure"
```

**Severity**: High

---

### Update Fails

**Symptom**: `pihole -up` command fails

**Cause**: Network issue or Pi-hole repository unavailable

**Fix**:
1. Check internet connectivity on Pi
2. Retry later
3. Check Pi-hole discourse for known issues

**Severity**: Medium

---

### Web Interface 404

**Symptom**: Pi-hole admin panel not accessible

**Cause**: Lighttpd web server is down

**Fix**:
```bash
ssh pi@pihole.local "sudo systemctl restart lighttpd"
```

**Severity**: Medium

---

## Python Application Issues

### Virtual Environment Creation Failed

**Symptom**: venv creation fails on first run

**Cause**: `python3-venv` package not installed

**Fix**:
```bash
sudo apt install python3-venv
```

**Severity**: High

---

### Module Import Errors

**Symptom**: ImportError for rich or other dependencies

**Cause**: Dependencies not installed in virtual environment

**Fix**:
```bash
~/.pihole-manager-venv/bin/pip install -r requirements.txt
```

**Severity**: High

---

### Configuration File Not Found

**Symptom**: Config file not found error

**Cause**: Config file doesn't exist at `/opt/pihole-manager/config.yaml`

**Fix**:
```bash
# On the Pi, create config from template
sudo cp /opt/pihole-network-manager/config.yaml.template /opt/pihole-manager/config.yaml
sudo chown $USER:$USER /opt/pihole-manager/config.yaml

# Edit with your router details (if using router integration)
nano /opt/pihole-manager/config.yaml
```

**Severity**: High

---

### UI Rendering Issues

**Symptom**: Terminal UI displays incorrectly

**Cause**: Terminal doesn't support Rich library features

**Fix**:
1. Use modern terminal (e.g., GNOME Terminal, iTerm2)
2. Update Rich library: `pip install --upgrade rich`

**Severity**: Low

---

## Deployment Issues

### Git Clone Failed

**Symptom**: Cannot clone repository to Pi during installation

**Cause**: Permission error, disk space issue, or network connectivity

**Fix**:
1. Check disk space: `df -h`
2. Check permissions: `sudo chown -R $USER:$USER /opt/pihole-network-manager`
3. Verify internet connectivity: `ping -c 3 github.com`
4. Re-run clone: `cd /opt && sudo git clone https://github.com/yourusername/pihole-network-manager.git`

**Severity**: Medium

---

### Service Restart Failed

**Symptom**: Pi-hole service won't start after deployment

**Cause**: Configuration error or port conflict

**Fix**:
1. Check logs: `ssh pi@pihole.local "journalctl -u pihole-FTL -n 50"`
2. Verify config: `ssh pi@pihole.local "pihole -d"`
3. Check port 53 availability: `ssh pi@pihole.local "sudo lsof -i :53"`

**Severity**: High

---

### Test Pi Verification Failed

**Symptom**: UAT tests fail on test-pi.local

**Cause**: Feature not working as expected

**Fix**:
1. SSH to Test Pi and debug manually
2. Check Pi-hole logs: `/var/log/pihole.log`
3. Verify database changes took effect
4. Rollback if needed

**Severity**: Medium

---

### Rollback Command Fails

**Symptom**: Rollback completes but service still broken

**Cause**: Incomplete rollback or database corruption

**Fix**:
1. Restore from backup (most reliable)
2. Manual reconfigure: `ssh pi@pihole.local "sudo pihole -r --reconfigure"`
3. Worst case: Reinstall Pi-hole

**Severity**: High

---

## Router Integration Issues

### Authentication Failed

**Symptom**: Cannot connect to router via API

**Cause**: Wrong password in configuration

**Fix**:
1. Update router password in config
2. If using automation mode, re-encrypt password
3. Verify router is TP-Link AXE5400 (other routers not supported)

**Severity**: Medium

---

### Device List Empty

**Symptom**: Router returns empty device list

**Cause**: Router API issue or no devices connected

**Fix**:
1. Verify devices are connected to router
2. Reboot router
3. Check router web UI directly

**Severity**: Low

---

### MAC Blocking Not Working

**Symptom**: Device still has network access after MAC blocking

**Cause**: Device using different MAC or DHCP lease still active

**Fix**:
1. Reboot blocked device to force DHCP renewal
2. Verify MAC address is correct
3. Check router DHCP lease table

**Severity**: Medium

---

## Content Filter Issues

### Time-Based Rules Not Auto-Enforcing

**Symptom**: Time-based content filter rules don't activate automatically

**Cause**: **KNOWN LIMITATION** - Automatic enforcement not implemented

**Fix**: Manually enable/disable rules via management tool or create custom cron jobs

**Severity**: Medium
**Known Limitation**: Yes

---

### Rule Not Blocking Domains

**Symptom**: Content filter rule created but domains still accessible

**Cause**: Gravity not rebuilt after rule creation

**Fix**:
```bash
ssh pi@pihole.local "sudo pihole -g"
```

**Severity**: Medium

---

## Backup/Restore Issues

### Backup Download Failed

**Symptom**: Cannot download backup from Pi

**Cause**: Network issue or permission error

**Fix**:
1. Check SSH connection
2. Verify backup file exists on Pi: `ssh pi@pihole.local "ls -lh /opt/pihole-manager/backups/"`
3. Check local disk space

**Severity**: Medium

---

### Restore Failed

**Symptom**: Restore command completes but configuration not restored

**Cause**: Backup file corrupted or incomplete

**Fix**:
1. Verify backup file integrity
2. Try older backup
3. Manual reconfigure if all backups fail

**Severity**: High

---

## Network Issues

### Entire Network DNS Down

**Symptom**: All network devices lose internet connectivity

**Cause**: Production Pi-hole is down

**Fix**: **EMERGENCY ROLLBACK REQUIRED**

1. Quick fix: Set devices to use public DNS (8.8.8.8)
2. SSH to Pi and restart Pi-hole: `sudo systemctl restart pihole-FTL`
3. If Pi is down, reboot Pi
4. If issue persists, rollback last deployment

**Severity**: Critical

---

### Only Some Devices Affected

**Symptom**: Some devices have DNS issues, others work fine

**Cause**: Device-specific DNS override or content filter rule

**Fix**:
1. Check device-specific DNS overrides in device management
2. Check content filter rules targeting specific devices
3. Verify device is using Pi-hole as DNS server

**Severity**: Low

---

## Summary

**Most Common Issues**:
1. Sudoers not configured or user not in pihole-manager group (logout/login required)
2. Pi-hole service down (sudo systemctl restart pihole-FTL)
3. Gravity not rebuilt after changes (sudo pihole -g)
4. Config file not found (create from template)
5. Time-based content filtering (manual enforcement required)

**Emergency Procedures**:
- Network-wide DNS failure: See "Entire Network DNS Down"
- Production Pi deployment failure: See "Rollback Procedures" in deployment-procedures.md

**For additional help**:
- Check logs: `/var/log/pihole.log` and `journalctl -u pihole-FTL`
- Pi-hole documentation: https://docs.pi-hole.net/
- GitHub Issues: Create issue in repository
