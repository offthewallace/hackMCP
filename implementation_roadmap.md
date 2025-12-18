# FerroSim MCP Server Implementation Roadmap

## Step-by-Step Implementation Guide

### Prerequisites
```bash
# Install required packages
pip install mcp anthropic numpy matplotlib scipy
pip install git+https://github.com/ramav87/FerroSim.git@rama-dev
```

---

## STEP 1: Set Up Project Structure (30 minutes)

Create this directory structure:
```
ferrosim-mcp-project/
├── ferrosim_mcp_server/
│   ├── __init__.py
│   ├── server.py              # Main MCP server
│   ├── simulation_manager.py  # Handles simulation lifecycle
│   ├── analysis.py            # Analysis tools
│   └── comparison.py          # Theory-experiment matching
├── tests/
│   └── test_server.py
├── examples/
│   ├── mock_afm_data.py       # Generate synthetic AFM data for testing
│   └── agent_workflow.py      # Example agent workflows
├── pyproject.toml
└── README.md
```

**Action Items:**
- [ ] Create directory structure
- [ ] Set up Git repository
- [ ] Create virtual environment

---

## STEP 2: Implement Simulation Manager (1-2 hours)

**File: `simulation_manager.py`**

This manages simulation instances and their lifecycle.

Key classes:
- `SimulationInstance`: Wrapper around Ferro2DSim with metadata
- `SimulationManager`: Manages multiple simulation instances

**Core functionality needed:**
```python
class SimulationManager:
    def create_simulation(self, params: dict) -> str:
        """Create new simulation, return unique ID"""
        pass
    
    def get_simulation(self, sim_id: str) -> SimulationInstance:
        """Retrieve simulation by ID"""
        pass
    
    def run_simulation(self, sim_id: str, **kwargs) -> dict:
        """Execute simulation and return results"""
        pass
    
    def delete_simulation(self, sim_id: str):
        """Clean up simulation"""
        pass
```

**Action Items:**
- [ ] Implement SimulationInstance class
- [ ] Implement SimulationManager with CRUD operations
- [ ] Add validation for simulation parameters
- [ ] Add error handling

---

## STEP 3: Implement Analysis Tools (1-2 hours)

**File: `analysis.py`**

Provides analysis functions for simulation results.

**Key functions needed:**
```python
def extract_hysteresis(sim_results: dict, component: str) -> dict:
    """Extract hysteresis loop data"""
    pass

def analyze_domain_structure(pmat: np.ndarray, timestep: int) -> dict:
    """Analyze domain statistics"""
    pass

def calculate_polarization_curl(pmat: np.ndarray, timestep: int) -> np.ndarray:
    """Calculate curl of polarization field"""
    pass

def compute_spatial_statistics(data: np.ndarray) -> dict:
    """Compute spatial correlation, domain sizes, etc."""
    pass
```

**Action Items:**
- [ ] Implement hysteresis extraction
- [ ] Implement domain analysis (using image segmentation)
- [ ] Implement curl calculation
- [ ] Add visualization functions

---

## STEP 4: Implement Comparison Tools (2-3 hours)

**File: `comparison.py`**

Core functions for theory-experiment matching.

**Key functions needed:**
```python
def compare_polarization_maps(
    sim_data: np.ndarray, 
    afm_data: np.ndarray,
    metric: str = 'mse'
) -> dict:
    """Compare simulation with AFM data"""
    pass

def compute_similarity_metrics(sim_data, afm_data) -> dict:
    """Multiple similarity metrics"""
    # MSE, correlation, SSIM, etc.
    pass

def suggest_parameter_adjustments(
    current_params: dict,
    sim_data: np.ndarray,
    afm_data: np.ndarray
) -> dict:
    """Use gradient-based or heuristic methods to suggest improvements"""
    pass

def align_and_register(sim_data, afm_data):
    """Handle scale/rotation differences"""
    pass
```

**Action Items:**
- [ ] Implement MSE, correlation, SSIM metrics
- [ ] Implement parameter optimization suggestions
- [ ] Add data preprocessing (normalization, alignment)
- [ ] Handle different data resolutions

---

## STEP 5: Build MCP Server (2-3 hours)

**File: `server.py`**

Main MCP server using Python SDK.

**Structure:**
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from .simulation_manager import SimulationManager
from .analysis import *
from .comparison import *

# Create MCP server instance
app = Server("ferrosim-mcp-server")

# Initialize simulation manager
sim_manager = SimulationManager()

# Define tools
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available tools"""
    return [
        types.Tool(
            name="initialize_simulation",
            description="Create new FerroSim simulation",
            inputSchema={
                "type": "object",
                "properties": {
                    "n": {"type": "integer", "description": "Lattice size"},
                    "gamma": {"type": "number", "description": "Kinetic coefficient"},
                    # ... more parameters
                },
                "required": ["n"]
            }
        ),
        # ... more tools
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    if name == "initialize_simulation":
        sim_id = sim_manager.create_simulation(arguments)
        return [types.TextContent(
            type="text",
            text=f"Created simulation {sim_id}"
        )]
    # ... handle other tools
```

**Action Items:**
- [ ] Set up MCP server boilerplate
- [ ] Implement all tool handlers from design doc
- [ ] Add input validation
- [ ] Implement resource providers (templates, materials)
- [ ] Add logging and error handling

---

## STEP 6: Create Mock AFM Data Generator (1 hour)

**File: `examples/mock_afm_data.py`**

Since you don't have real AFM digital twin yet, create synthetic data.

**Approach:**
```python
def generate_mock_afm_data(
    n: int = 20,
    pattern: str = 'domains',  # 'domains', 'vortex', 'defect'
    noise_level: float = 0.05
) -> dict:
    """
    Generate synthetic AFM-like data by:
    1. Running a FerroSim simulation
    2. Adding realistic noise
    3. Converting to AFM-like format
    """
    # Run reference simulation
    sim = Ferro2DSim(n=n, mode='tetragonal', ...)
    results = sim.runSim()
    pmat = sim.getPmat(timestep=-1)
    
    # Convert to AFM amplitude signal
    amplitude = np.sqrt(pmat[0]**2 + pmat[1]**2)
    phase = np.arctan2(pmat[1], pmat[0])
    
    # Add noise
    amplitude += noise_level * np.random.randn(*amplitude.shape)
    
    return {
        "amplitude": amplitude,
        "phase": phase,
        "metadata": {...}
    }
```

**Action Items:**
- [ ] Create multiple pattern generators
- [ ] Add realistic noise models
- [ ] Save as standard format for testing

---

## STEP 7: Implement Test Agent Workflow (2-3 hours)

**File: `examples/agent_workflow.py`**

Create example workflows showing how Claude agents use the MCP server.

**Example Workflow 1: Parameter Fitting**
```python
import anthropic
import json

client = anthropic.Anthropic()

# Generate target "experimental" data
target_afm_data = generate_mock_afm_data(
    n=20, 
    pattern='domains',
    noise_level=0.1
)

# Initial conversation with agent
messages = [
    {
        "role": "user",
        "content": f"""I have AFM piezoresponse data from a ferroelectric sample.
        The data shows domain patterns. I need you to:
        1. Set up a FerroSim simulation
        2. Run it with reasonable initial parameters
        3. Compare with my AFM data
        4. Iterate to find best-fit parameters
        
        AFM data shape: {target_afm_data['amplitude'].shape}
        Initial parameters to try: tetragonal mode, n=20, k=1.0
        """
    }
]

# Let Claude agent work with MCP server
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4000,
    tools=[...],  # MCP tools from server
    messages=messages
)

# Agent will:
# 1. Call initialize_simulation
# 2. Call run_simulation  
# 3. Call compare_with_afm_data
# 4. Call optimize_parameters
# 5. Iterate until good fit
```

**Example Workflow 2: Defect Detection**
```python
# Agent discovers defect locations by:
# 1. Observing mismatch regions
# 2. Adding defects at those locations
# 3. Re-simulating
# 4. Validating improvement
```

**Action Items:**
- [ ] Implement end-to-end parameter fitting workflow
- [ ] Implement defect discovery workflow
- [ ] Add visualization of agent's progress
- [ ] Document best practices

---

## STEP 8: Testing and Validation (1-2 hours)

**File: `tests/test_server.py`**

**Test cases needed:**
- [ ] Simulation creation and management
- [ ] All tool functions work correctly
- [ ] Comparison metrics are accurate
- [ ] Parameter optimization converges
- [ ] Error handling works
- [ ] Agent workflows complete successfully

---

## STEP 9: Documentation and Polish (1 hour)

**Action Items:**
- [ ] Write comprehensive README
- [ ] Add docstrings to all functions
- [ ] Create usage examples
- [ ] Add troubleshooting guide
- [ ] Prepare demo for hackathon presentation

---

## Timeline Estimate

**Minimum Viable Product (MVP):** 8-10 hours
- Basic MCP server with core tools
- Simple comparison metrics
- One working agent workflow

**Full Implementation:** 12-15 hours
- All tools from design doc
- Multiple comparison metrics
- Parameter optimization
- Multiple agent workflows
- Comprehensive testing

**Hackathon Recommendation:**
Focus on MVP first, then add features if time permits.

---

## Critical Success Factors

1. **Get MCP server running early** - Test with simple tools first
2. **Mock AFM data quality** - Make it realistic enough for meaningful comparison
3. **Agent prompt engineering** - Guide Claude to use tools effectively
4. **Visualization** - Show comparisons clearly for demo
5. **Error handling** - Simulations can be unstable, handle gracefully

---

## Resources and References

- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **MCP Spec**: https://spec.modelcontextprotocol.io/
- **FerroSim**: https://github.com/ramav87/FerroSim
- **Image comparison metrics**: scikit-image (SSIM, MSE)
- **Optimization**: scipy.optimize for parameter fitting

---

## Next Steps for Wallace

1. **TODAY**: 
   - Set up project structure
   - Get basic MCP server running with 1-2 tools
   - Test with Claude API

2. **TOMORROW**:
   - Implement core comparison tools
   - Create mock AFM data
   - Build first agent workflow

3. **DAY 3**:
   - Add more analysis tools
   - Test agent workflows
   - Create demo visualizations

4. **DAY 4**:
   - Polish and debug
   - Prepare presentation
   - Document results
