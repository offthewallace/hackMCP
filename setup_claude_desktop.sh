#!/bin/bash
# Setup script to configure FerroSim MCP Server with Claude Desktop

set -e

echo "=================================================="
echo "FerroSim MCP - Claude Desktop Configuration"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Claude Desktop config location on macOS
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

# Check if Claude Desktop is installed
if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    echo -e "${RED}✗ Claude Desktop not found${NC}"
    echo "Please install Claude Desktop first from:"
    echo "https://claude.ai/download"
    exit 1
fi

echo -e "${GREEN}✓ Claude Desktop directory found${NC}"

# Backup existing config if it exists
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    BACKUP_FILE="$CLAUDE_CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}Backing up existing config to:${NC}"
    echo "  $BACKUP_FILE"
    cp "$CLAUDE_CONFIG_FILE" "$BACKUP_FILE"
fi

# Get the current directory
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get Python path from conda environment
PYTHON_PATH="/Users/guanlinhe/miniconda3/envs/ferrosim_mcp/bin/python"

if [ ! -f "$PYTHON_PATH" ]; then
    echo -e "${RED}✗ Python not found at $PYTHON_PATH${NC}"
    echo "Please make sure the ferrosim_mcp conda environment is set up"
    exit 1
fi

echo -e "${GREEN}✓ Found Python at $PYTHON_PATH${NC}"

# Create the config file
echo ""
echo "Creating Claude Desktop configuration..."

cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "ferrosim": {
      "command": "$PYTHON_PATH",
      "args": [
        "$CURRENT_DIR/ferrosim_mcp_server_minimal.py"
      ],
      "env": {}
    }
  }
}
EOF

echo -e "${GREEN}✓ Configuration file created${NC}"
echo ""
echo "Config location: $CLAUDE_CONFIG_FILE"
echo ""
echo "Configuration content:"
cat "$CLAUDE_CONFIG_FILE"
echo ""
echo "=================================================="
echo -e "${GREEN}Setup Complete! 🎉${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Quit Claude Desktop completely (Cmd+Q)"
echo ""
echo "2. Restart Claude Desktop"
echo ""
echo "3. In Claude Desktop, you should now see 'ferrosim' MCP server"
echo "   available in the tools/integrations"
echo ""
echo "4. Try asking Claude:"
echo "   'Can you run a FerroSim simulation with n=15 and k=1.5?'"
echo ""
echo "Available MCP Tools:"
echo "  - initialize_simulation: Create new simulation"
echo "  - run_simulation: Execute simulation"
echo "  - get_simulation_results: Retrieve results"
echo "  - compare_with_afm_data: Compare with experimental data"
echo "  - list_simulations: List all active simulations"
echo ""
echo "If you don't see the server in Claude Desktop:"
echo "  1. Check the Developer Console in Claude Desktop"
echo "  2. Look for any error messages"
echo "  3. Verify the paths in: $CLAUDE_CONFIG_FILE"
echo ""

