# Pi-hole Network Manager - Installation Guide

Complete installation instructions for setting up Pi-hole Network Manager on your Raspberry Pi.

## Overview

Pi-hole Network Manager is a local management tool that runs directly on your Raspberry Pi. It provides a terminal-based interface for managing Pi-hole, blocklists, devices, and optionally your TP-Link router.

## System Requirements

### Hardware

- **Raspberry Pi**: Pi 4 Model B (2GB+ RAM recommended)
- **Storage**: MicroSD card 16GB+ (Class 10 or better)
- **Network**: Ethernet cable (Wi-Fi supported but not recommended for Pi-hole)
- **Power**: Official Raspberry Pi power supply or equivalent

### Software

- **Operating System**: Raspberry Pi OS Lite (64-bit)
- **Python**: Python 3.11 or higher (installed during setup)
- **Network**: Static IP address for Pi-hole (configured during initial setup)

### Optional

- **Router**: TP-Link AXE5400 (or compatible model) for router integration features

## Installation Steps

### Step 1: Prepare Raspberry Pi

**1.1 Flash SD Card**

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash Raspberry Pi OS:

1. Download and install Raspberry Pi Imager
2. Click "Choose OS" → Raspberry Pi OS (other) → **Raspberry Pi OS Lite (64-bit)**
3. Click "Choose Storage" → Select your SD card
4. Click the settings icon (⚙️) to configure:
   - Set hostname: `pihole` (recommended)
   - Enable SSH (with password authentication)
   - Set username and password
   - Configure Wi-Fi (optional, Ethernet recommended)
   - Set locale settings
5. Click "Write" and wait for completion

**1.2 Boot Raspberry Pi**

1. Insert SD card into Raspberry Pi
2. Connect Ethernet cable
3. Connect power supply
4. Wait 1-2 minutes for first boot

**1.3 Find Pi's IP Address**

Option A - Using hostname:
```bash
ping pihole.local
```

Option B - Check your router's DHCP leases:
- Log into router admin interface
- Look for device named "pihole" or your configured hostname

Option C - Network scan (Linux/Mac):
```bash
sudo nmap -sn 192.168.1.0/24  # Adjust subnet to match your network
```

### Step 2: SSH into Pi

```bash
ssh username@pihole.local
# Or use IP address if hostname doesn't work:
# ssh username@192.168.1.xxx
```

**First Login:**
- Accept SSH fingerprint when prompted
- Enter password you set during SD card preparation

### Step 3: Clone Repository

```bash
# Navigate to /opt directory
cd /opt

# Clone the repository (replace with actual repository URL)
sudo git clone https://github.com/YOUR_USERNAME/pihole-network-manager.git

# Set ownership to current user
sudo chown -R $USER:$USER /opt/pihole-network-manager

# Navigate to project directory
cd /opt/pihole-network-manager
```

### Step 4: Run Initial Setup

The initial setup script will:
- Update system packages
- Install Python 3.11+ and required system dependencies
- Configure passwordless sudo for Pi-hole commands
- Create configuration directories
- Set up Python virtual environment
- Install Python dependencies
- Mark setup as complete

**Run the setup script:**

```bash
sudo ./pi-setup/initial-setup.sh
```

**Expected output:**
```
=== Pi-hole Network Manager - Initial Setup ===

Step 1/7: Updating system packages...
✓ System packages updated

Step 2/7: Installing system dependencies...
✓ Python 3.11 installed
✓ SQLite3 installed
✓ Git installed

Step 3/7: Creating pihole-manager group...
✓ Group created
✓ User added to group

Step 4/7: Installing sudoers configuration...
✓ Sudoers file installed
✓ Syntax validated

Step 5/7: Creating configuration directory...
✓ Directory created: /opt/pihole-manager

Step 6/7: Setting up Python virtual environment...
✓ Virtual environment created
✓ Pip upgraded
✓ Dependencies installed

Step 7/7: Marking setup as complete...
✓ State file created

=== Setup Complete! ===

You can now run the manager:
  cd /opt/pihole-network-manager
  python3 main.py
```

**Important Notes:**
- The script requires sudo access
- Setup takes 5-10 minutes depending on your internet speed
- You may need to log out and log back in for group changes to take effect
- If setup fails, check `/var/log/pihole-setup.log` for errors

### Step 5: Run the Manager

```bash
cd /opt/pihole-network-manager
python3 main.py
```

**First Run:**
- Virtual environment activates automatically
- All dependencies are already installed
- Main menu appears immediately

## Post-Installation Configuration

### Configure Pi-hole Web URL (Optional)

The web URL is used for quick browser access from the management tool:

1. Run the manager: `python3 main.py`
2. Select "Configuration" from main menu
3. Select "Edit Settings"
4. Edit `/opt/pihole-manager/config.yaml`
5. Set `web_url` to your Pi-hole admin URL (e.g., `http://192.168.1.100/admin`)

### Configure Router Integration (Optional)

For TP-Link router control features:

1. Run the manager: `python3 main.py`
2. Select "Pi-hole Management" → "Router Control"
3. Follow prompts to enter:
   - Router IP address
   - Admin username (usually `admin`)
   - Admin password
4. Credentials are encrypted and stored in `/opt/pihole-manager/config.yaml`

### Set Static IP for Pi-hole

**Important**: Pi-hole requires a static IP address.

**Option A - Configure on Router (Recommended):**
1. Log into router admin interface
2. Find DHCP settings
3. Reserve current IP for Pi's MAC address
4. This survives SD card replacements

**Option B - Configure on Pi:**
```bash
# Edit dhcpcd configuration
sudo nano /etc/dhcpcd.conf

# Add at end (adjust values for your network):
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=1.1.1.1 8.8.8.8

# Save and restart
sudo systemctl restart dhcpcd
```

### Configure Router DNS

Point your router's DNS to Pi-hole for network-wide blocking:

1. Log into router admin interface
2. Navigate to DHCP settings
3. Set Primary DNS to Pi-hole IP (e.g., `192.168.1.100`)
4. Set Secondary DNS to fallback (e.g., `1.1.1.1` or `8.8.8.8`)
5. Save and reboot router

**Verification:**
- Run health check in manager: Management → Health & Diagnostics → Run Full Health Check
- Visit Pi-hole admin interface and check query log
- Test ad blocking on a device

## Daily Usage

### Starting the Manager

```bash
# SSH into your Pi
ssh username@pihole.local

# Run the manager
cd /opt/pihole-network-manager
python3 main.py
```

### Main Menu Options

**Pi-hole Management:**
- Blocklist Management - Switch profiles, add/remove lists
- Device Management - Manage devices, set custom DNS
- Whitelist/Blacklist - Domain allow/block lists
- Content Filtering - Time-based website blocking
- Statistics & Monitoring - Query stats, top domains, logs
- Router Control - TP-Link router integration (if configured)
- Maintenance & Updates - System updates, service restarts
- Health & Diagnostics - Health checks, troubleshooting

**Configuration:**
- View current settings
- Edit configuration file

### Useful Commands

**Check Pi-hole status:**
```bash
pihole status
```

**Restart Pi-hole DNS:**
```bash
pihole restartdns
```

**Update Pi-hole:**
```bash
pihole -up
```

**View Pi-hole logs:**
```bash
tail -f /var/log/pihole.log
```

**Check manager logs:**
```bash
ls -lh /tmp/pihole-manager-*.log
tail -f /tmp/pihole-manager-$(date +%Y%m%d).log
```

## Troubleshooting

### Application won't start

**Symptom:** `python3 main.py` fails or shows errors

**Solutions:**
```bash
# Check Python version (must be 3.11+)
python3 --version

# Verify setup completed
cat /opt/pihole-manager/state.json

# If state file missing, re-run setup
sudo ./pi-setup/initial-setup.sh

# Delete and recreate virtual environment
rm -rf ~/.pihole-manager-venv
python3 main.py  # Will recreate venv
```

### Permission denied errors

**Symptom:** Commands fail with "permission denied"

**Solutions:**
```bash
# Verify sudoers configuration
sudo visudo -c -f /etc/sudoers.d/pihole-manager

# Check group membership (log out and back in if recently added)
groups
# Should show: ... pihole-manager ...

# Re-run initial setup if needed
sudo ./pi-setup/initial-setup.sh
```

### Pi-hole not blocking ads

**Symptom:** Ads still appearing on devices

**Solutions:**
1. **Run health check in manager:**
   - Management → Health & Diagnostics → Run Full Health Check
   - Check for DNS resolution failures

2. **Verify router DNS settings:**
   - Router should point to Pi-hole IP
   - Devices should receive Pi-hole as DNS from DHCP

3. **Check device DNS override:**
   - Some devices (phones, smart TVs) may have hardcoded DNS
   - Check device network settings

4. **Restart Pi-hole:**
   ```bash
   pihole restartdns
   ```

### Router integration not working

**Symptom:** Router control features fail

**Solutions:**
```bash
# Test router connectivity from Pi
ping <router-ip>

# Test SSH to router
ssh admin@<router-ip>

# Verify credentials in manager
# Configuration → View Current Configuration

# Check router model compatibility
# Only TP-Link AXE5400 and similar models supported
```

### Database errors

**Symptom:** "Database locked" or integrity errors

**Solutions:**
```bash
# Stop Pi-hole FTL
sudo systemctl stop pihole-FTL

# Run integrity check
sudo sqlite3 /etc/pihole/gravity.db 'PRAGMA integrity_check;'
sudo sqlite3 /etc/pihole/pihole-FTL.db 'PRAGMA integrity_check;'

# If corrupted, restore from backup or rebuild
pihole -g  # Rebuild gravity

# Restart FTL
sudo systemctl start pihole-FTL
```

### SD card issues

**Symptom:** System slowing down, corruption errors

**Solutions:**
```bash
# Check SD card health
sudo dmesg | grep -i mmc

# Check filesystem
sudo touch /forcefsck
sudo reboot

# Monitor disk usage
df -h
```

**Prevention:**
- Use high-quality SD cards (SanDisk Extreme, Samsung EVO)
- Consider USB boot for better reliability
- Regular backups

## File Locations Reference

| Component | Location | Purpose |
|-----------|----------|---------|
| Application | `/opt/pihole-network-manager/` | Manager installation |
| Configuration | `/opt/pihole-manager/config.yaml` | Settings and credentials |
| State File | `/opt/pihole-manager/state.json` | Setup completion tracking |
| Sudoers | `/etc/sudoers.d/pihole-manager` | Passwordless sudo rules |
| Session Logs | `/tmp/pihole-manager-*.log` | Daily session logs |
| Virtual Env | `~/.pihole-manager-venv/` | Python dependencies |
| Pi-hole Gravity | `/etc/pihole/gravity.db` | Blocklist database |
| Pi-hole FTL | `/etc/pihole/pihole-FTL.db` | Query database |
| Pi-hole Config | `/etc/pihole/` | Pi-hole configuration |

## Updating the Manager

To update to the latest version:

```bash
cd /opt/pihole-network-manager

# Pull latest changes
git pull

# Update dependencies
source ~/.pihole-manager-venv/bin/activate
pip install -r requirements.txt --upgrade
deactivate

# Run the updated manager
python3 main.py
```

## Uninstallation

To completely remove Pi-hole Network Manager:

```bash
# Remove application
sudo rm -rf /opt/pihole-network-manager

# Remove configuration
sudo rm -rf /opt/pihole-manager

# Remove virtual environment
rm -rf ~/.pihole-manager-venv

# Remove sudoers configuration
sudo rm /etc/sudoers.d/pihole-manager

# Remove group (optional)
sudo groupdel pihole-manager

# Remove logs
rm /tmp/pihole-manager-*.log
```

**Note**: This does not remove Pi-hole itself. To uninstall Pi-hole, run:
```bash
pihole uninstall
```

## Getting Help

- **Documentation**: Check `docs/` folder for detailed guides
- **Pi-hole Docs**: https://docs.pi-hole.net/
- **GitHub Issues**: Report bugs or request features
- **Health Check**: Use built-in diagnostics (Management → Health & Diagnostics)

## Security Considerations

- **SSH Access**: Consider using SSH keys instead of password authentication
- **Firewall**: UFW is configured during setup (SSH, DNS, HTTP/HTTPS only)
- **Updates**: System is configured for automatic security updates
- **Router Passwords**: Stored encrypted in config file
- **Sudo**: Limited to specific Pi-hole commands only

## Next Steps

After installation:

1. ✅ Install Pi-hole (if not already installed)
2. ✅ Configure static IP
3. ✅ Point router DNS to Pi-hole
4. ✅ Choose blocklist profile (Management → Blocklist Management)
5. ✅ Run health check (Management → Health & Diagnostics)
6. ✅ Monitor statistics (Management → Statistics & Monitoring)
7. ✅ Configure router integration (optional)

Enjoy network-wide ad blocking! 🎉
