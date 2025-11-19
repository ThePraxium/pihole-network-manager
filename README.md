# Pi-hole Network Management System

A comprehensive network management solution for Pi-hole with advanced content filtering and optional TP-Link router integration, running directly on your Raspberry Pi.

## Features

- **Network-wide Ad Blocking**: Pi-hole DNS-based ad blocking for all devices
- **Advanced Content Filtering**: Time-based, device-specific website blocking
- **Router Integration**: TP-Link AXE5400 control (device blocking, DHCP, bandwidth monitoring)
- **Multiple Blocklist Profiles**: Light (~100K), Moderate (~300K), Aggressive (~1M+ domains)
- **Unified Management**: Single Python TUI running on your Pi
- **Security Hardening**: UFW firewall, fail2ban, auto-updates
- **Health Diagnostics**: DNS testing, service monitoring, system checks

## Architecture

### Local Execution Model

Pi-hole Network Manager runs **directly on your Raspberry Pi** - no remote SSH connection required. All management operations execute locally with proper sudo permissions configured during setup.

**Components:**
- **Management TUI**: Python application for all Pi-hole operations
- **Local Executor**: Subprocess-based command execution with passwordless sudo
- **Setup Scripts**: Automated Pi-hole installation and configuration

### Router Control

Router operations use SSH to communicate with your TP-Link router:
- **Default Mode**: Router credentials stay on Pi in encrypted form
- **All operations**: Executed from Pi to router via SSH

## Quick Start

### Prerequisites

- Raspberry Pi 4 Model B (2GB+ RAM recommended)
- MicroSD card (16GB+ recommended, Class 10 or better)
- TP-Link AXE5400 router (optional, for router integration features)
- Ethernet cable
- Raspberry Pi OS Lite (64-bit)

### Installation

**Step 1: Prepare SD Card**
1. Flash Raspberry Pi OS Lite (64-bit) using Raspberry Pi Imager
2. Enable SSH and set username/password in Imager settings
3. Insert SD card, connect Pi via Ethernet, power on
4. Wait for Pi to boot and obtain IP address

**Step 2: Clone Repository on Pi**
```bash
# SSH into your Pi
ssh username@pihole.local  # or use IP address

# Clone the repository
cd /opt
sudo git clone https://github.com/YOUR_REPO/pihole-network-manager.git
sudo chown -R $USER:$USER /opt/pihole-network-manager

# Run initial setup
cd /opt/pihole-network-manager
sudo ./pi-setup/initial-setup.sh
```

**Step 3: Run the Manager**
```bash
cd /opt/pihole-network-manager
python3 main.py
```

That's it! The application will:
- Automatically create and activate a virtual environment
- Install all required dependencies
- Present the management menu

### Initial Setup

The `initial-setup.sh` script automatically:
- Installs system dependencies (Python, SQLite, etc.)
- Configures passwordless sudo for Pi-hole commands
- Sets up the Python virtual environment
- Creates configuration directories
- Marks setup as complete

After running `initial-setup.sh`, you can immediately use the management tool.

## Directory Structure

```
pihole-network-manager/
├── main.py                # Main entry point - TUI application
│
├── core/                  # Core utilities
│   ├── config.py          # Configuration management
│   ├── local_executor.py  # Local command execution
│   ├── state.py           # Setup state tracking
│   ├── ui.py              # Rich-based TUI components
│   └── logger.py          # Session logging
│
├── management/            # Management modules
│   ├── blocklists.py      # Blocklist profile management
│   ├── devices.py         # Device management and DNS overrides
│   ├── lists.py           # Whitelist/blacklist management
│   ├── content_filter.py  # Time-based website blocking
│   ├── stats.py           # Query analytics and statistics
│   ├── router_control.py  # TP-Link router integration (via SSH)
│   ├── maintenance.py     # Updates and system maintenance
│   └── health.py          # Health checks and diagnostics
│
├── pi-setup/              # Setup scripts
│   ├── initial-setup.sh   # Bash bootstrap script
│   ├── templates/         # Configuration templates
│   │   └── sudoers-pihole-manager  # Passwordless sudo config
│   └── profiles/          # Blocklist profile definitions
│       ├── light.yaml
│       ├── moderate.yaml
│       └── aggressive.yaml
│
├── requirements.txt       # Python dependencies
│
└── docs/                  # Documentation
    ├── architecture.md
    ├── code-reference.md
    ├── development-guide.md
    └── troubleshooting-guide.md
```

## Management Tool Features

### 1. Blocklist Management
- Switch between Light/Moderate/Aggressive profiles
- Add/remove custom blocklists
- View current block count
- Update gravity database

### 2. Device & DNS Management
- Unified device view (Pi-hole + router data)
- Set custom DNS per device
- Device-friendly names and grouping
- Bypass Pi-hole for specific devices

### 3. Content Filtering
- Block/allow specific websites (reddit, facebook, instagram, etc.)
- Per-device rules with time scheduling
- Pre-made templates for common categories
- Interactive wizard for rule creation

### 4. Router Control (Optional)
- View connected devices with bandwidth stats
- Network-level device blocking (MAC filtering)
- DHCP lease information
- Guest network control
- Remote router reboot

### 5. Statistics & Monitoring
- Query dashboard (total, blocked %, top domains)
- Top clients and query types
- Real-time query log
- Domain history search

### 6. System Maintenance
- Update Pi-hole and Raspberry Pi OS
- Restart services and reboot Pi
- System resource monitoring (CPU, RAM, disk, temp)
- Clear logs and flush cache

### 7. Health & Diagnostics
- Run full health check
- Test DNS resolution
- Test blocking functionality
- Check service status
- Network connectivity test
- Database integrity check
- View error logs
- Generate diagnostic report

## Blocklist Profiles

**Light (~100K domains)**
- StevenBlack's Unified Hosts
- AdGuard DNS filter (sanitized)
- EasyList essentials
- Best for: Minimal breakage, basic ad blocking

**Moderate (~300K domains) - DEFAULT**
- All Light lists
- AdGuard DNS filter (full)
- EasyPrivacy tracking protection
- Fanboy's Enhanced Tracking
- Malware/Phishing domains
- Best for: Comprehensive blocking, rare breakage

**Aggressive (~1M+ domains)**
- All Moderate lists
- OISD Big List
- 1Hosts Pro
- HaGeZi's Ultimate
- Energized Ultimate
- Social media trackers
- Telemetry blocking
- Best for: Maximum blocking, active whitelisting

**Custom**
- User-defined lists
- Clone and modify existing profiles

## Security Features

- **Firewall**: UFW configured (SSH, DNS, HTTP/HTTPS only)
- **Fail2ban**: SSH brute-force protection
- **Auto-updates**: Unattended security updates
- **Passwordless Sudo**: Specific Pi-hole commands only (via sudoers.d)
- **Encrypted Credentials**: Router passwords encrypted when stored
- **SD Card Optimization**: Reduced swap wear

## Router Configuration

**Configure TP-Link AXE5400:**
1. Navigate to: Advanced → Network → DHCP Server
2. Set Primary DNS to Pi-hole IP (e.g., 192.168.1.100)
3. Optional: Set Secondary DNS to 1.1.1.1 (fallback)
4. Save and reboot router

**For Router Integration:**
- Go to Management → Router Control
- Enter router IP, username, and password
- Credentials are encrypted and stored in `/opt/pihole-manager/config.yaml`

## Known Limitations

**Time-Based Content Filtering:**
- Content filtering rules can be created with time schedules (e.g., "block social media 9am-5pm")
- **Manual enforcement required**: Rules must be manually enabled/disabled at scheduled times
- **Workaround**: Use the management tool to enable/disable rules as needed, or create custom cron jobs

**Router API Features:**
- Some advanced router features are pending hardware testing with TP-Link AXE5400:
  - DHCP lease management
  - Detailed bandwidth statistics per device
  - Guest network configuration
- **Impact**: These features appear in menus but may not function correctly
- **Workaround**: Use router's web interface for these advanced features
- **Note**: Basic router features (device list, blocking, reboot) are fully functional

**Platform Compatibility:**
- Tested on Raspberry Pi OS (64-bit) only
- TP-Link router integration is model-specific (designed for AXE5400)
- IPv6 support not fully tested
- Local network access only

**Historical Statistics:**
- Query trend graphs and historical analysis are placeholder implementations
- **Workaround**: Export raw statistics to CSV for analysis in external tools

## Daily Usage

After initial setup is complete, SSH into your Pi and run:

```bash
cd /opt/pihole-network-manager
python3 main.py
```

The virtual environment is automatically activated, and you'll see the main menu with:

- **Pi-hole Management**: All daily operations (blocklists, devices, stats, etc.)
- **Configuration**: View/edit configuration settings

Navigate using number keys and enjoy network-wide ad blocking!

## Troubleshooting

**Application won't start:**
- Ensure you ran `initial-setup.sh`: `sudo ./pi-setup/initial-setup.sh`
- Check Python 3.11+ is installed: `python3 --version`
- Delete venv if corrupted: `rm -rf ~/.pihole-manager-venv`
- Re-run `python3 main.py` to recreate venv

**Pi-hole not blocking ads:**
- Run Health Check via Management → Health & Diagnostics
- Verify router DNS points to Pi-hole IP
- Check device DNS settings aren't overridden
- Restart Pi-hole: `pihole restartdns`

**Permission denied errors:**
- Verify sudoers configuration: `sudo visudo -c -f /etc/sudoers.d/pihole-manager`
- Re-run initial setup if needed: `sudo ./pi-setup/initial-setup.sh`

**Router integration not working:**
- Verify router IP and admin password in Configuration menu
- Check router is accessible from Pi: `ping <router-ip>`
- Test SSH to router: `ssh admin@<router-ip>`
- Check router firmware version compatibility

## Configuration Files

- **Pi Configuration**: `/opt/pihole-manager/config.yaml`
- **State File**: `/opt/pihole-manager/state.json`
- **Sudoers**: `/etc/sudoers.d/pihole-manager`
- **Session Logs**: `/tmp/pihole-manager-<date>.log`

## Requirements

### Hardware
- Raspberry Pi 4 Model B (2GB+ RAM recommended)
- MicroSD card 16GB+ (Class 10 or better)
- Ethernet cable
- Power supply (official recommended)

### Software
- Raspberry Pi OS Lite (64-bit)
- Python 3.11+
- Dependencies installed automatically via requirements.txt

### Network (Optional for Router Integration)
- TP-Link AXE5400 router (or compatible TP-Link model)
- Static IP for Pi-hole
- Access to router admin interface

## Contributing

Contributions welcome! Please open issues or pull requests.

## License

MIT License

## Acknowledgments

- [Pi-hole](https://pi-hole.net/) - Network-wide ad blocking
- [Rich](https://github.com/Textualize/rich) - Python TUI library
- [tplinkrouterc6u](https://github.com/AlexandrErohin/TP-Link-Archer-C6U) - TP-Link router integration

## Support

For issues and questions:
- Check documentation in `docs/` folder
- Review Pi-hole documentation: https://docs.pi-hole.net/
- Open an issue on GitHub
