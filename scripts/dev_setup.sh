#!/usr/bin/env bash
#
# Recon Framework - Development Environment Setup
#
# This script sets up everything needed for development:
# - Virtual environment with all production and dev dependencies
# - Pre‑commit hooks (linting, formatting, type‑checking)
# - Editable install of the framework
# - Local configuration for testing
#
# Usage:
#   chmod +x dev_setup.sh
#   ./dev_setup.sh [DEV_DIR]   # default: .venv in current directory

set -euo pipefail

# -- Colours --
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# -- Configuration --
DEV_DIR="${1:-.venv}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

info "Setting up development environment for Recon Framework..."
info "Repository root: $REPO_ROOT"

# -- Check Python --
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
    err "Python 3.10+ is required. Install it and re‑run."
    exit 1
fi
ok "Python: $($PYTHON --version)"

# -- Create virtual environment if missing --
if [ ! -d "$DEV_DIR" ]; then
    info "Creating virtual environment: $DEV_DIR"
    "$PYTHON" -m venv "$DEV_DIR"
fi

# Activate
source "$DEV_DIR/bin/activate"

# -- Upgrade pip and install build tools --
pip install --upgrade pip setuptools wheel &>/dev/null

# -- Install the package in editable mode with all dev extras --
info "Installing framework with dev dependencies..."
pip install -e ".[dev,pdf]" &>/dev/null
ok "Editable install complete."

# -- Install additional dev tools if not already present --
info "Checking code quality tools..."
pip install --quiet pre-commit black ruff mypy pytest pytest-cov &>/dev/null

# -- Set up pre‑commit hooks --
if [ -f ".pre-commit-config.yaml" ]; then
    info "Installing pre‑commit hooks..."
    pre-commit install --install-hooks &>/dev/null
    ok "Pre‑commit hooks installed."
else
    warn "No .pre-commit-config.yaml found. Creating one..."
    cat > .pre-commit-config.yaml <<EOF
repos:
  - repo: https://github.com/psf/black
    rev: 24.8.0
    hooks:
      - id: black
        language_version: python3.11
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.5.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.1
    hooks:
      - id: mypy
        additional_dependencies: [types-toml, types-requests]
EOF
    pre-commit install --install-hooks &>/dev/null
    ok "Pre‑commit hooks created and installed."
fi

# -- Initialize local test configuration --
if [ ! -f "tests/.env" ]; then
    info "Creating test environment file..."
    cat > tests/.env <<EOF
RECON_WORKSPACE_DIR=$REPO_ROOT/tests/tmp/workspaces
RECON_LOG_LEVEL=DEBUG
EOF
fi

# -- Create directories for testing --
mkdir -p tests/tmp/workspaces

# -- Run quick sanity check --
info "Running quick sanity test..."
if python -c "import recon; print(recon.__version__)" &>/dev/null; then
    ok "Framework imports successfully. Version: $(python -c 'import recon; print(recon.__version__)')"
else
    err "Framework import failed. Check installation."
    exit 1
fi

# -- Instructions --
cat <<EOF

====================================
${GREEN}Development environment ready!${NC}
====================================

Activate it with:
    source $DEV_DIR/bin/activate

Run tests:
    pytest -v --cov=recon tests/

Run linting:
    ruff check src/ tests/
    black --check src/ tests/
    mypy src/

Run pre-commit on all files:
    pre-commit run --all-files

Start developing!

EOF

exit 0