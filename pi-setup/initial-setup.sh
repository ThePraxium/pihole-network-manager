#!/bin/bash

################################################################################
# Pi-hole Network Manager - Initial Setup Bootstrap
#
# This script prepares the Raspberry Pi for the Python-based setup system.
# It installs Python, dependencies, creates directory structure, and launches
# the Python setup orchestrator.
#
# Usage: sudo ./initial-setup.sh
################################################################################

set -e  # Exit on error

# Non-interactive mode for apt-get and package configuration
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a  # Auto-restart services without prompting

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

# Banner
clear
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Pi-hole Network Manager - Initial Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log_info "Starting bootstrap process..."
echo ""

# Step 1: Update system packages
log_info "Step 1/8: Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq
log_success "System packages updated"

# Step 2: Install Python and pip
log_info "Step 2/8: Installing Python 3 and pip..."
apt-get install -y -qq python3 python3-pip python3-venv
PYTHON_VERSION=$(python3 --version)
log_success "Python installed: $PYTHON_VERSION"

# Step 3: Install essential system tools
log_info "Step 3/8: Installing essential system tools..."
apt-get install -y -qq \
    git \
    curl \
    wget \
    ufw \
    fail2ban \
    unattended-upgrades \
    htop \
    vim \
    dnsutils \
    net-tools \
    iptables

log_success "System tools installed"

# Step 4: Install Python packages
log_info "Step 4/8: Installing Python dependencies..."

# Install available packages via apt (system-managed, PEP 668 compliant)
log_info "Installing system Python packages via apt..."
apt-get install -y -qq \
    python3-rich \
    python3-yaml \
    python3-paramiko \
    python3-requests \
    python3-cryptography

# Create virtual environment for packages not available via apt
log_info "Creating virtual environment for additional packages..."
python3 -m venv /opt/pihole-manager/venv

# Install remaining packages in venv (tplinkrouterc6u not in Debian repos)
log_info "Installing additional packages in virtual environment..."
/opt/pihole-manager/venv/bin/pip install --quiet --upgrade pip
/opt/pihole-manager/venv/bin/pip install --quiet tplinkrouterc6u

log_success "Python packages installed (system + venv)"

# Step 5: Create directory structure
log_info "Step 5/8: Creating directory structure..."

# Create main directories
mkdir -p /opt/pihole-manager/{setup,api,backups,logs}
mkdir -p /etc/pihole/profiles
mkdir -p /var/log/pihole-manager

# Set permissions
chmod 755 /opt/pihole-manager
chmod 755 /etc/pihole/profiles
chmod 755 /var/log/pihole-manager

log_success "Directory structure created"

# Step 6: Copy setup files (if they exist in current directory)
log_info "Step 6/8: Checking for setup files..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d "$SCRIPT_DIR/setup" ]; then
    log_info "Copying setup modules to /opt/pihole-manager/setup/"
    cp -r "$SCRIPT_DIR/setup/"* /opt/pihole-manager/setup/
    log_success "Setup modules copied"
else
    log_warning "Setup modules not found in $SCRIPT_DIR/setup/"
    log_warning "Please manually copy setup files to /opt/pihole-manager/setup/"
fi

if [ -f "$SCRIPT_DIR/setup.py" ]; then
    log_info "Copying setup orchestrator..."
    cp "$SCRIPT_DIR/setup.py" /opt/pihole-manager/
    chmod +x /opt/pihole-manager/setup.py
    log_success "Setup orchestrator installed"
else
    log_warning "setup.py not found in $SCRIPT_DIR"
fi

if [ -d "$SCRIPT_DIR/api" ]; then
    log_info "Copying API backend..."
    cp -r "$SCRIPT_DIR/api/"* /opt/pihole-manager/api/
    log_success "API backend installed"
fi

if [ -d "$SCRIPT_DIR/profiles" ]; then
    log_info "Copying blocklist profiles..."
    cp -r "$SCRIPT_DIR/profiles/"* /etc/pihole/profiles/
    log_success "Blocklist profiles installed"
fi

# Step 7: Install sudoers configuration
log_info "Step 7/8: Configuring sudo permissions..."

if [ -f "$SCRIPT_DIR/templates/sudoers-pihole-manager" ]; then
    # Create pihole-manager group if it doesn't exist
    if ! getent group pihole-manager > /dev/null 2>&1; then
        groupadd pihole-manager
        log_success "Created pihole-manager group"
    fi

    # Add current user to pihole-manager group
    SUDO_USER_NAME=${SUDO_USER:-$(whoami)}
    if [ "$SUDO_USER_NAME" != "root" ]; then
        usermod -aG pihole-manager "$SUDO_USER_NAME"
        log_success "Added $SUDO_USER_NAME to pihole-manager group"
    fi

    # Install sudoers configuration
    cp "$SCRIPT_DIR/templates/sudoers-pihole-manager" /etc/sudoers.d/pihole-manager
    chmod 0440 /etc/sudoers.d/pihole-manager

    # Validate sudoers file
    if visudo -c -f /etc/sudoers.d/pihole-manager > /dev/null 2>&1; then
        log_success "Sudoers configuration installed and validated"
        log_info "Passwordless sudo enabled for pihole-manager commands"
    else
        log_error "Sudoers configuration validation failed!"
        rm /etc/sudoers.d/pihole-manager
        log_warning "Removed invalid sudoers file for safety"
    fi
else
    log_warning "Sudoers template not found at $SCRIPT_DIR/templates/sudoers-pihole-manager"
    log_warning "You may need to enter sudo password for Pi-hole operations"
fi

# Step 8: Create initial log file
log_info "Step 8/8: Initializing logging..."
touch /var/log/pihole-manager/setup.log
chmod 644 /var/log/pihole-manager/setup.log
log_success "Logging initialized"

# Bootstrap complete
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_success "Bootstrap complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log_info "System Information:"
echo "  • Python Version: $(python3 --version)"
echo "  • Pip Version: $(pip3 --version | cut -d' ' -f1-2)"
echo "  • OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '"')"
echo "  • Kernel: $(uname -r)"
echo "  • Architecture: $(uname -m)"
echo ""

# Check if setup.py exists
if [ -f "/opt/pihole-manager/setup.py" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "Next Steps:"
    echo ""
    echo "  1. Review the configuration in setup.py"
    echo "  2. Run the Python setup orchestrator via the management tool"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Bootstrap complete - setup wizard should be run separately via remote management
    log_info "Bootstrap complete. Run setup wizard via management tool."
else
    log_warning "Setup orchestrator not found at /opt/pihole-manager/setup.py"
    log_warning "Please copy the setup files manually and run setup.py"
fi

log_success "Initial setup complete!"
