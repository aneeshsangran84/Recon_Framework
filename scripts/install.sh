#!/usr/bin/env bash
#
# Recon Framework - Production Installation Script
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
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# -- Determine install directory --
INSTALL_DIR="${1:-$HOME/.recon}"
VENV_DIR="$INSTALL_DIR/venv"

echo ""
info "============================================"
info "  Recon Framework Installer"
info "============================================"
info "Install directory: $INSTALL_DIR"
echo ""

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
    err "Python 3.10 or higher is required. Please install it and re-run."
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
source "$VENV_DIR/bin/activate"

# -- Upgrade pip --
info "Upgrading pip..."
pip install --upgrade pip setuptools wheel --quiet 2>/dev/null
ok "pip upgraded."

# -- Install the framework --
info "Installing Recon Framework..."
if [ -f "pyproject.toml" ]; then
    pip install . --quiet 2>/dev/null
elif [ -f "../pyproject.toml" ]; then
    pip install .. --quiet 2>/dev/null
else
    pip install recon-framework --quiet 2>/dev/null || {
        err "Could not find pyproject.toml. Run this script from the repo root."
        exit 1
    }
fi
ok "Framework installed."

# -- Install tomli_w for config management --
pip install tomli_w --quiet 2>/dev/null

# -- Initialize default configuration if missing --
CONFIG_DIR="$HOME/.config/recon"
CONFIG_FILE="$CONFIG_DIR/config.toml"
if [ ! -f "$CONFIG_FILE" ]; then
    info "Creating default configuration..."
    mkdir -p "$CONFIG_DIR"
    
    # Try to copy default.toml from installed package
    DEFAULT_TOML=$(python -c "from pathlib import Path; import recon.config; print(Path(recon.config.__file__).parent/'default.toml')" 2>/dev/null || true)
    if [ -n "$DEFAULT_TOML" ] && [ -f "$DEFAULT_TOML" ]; then
        cp "$DEFAULT_TOML" "$CONFIG_FILE"
        ok "Default configuration written to $CONFIG_FILE"
    else
        # Create minimal config
        cat > "$CONFIG_FILE" << 'EOF'
[general]
workspace_dir = "~/.recon/workspaces"
threads = 10
timeout = 30
user_agent = "ReconFramework/0.1"

[logging]
level = "INFO"
format = "text"
file_enabled = true
file_dir = "~/.recon/logs"

[plugins]
auto_enable_safe = true
disabled_plugins = []

[report]
template_dir = ""
company_name = "Security Assessment Team"
EOF
        ok "Minimal configuration created at $CONFIG_FILE"
    fi
else
    ok "Configuration already exists at $CONFIG_FILE"
fi

# -- Create system-wide command --
echo ""
info "Setting up system-wide 'recon' command..."

SYMLINK_CREATED=false

if [ -w /usr/local/bin ]; then
    ln -sf "$VENV_DIR/bin/recon" /usr/local/bin/recon 2>/dev/null && SYMLINK_CREATED=true
else
    sudo ln -sf "$VENV_DIR/bin/recon" /usr/local/bin/recon 2>/dev/null && SYMLINK_CREATED=true
fi

if [ "$SYMLINK_CREATED" = true ]; then
    ok "Command 'recon' is now available system-wide."
    echo ""
    echo "  You can run 'recon' from any terminal."
else
    warn "Could not create system-wide command (no sudo?)."
    echo ""
    echo "  Add this alias to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo "    alias recon='source $VENV_DIR/bin/activate && recon'"
    echo ""
    echo "  Or activate the venv before use:"
    echo "    source $VENV_DIR/bin/activate"
fi

# -- Run self-test --
echo ""
info "Running self-test..."
if "$VENV_DIR/bin/recon" --version &>/dev/null; then
    ok "Self-test passed!"
    "$VENV_DIR/bin/recon" --version
else
    err "Self-test failed. Check the installation."
    exit 1
fi

# -- Final message --
echo ""
echo "============================================"
echo -e "${GREEN}  Recon Framework installation complete!${NC}"
echo "============================================"
echo ""
echo "  Quick start:"
echo "    recon --help"
echo "    recon project create my-project"
echo "    recon scan --project my-project example.com"
echo ""

exit 0
