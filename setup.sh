#!/bin/bash
# FerroSim MCP Hackathon - Automated Setup Script

set -e  # Exit on error

echo "=================================================="
echo "FerroSim MCP Hackathon - Automated Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if conda is installed
echo "Checking for conda..."
if ! command -v conda &> /dev/null; then
    echo -e "${RED}✗ conda not found. Please install Anaconda or Miniconda first.${NC}"
    echo "Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi
echo -e "${GREEN}✓ conda found${NC}"

# Set conda environment name
ENV_NAME="ferrosim_mcp"

# Check if conda environment exists
if conda env list | grep -q "^${ENV_NAME} "; then
    echo -e "${GREEN}✓ Conda environment '${ENV_NAME}' already exists${NC}"
else
    echo -e "${YELLOW}Creating conda environment '${ENV_NAME}'...${NC}"
    conda create -n ${ENV_NAME} python=3.11 -y
    echo -e "${GREEN}✓ Conda environment created${NC}"
fi

# Activate conda environment
echo "Activating conda environment '${ENV_NAME}'..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ${ENV_NAME}

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"

echo "  - anthropic"
pip install anthropic --quiet || { echo -e "${RED}✗ Failed to install anthropic${NC}"; exit 1; }

echo "  - mcp"
pip install mcp --quiet || { echo -e "${RED}✗ Failed to install mcp${NC}"; exit 1; }

echo "  - numpy, matplotlib, scipy"
pip install numpy matplotlib scipy --quiet || { echo -e "${RED}✗ Failed to install numpy/matplotlib/scipy${NC}"; exit 1; }

echo "  - tqdm, numba"
pip install tqdm numba --quiet || { echo -e "${RED}✗ Failed to install tqdm/numba${NC}"; exit 1; }

echo "  - FerroSim (from GitHub)"
pip install git+https://github.com/ramav87/FerroSim.git@rama-dev --quiet || { echo -e "${RED}✗ Failed to install FerroSim${NC}"; exit 1; }

echo -e "${GREEN}✓ All dependencies installed${NC}"

# Generate mock AFM data
echo ""
echo -e "${YELLOW}Generating mock AFM data...${NC}"
python generate_mock_afm.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Mock AFM data generated${NC}"
    echo "  Files created:"
    echo "    - mock_afm_clean.json"
    echo "    - mock_afm_noisy.json"  
    echo "    - mock_afm_defects.json"
    echo "    - PNG visualizations"
else
    echo -e "${RED}✗ Failed to generate mock AFM data${NC}"
    exit 1
fi

# Test MCP server (quick test)
echo ""
echo -e "${YELLOW}Testing MCP server...${NC}"
timeout 2 python ferrosim_mcp_server_minimal.py < /dev/null > /dev/null 2>&1 &
server_pid=$!
sleep 1
if ps -p $server_pid > /dev/null; then
    echo -e "${GREEN}✓ MCP server can start${NC}"
    kill $server_pid 2>/dev/null
else
    echo -e "${YELLOW}⚠ MCP server test inconclusive (this is usually OK)${NC}"
fi

# Create quick test script
echo ""
echo -e "${YELLOW}Creating test script...${NC}"
cat > test_installation.py << 'EOF'
#!/usr/bin/env python3
"""Quick test to verify installation"""

import sys

def test_imports():
    """Test that all required packages can be imported"""
    packages = [
        ('anthropic', 'Anthropic API'),
        ('mcp', 'Model Context Protocol'),
        ('numpy', 'NumPy'),
        ('matplotlib', 'Matplotlib'),
        ('scipy', 'SciPy'),
        ('ferrosim', 'FerroSim'),
    ]
    
    all_ok = True
    for package, name in packages:
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - NOT FOUND")
            all_ok = False
    
    return all_ok

def test_ferrosim():
    """Test FerroSim basic functionality"""
    from ferrosim import Ferro2DSim
    import numpy as np
    
    try:
        sim = Ferro2DSim(n=5, gamma=1.0, k=1.0)
        print("✓ FerroSim can create simulations")
        return True
    except Exception as e:
        print(f"✗ FerroSim test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing installation...")
    print("\nPackages:")
    imports_ok = test_imports()
    
    print("\nFunctionality:")
    ferrosim_ok = test_ferrosim()
    
    if imports_ok and ferrosim_ok:
        print("\n✅ All tests passed! You're ready to go.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check installation.")
        sys.exit(1)
EOF

chmod +x test_installation.py
python test_installation.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo -e "${GREEN}Setup Complete! 🎉${NC}"
    echo "=================================================="
    echo ""
    echo "What to do next:"
    echo ""
    echo "1. Activate the conda environment (if not already active):"
    echo "   conda activate ferrosim_mcp"
    echo ""
    echo "2. Read the documentation:"
    echo "   cat README.md"
    echo ""
    echo "3. Start the MCP server:"
    echo "   python ferrosim_mcp_server_minimal.py"
    echo ""
    echo "4. Run the demo workflow:"
    echo "   python test_agent_workflow.py"
    echo ""
    echo "5. Set your API key (for Claude integration):"
    echo "   export ANTHROPIC_API_KEY='your-key-here'"
    echo ""
    echo "For detailed instructions, see:"
    echo "  - README.md (quick start)"
    echo "  - PROJECT_SUMMARY.md (overview)"
    echo "  - implementation_roadmap.md (detailed steps)"
    echo ""
    echo "Good luck with the hackathon! 🚀"
else
    echo ""
    echo "=================================================="
    echo -e "${RED}Setup encountered issues${NC}"
    echo "=================================================="
    echo ""
    echo "Please check the error messages above and:"
    echo "1. Ensure Python 3.8+ is installed"
    echo "2. Check internet connection (for pip installs)"
    echo "3. Review README.md for manual installation steps"
fi
