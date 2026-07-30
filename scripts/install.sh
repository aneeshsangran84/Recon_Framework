#!/usr/bin/env bash
#
# Recon Framework - Production Installation Script
#
# This script:
# 1. Checks Python 3.10+ availability
# 2. Creates a Python virtual environment
# 3. Installs the framework and its dependencies
# 4. Initialises default configuration
# 5. Runs a self‑test to verify functionality
#
# Usage:
#   chmod +x install.sh
#   ./install.sh [INSTALL_DIR]   # default: $HOME/.recon

set -euo pipefail

# -- Colour helpers --
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# -- Determine install directory --
INSTALL_DIR="${1:-$HOME/.recon}"
VENV_DIR="$INSTALL_DIR/venv"

info "Recon Framework Installer"
info "Install directory: $INSTALL_DIR"

# -- Prerequisite: Python 3.10+ --
PYTHON=""
for py in python3.12 python3.11 python3.10 python3; do
    if command -v "$py" &>/dev/null; then
        ver=$("$py" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$py"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    err "Python 3.10 or higher is required. Please install it and re‑run."
    exit 1
fi
ok "Using Python: $($PYTHON --version)"

# -- Create directories --
mkdir -p "$INSTALL_DIR" || {
    err "Cannot create directory $INSTALL_DIR"
    exit 1
}

# -- Virtual environment --
if [ ! -d "$VENV_DIR" ]; then
    info "Creating virtual environment in $VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
    ok "Virtual environment created."
else
    info "Virtual environment already exists, skipping creation."
fi

# Activate
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# -- Upgrade pip and install build tools --
info "Upgrading pip and installing build dependencies..."
pip install --upgrade pip setuptools wheel &>/dev/null

# -- Install the framework --
info "Installing Recon Framework..."
# We assume the script is run from the repo root (or the package is in the current directory)
if [ -f "pyproject.toml" ]; then
    pip install . &>/dev/null
else
    # Maybe it was pip installed; attempt to install from PyPI
    pip install recon-framework &>/dev/null
fi
ok "Framework installed."

# -- Initialize default configuration if missing --
CONFIG_DIR="$HOME/.config/recon"
CONFIG_FILE="$CONFIG_DIR/config.toml"
if [ ! -f "$CONFIG_FILE" ]; then
    info "Creating default configuration..."
    mkdir -p "$CONFIG_DIR"
    # Copy the built-in default.toml as a starting point
    # The package should be installed, so we can locate the default file
    DEFAULT_TOML=$(python -c "from pathlib import Path; import recon.config; print(Path(recon.config.__file__).parent/'default.toml')" 2>/dev/null || true)
    if [ -n "$DEFAULT_TOML" ] && [ -f "$DEFAULT_TOML" ]; then
        cp "$DEFAULT_TOML" "$CONFIG_FILE"
        ok "Default configuration written to $CONFIG_FILE"
    else
        warn "Could not locate default.toml; creating minimal config."
        cat > "$CONFIG_FILE" <<EOF
[general]
workspace_dir = "$INSTALL_DIR/workspaces"
threads = 10
timeout = 30

[logging]
level = "INFO"
format = "text"
file_enabled = true
file_dir = "$INSTALL_DIR/logs"
EOF
    fi
fi

# -- Run self-test --
info "Running self‑test..."
if recon --version &>/dev/null; then
    ok "Self‑test passed: recon --version succeeded."
else
    err "Self‑test failed. Check the installation."
    exit 1
fi

# -- Final message --
cat <<EOF

========================================
${GREEN}Recon Framework installation complete!${NC}
========================================

The 'recon' command is now available within the virtual environment.
To activate the environment in a new shell, run:

    source $VENV_DIR/bin/activate

Or add the following to your ~/.bashrc / ~/.zshrc:

    alias recon='$VENV_DIR/bin/recon'

EOF

exit 0
