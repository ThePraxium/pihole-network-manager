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

# Determine project root (parent of pi-setup directory where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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

# Note: Virtual environment will be created automatically by main.py on first run
log_info "Skipping venv creation (will be auto-created on first run)..."

log_success "Python packages installed (system + venv)"

# Step 5: Create directory structure within project
log_info "Step 5/8: Creating directory structure..."

# Create project subdirectories
mkdir -p "$PROJECT_ROOT"/{data,logs,profiles}
mkdir -p /etc/pihole/profiles

# Set permissions
chmod 755 "$PROJECT_ROOT"/data
chmod 755 "$PROJECT_ROOT"/logs
chmod 755 "$PROJECT_ROOT"/profiles
chmod 755 /etc/pihole/profiles

log_success "Directory structure created"

# Step 6: Setup files are already in place (git cloned)
log_info "Step 6/8: Verifying project structure..."
log_success "Project files found at $PROJECT_ROOT"

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
touch "$PROJECT_ROOT/logs/setup.log"
chmod 644 "$PROJECT_ROOT/logs/setup.log"
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

# Verify main.py exists (entry point)
if [ -f "$PROJECT_ROOT/main.py" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "Next Steps:"
    echo ""
    echo "  1. Run the application: python3 $PROJECT_ROOT/main.py"
    echo "  2. Venv will be created automatically on first run"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    log_info "Bootstrap complete. You can now run the application."
else
    log_warning "Main application not found at $PROJECT_ROOT/main.py"
    log_warning "Please verify the repository was cloned correctly"
fi

log_success "Initial setup complete!"
