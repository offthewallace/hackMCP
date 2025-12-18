# FerroSim MCP Server Design

## Overview
MCP server to expose FerroSim simulation capabilities for agentic AI workflows performing theory-experiment matching with AFM digital twin data.

## MCP Server Tools

### 1. Simulation Control Tools

#### `initialize_simulation`
**Purpose**: Create a new simulation instance with specified parameters
**Parameters**:
- `n` (int): Lattice size (default: 10)
- `gamma` (float): Kinetic coefficient/domain wall mobility (default: 1.0)
- `k` (float): Coupling constant for nearest neighbors (default: 1.0)
- `mode` (string): Material mode - 'tetragonal', 'rhombohedral', 'uniaxial', 'squareelectric'
- `time_vec` (array): Time vector for simulation
- `applied_field` (array): Applied electric field [Ex, Ey] over time
- `defects` (list): Random field defects at each site [(RFx, RFy), ...]
- `landau_params` (dict): Landau coefficients {alpha1, alpha2, alpha3}
- `dep_alpha` (float): Depolarization constant (default: 0.0)
- `initial_condition` (string): 'pr' (remnant) or 'random'

**Returns**: Simulation ID for subsequent operations

#### `run_simulation`
**Purpose**: Execute the simulation
**Parameters**:
- `sim_id` (string): Simulation instance ID
- `verbose` (bool): Show progress (default: True)

**Returns**: 
- Total polarization [Px, Py] vs time
- dP/dt vs time
- Success status

#### `get_simulation_results`
**Purpose**: Retrieve simulation results
**Parameters**:
- `sim_id` (string): Simulation instance ID
- `timestep` (int, optional): Specific timestep (None for all)

**Returns**:
- Polarization matrix [2, time, N, N]
- Total polarization time series
- Field time series

### 2. Analysis Tools

#### `calculate_hysteresis`
**Purpose**: Extract hysteresis loop from simulation
**Parameters**:
- `sim_id` (string): Simulation instance ID
- `component` (string): 'x' or 'y' component

**Returns**:
- Field values
- Polarization values
- Coercive field
- Remnant polarization

#### `calculate_domain_statistics`
**Purpose**: Analyze domain structure at specific time
**Parameters**:
- `sim_id` (string): Simulation instance ID
- `timestep` (int): Time step to analyze

**Returns**:
- Average domain size
- Number of domains
- Domain wall density
- Polarization magnitude map
- Polarization angle map

#### `calculate_curl`
**Purpose**: Calculate curl of polarization field (topological features)
**Parameters**:
- `sim_id` (string): Simulation instance ID
- `timestep` (int): Time step to analyze

**Returns**:
- Curl field map
- Max/min curl values
- Topological charge density

### 3. Comparison Tools (for Theory-Experiment Matching)

#### `compare_with_afm_data`
**Purpose**: Compare simulation results with AFM data
**Parameters**:
- `sim_id` (string): Simulation instance ID
- `afm_data` (array): AFM measurement data
- `metric` (string): 'mse', 'correlation', 'structural_similarity'
- `timestep` (int, optional): Which sim timestep to compare

**Returns**:
- Similarity score
- Residual map
- Best matching timestep (if not specified)

#### `optimize_parameters`
**Purpose**: Suggest parameter adjustments to improve fit
**Parameters**:
- `sim_id` (string): Current simulation ID
- `afm_data` (array): Target AFM data
- `parameters_to_optimize` (list): ['k', 'defects', 'field_strength', etc.]

**Returns**:
- Suggested parameter values
- Expected improvement score
- Optimization confidence

### 4. Visualization Tools

#### `generate_polarization_map`
**Purpose**: Create visualization of polarization field
**Parameters**:
- `sim_id` (string): Simulation instance ID
- `timestep` (int): Time step to visualize
- `style` (string): 'quiver', 'magnitude', 'angle', 'combined'

**Returns**: 
- Image data (base64 or file path)
- Metadata (colorbar ranges, etc.)

#### `generate_comparison_plot`
**Purpose**: Create side-by-side comparison of sim vs AFM
**Parameters**:
- `sim_id` (string): Simulation instance ID
- `afm_data` (array): AFM data to compare
- `timestep` (int): Simulation timestep

**Returns**: 
- Comparison image (base64 or file path)
- Difference map

### 5. State Management Tools

#### `list_simulations`
**Purpose**: List all active simulation instances
**Returns**: List of simulation IDs with their parameters

#### `delete_simulation`
**Purpose**: Clean up a simulation instance
**Parameters**:
- `sim_id` (string): Simulation to delete

#### `save_simulation`
**Purpose**: Serialize simulation state for later use
**Parameters**:
- `sim_id` (string): Simulation to save
- `filepath` (string): Where to save

#### `load_simulation`
**Purpose**: Restore a saved simulation
**Parameters**:
- `filepath` (string): Saved simulation file

**Returns**: New simulation ID

## Resources (Read-only data)

### `simulation_templates`
**Purpose**: Pre-configured simulation setups
**Examples**:
- `pristine_tetragonal`: Clean tetragonal material
- `defect_study`: Material with varying defect densities
- `domain_wall_180`: 180° domain wall configuration
- `hysteresis_standard`: Standard hysteresis measurement setup

### `material_parameters`
**Purpose**: Common material parameter sets
**Examples**:
- PZT (Lead Zirconate Titanate)
- BTO (Barium Titanate)  
- LiNbO3 (Lithium Niobate)

## Implementation Notes

### Server Structure
```
ferrosim-mcp-server/
├── server.py              # Main MCP server
├── simulation_manager.py  # Manages simulation instances
├── analysis.py           # Analysis functions
├── comparison.py         # Theory-experiment matching
└── ferrosim/            # FerroSim library
```

### Key Design Decisions

1. **Stateful Simulations**: Each simulation gets a unique ID and is kept in memory during session
2. **Async Operations**: Long-running simulations should be async to not block agent
3. **Caching**: Cache results for common parameter sets
4. **Error Handling**: Validate parameters before running expensive simulations
5. **Units**: All inputs/outputs should have clear units documented

### AFM Digital Twin Interface

The server should expect AFM data in format:
```python
{
    "data": np.array([N, N]),  # Spatial map
    "metadata": {
        "scan_size": [x_size, y_size],  # nm
        "resolution": [nx, ny],
        "type": "amplitude" | "phase" | "piezoresponse",
        "timestamp": "...",
    }
}
```

## Agent Workflow Examples

### Workflow 1: Parameter Fitting
```
1. Agent receives AFM data from digital twin
2. Agent calls initialize_simulation with initial guess parameters
3. Agent calls run_simulation
4. Agent calls compare_with_afm_data to get similarity score
5. Agent calls optimize_parameters for suggestions
6. Agent iterates steps 2-5 until good fit achieved
7. Agent generates comparison plots
```

### Workflow 2: Defect Discovery
```
1. Agent observes unusual features in AFM data
2. Agent runs multiple simulations with different defect configurations
3. Agent uses compare_with_afm_data to find best match
4. Agent reports discovered defect pattern
```

### Workflow 3: Domain Dynamics
```
1. Agent receives time-series AFM data
2. Agent initializes simulation with matching initial state
3. Agent runs simulation with time-varying field
4. Agent compares temporal evolution
5. Agent extracts domain wall velocity, pinning sites
```
