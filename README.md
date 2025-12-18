# FerroSim MCP Server - Quick Start Guide

## 🎯 Hackathon Goal

Build an **agentic AI system** that performs **theory-experiment matching** by:
1. Creating an MCP server that exposes FerroSim simulation capabilities
2. Using Claude agents to control simulations through the MCP interface
3. Comparing simulation results with AFM "experimental" data
4. Iteratively optimizing parameters to achieve best fit

## 📁 Project Files

### Core Implementation
- `ferrosim_mcp_server_minimal.py` - Minimal working MCP server (START HERE!)
- `generate_mock_afm.py` - Creates synthetic AFM data for testing
- `test_agent_workflow.py` - Demonstrates agent workflows

### Documentation
- `ferrosim_mcp_design.md` - Full architecture design
- `implementation_roadmap.md` - Detailed implementation steps

## ⚡ Quick Start (30 minutes)

### Step 1: Install Dependencies (5 min)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install anthropic mcp numpy matplotlib scipy tqdm numba

# Install FerroSim
pip install git+https://github.com/ramav87/FerroSim.git@rama-dev
```

### Step 2: Generate Mock AFM Data (2 min)

```bash
python generate_mock_afm.py
```

This creates:
- `mock_afm_clean.json` - Clean domain structure
- `mock_afm_noisy.json` - Noisy measurement
- `mock_afm_defects.json` - Data with defects
- PNG visualizations of each

### Step 3: Test the MCP Server (5 min)

```bash
# Terminal 1: Start MCP server
python ferrosim_mcp_server_minimal.py
```

The server will wait for input on stdin. You can test it with a simple JSON-RPC request:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

### Step 4: Test Agent Workflow (5 min)

```bash
# Terminal 2: Run workflow simulation
python test_agent_workflow.py
```

This demonstrates how agents would use the MCP server.

### Step 5: Connect Claude API (10 min)

Create `test_with_claude.py`:

```python
import anthropic
import json
import subprocess
import os

# Start MCP server as subprocess
server_process = subprocess.Popen(
    ['python', 'ferrosim_mcp_server_minimal.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Load mock AFM data
with open('mock_afm_clean.json', 'r') as f:
    afm_data = json.load(f)

amplitude_flat = [item for row in afm_data['amplitude'] for item in row]

# Initialize Claude
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Configure MCP tools
mcp_tools = [
    # ... tool definitions from ferrosim_mcp_server_minimal.py
]

# Ask Claude to fit parameters
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4000,
    tools=mcp_tools,
    messages=[{
        "role": "user",
        "content": f"""I have AFM data from a ferroelectric sample. 
        Find simulation parameters (k, dep_alpha) that match this data.
        
        AFM amplitude (20x20, flattened): {amplitude_flat}
        
        Use tetragonal mode. Target correlation > 0.90."""
    }]
)

print(response.content)
```

Run:
```bash
export ANTHROPIC_API_KEY="your-key-here"
python test_with_claude.py
```

## 🎨 What Each File Does

### `ferrosim_mcp_server_minimal.py`
**Purpose**: MCP server that wraps FerroSim

**Key functions**:
- `SimulationManager`: Manages simulation instances with unique IDs
- `initialize_simulation`: Creates new simulation with parameters
- `run_simulation`: Executes the simulation
- `get_simulation_results`: Retrieves polarization data
- `compare_with_afm_data`: Calculates similarity metrics

**MCP Tools exposed**:
1. ✅ `initialize_simulation` - Create sim with parameters
2. ✅ `run_simulation` - Execute simulation
3. ✅ `get_simulation_results` - Get Px, Py data
4. ✅ `compare_with_afm_data` - Compare with AFM
5. ✅ `list_simulations` - See all active sims

### `generate_mock_afm.py`
**Purpose**: Creates synthetic "experimental" data

**How it works**:
1. Runs FerroSim with **known parameters**
2. Extracts final polarization state
3. Converts to AFM-like signals (amplitude, phase)
4. Adds realistic noise and artifacts
5. Saves as JSON with metadata

**Why it's needed**: Real AFM digital twin not available yet, so we create synthetic data that behaves like real measurements.

### `test_agent_workflow.py`
**Purpose**: Demonstrates agent-based optimization

**Workflows shown**:
1. **Parameter Fitting**: Agent iteratively adjusts k, dep_alpha to improve fit
2. **Defect Discovery**: Agent identifies defect locations from anomalies
3. **Multi-Objective**: Agent balances multiple fitness criteria

## 🧪 Theory-Experiment Matching Process

```
┌─────────────────┐
│   AFM Data      │ "Experiment"
│   (target)      │
└────────┬────────┘
         │
         │ 1. Agent observes mismatch
         │
         ▼
┌─────────────────┐
│  Claude Agent   │
│  (via MCP)      │◄──── 4. Iterate
└────────┬────────┘
         │
         │ 2. Adjust parameters
         │
         ▼
┌─────────────────┐
│  FerroSim       │ "Theory"
│  Simulation     │
└────────┬────────┘
         │
         │ 3. Compare results
         │
         ▼
┌─────────────────┐
│  Similarity     │
│  Score          │
└─────────────────┘
```

## 📊 Example Agent Conversation

**Human**: "I have AFM data. Find parameters that match it."

**Claude**: "I'll help you fit the simulation parameters. Let me start with reasonable values for a tetragonal ferroelectric."

*→ Calls `initialize_simulation(n=20, k=1.0, dep_alpha=0.05, mode='tetragonal')`*
*← Gets `sim_id='abc123'`*

**Claude**: "Running simulation with initial parameters..."

*→ Calls `run_simulation(sim_id='abc123')`*
*← Gets results*

**Claude**: "Comparing with your AFM data..."

*→ Calls `compare_with_afm_data(sim_id='abc123', afm_data=[...])`*
*← Gets `correlation=0.72`*

**Claude**: "Correlation is 0.72. Let me try increasing the coupling constant..."

*→ Calls `initialize_simulation(n=20, k=1.5, dep_alpha=0.1, mode='tetragonal')`*
*→ Calls `run_simulation(sim_id='def456')`*
*→ Calls `compare_with_afm_data(sim_id='def456', afm_data=[...])`*
*← Gets `correlation=0.94`*

**Claude**: "Excellent! I found parameters that match your data with 94% correlation: k=1.5, dep_alpha=0.1"

## 🔧 Troubleshooting

### Problem: MCP server not starting
```bash
# Check if FerroSim is installed
python -c "import ferrosim; print('OK')"

# Check if MCP is installed
python -c "import mcp; print('OK')"
```

### Problem: Simulations are slow
```python
# In ferrosim_mcp_server_minimal.py, reduce timesteps:
time_vec = np.linspace(0, 1.0, 200)  # Instead of 1000
```

### Problem: Poor convergence
- Increase gamma (makes simulation more stable but slower)
- Reduce time step (dt)
- Check parameter bounds are reasonable

### Problem: Agent not using tools correctly
- Ensure tool schemas match server implementation
- Add more descriptive tool descriptions
- Provide example usage in prompt

## 🚀 Next Steps

### For Hackathon MVP (4-6 hours)
1. ✅ Get basic MCP server running
2. ✅ Generate mock AFM data
3. ✅ Test parameter fitting with Claude
4. 🔄 Add visualization of results
5. 🔄 Prepare demo notebook
6. 🔄 Create presentation

### Full Implementation (10-15 hours)
1. Add more analysis tools (domain statistics, curl)
2. Implement parameter optimization algorithms
3. Add support for defects and custom fields
4. Create interactive visualizations
5. Integrate with real AFM digital twin (when available)
6. Add batch processing for multiple datasets

### Advanced Features
- **Bayesian Optimization**: Use GPyOpt for smarter parameter search
- **Multi-fidelity**: Use cheap low-res sims to guide expensive high-res
- **Active Learning**: Agent decides which experiments to run next
- **Uncertainty Quantification**: Report confidence in parameter estimates

## 📚 Key Concepts

### What is MCP?
**Model Context Protocol** - Standard way for LLMs to interact with external tools and data sources. Like an API, but designed for AI agents.

### What is FerroSim?
Simulation tool for ferroelectric materials based on Landau-Khalatnikov equations. Models polarization dynamics in 2D lattice with:
- Double-well potential (bistable states)
- Nearest-neighbor coupling
- Applied electric fields
- Defects and disorder

### What is Theory-Experiment Matching?
Finding simulation parameters that make theoretical predictions match experimental observations. Classic inverse problem in materials science.

## 🎓 Understanding the Physics

### Ferroelectric Materials
- Have spontaneous polarization (P)
- Polarization can be switched by electric field
- Form domains (regions of uniform P)
- Show hysteresis (memory effect)

### AFM Piezoresponse
- Measures local polarization response
- Amplitude ∝ |P| (magnitude)
- Phase ∝ direction of P
- Can map domains at nanoscale

### Simulation Parameters
- **k**: Coupling between neighbors (higher = more uniform)
- **dep_alpha**: Depolarization field (higher = smaller domains)
- **gamma**: Domain wall mobility (kinetic factor)
- **mode**: Crystal structure (tetragonal, rhombohedral)

## 📈 Success Metrics

For hackathon demo, you should achieve:
- ✅ MCP server runs without errors
- ✅ Agent successfully calls all tools
- ✅ Parameter fitting reaches >0.90 correlation
- ✅ Process completes in <5 iterations
- ✅ Results visualized clearly

## 🤝 Resources

- **FerroSim Notebook**: https://colab.research.google.com/drive/1yR698-_qoAKoiK6VRVbU5UFJUkV5tS_l
- **MCP Documentation**: https://modelcontextprotocol.io
- **Anthropic API**: https://docs.anthropic.com
- **FerroSim Repo**: https://github.com/ramav87/FerroSim

## 💡 Tips for Success

1. **Start simple**: Get basic MCP server working first
2. **Test incrementally**: Verify each tool works before adding more
3. **Use good prompts**: Guide Claude with clear objectives
4. **Visualize results**: Show before/after comparisons
5. **Document everything**: Explain what each parameter does
6. **Handle errors**: Simulations can fail, catch gracefully
7. **Optimize later**: Focus on functionality first, then speed

## ❓ FAQ

**Q: Do I need real AFM data?**
A: No! Use the mock data generator for testing.

**Q: How long should simulations take?**
A: 1-5 seconds for n=20, 1000 timesteps on modern laptop.

**Q: What if parameters don't converge?**
A: Add bounds checking, try smaller step sizes, or use optimization library.

**Q: Can I use other LLMs?**
A: Yes, but MCP is designed for Claude. You'd need to adapt the interface.

**Q: What about the AFM digital twin mentioned?**
A: Not provided yet. Use mock data as placeholder.

## 🎉 Good Luck!

You have everything you need to build a working demo:
- ✅ MCP server code
- ✅ Mock AFM data generator
- ✅ Test workflows
- ✅ Documentation

**Your mission**: Connect these pieces and show autonomous agent-driven theory-experiment matching!

Questions? Check the detailed docs:
- `ferrosim_mcp_design.md` - Architecture
- `implementation_roadmap.md` - Step-by-step guide
