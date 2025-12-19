#!/usr/bin/env python3
"""
Minimal FerroSim MCP Server - Quick Start Template
Run this to test basic MCP server functionality
"""

import os
import asyncio
import json
import sys
import uuid
import warnings
from typing import Dict, Any
import numpy as np

# Set environment variables before importing numba/scipy
os.environ['NUMBA_DISABLE_JIT'] = '0'  # Keep JIT enabled but controlled
os.environ['NUMBA_NUM_THREADS'] = '1'  # Single thread to avoid semaphore issues
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

# Suppress warnings that could interfere with JSON-RPC
warnings.filterwarnings('ignore')

# Import MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    import mcp.types as types
except ImportError:
    print("Install MCP SDK: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Import FerroSim
try:
    from ferrosim import Ferro2DSim
except ImportError:
    print("Install FerroSim: pip install git+https://github.com/ramav87/FerroSim.git@rama-dev", 
          file=sys.stderr)
    sys.exit(1)

# ============================================================================
# Helper Functions
# ============================================================================

def safe_serialize(obj):
    """Convert numpy arrays to JSON-safe lists, handling NaN/Inf"""
    if isinstance(obj, np.ndarray):
        # Replace NaN and Inf with None for JSON safety
        obj = np.nan_to_num(obj, nan=0.0, posinf=1e10, neginf=-1e10)
        return obj.tolist()
    return obj

# ============================================================================
# Electric Field Generation
# ============================================================================

def generate_electric_field(field_type: str, time_vec: np.ndarray, params: dict) -> np.ndarray:
    """
    Generate custom electric field waveforms
    
    Args:
        field_type: 'sine', 'step', 'polynomial', 'custom'
        time_vec: Time vector
        params: Parameters specific to field type
        
    Returns:
        applied_field: (timesteps, 2) array with Ex and Ey components
    """
    n_steps = len(time_vec)
    applied_field = np.zeros((n_steps, 2))
    
    if field_type == 'sine':
        # Sinusoidal field: Ex = Ax*sin(2π*fx*t), Ey = Ay*sin(2π*fy*t + phase)
        Ax = params.get('amplitude_x', 0.0)
        Ay = params.get('amplitude_y', 10.0)
        fx = params.get('freq_x', 1.0)
        fy = params.get('freq_y', 1.0)
        phase = params.get('phase', 0.0)
        
        applied_field[:, 0] = Ax * np.sin(2 * np.pi * fx * time_vec)
        applied_field[:, 1] = Ay * np.sin(2 * np.pi * fy * time_vec + phase)
        
    elif field_type == 'step':
        # Step function: field applied for first fraction of time, then removed
        Ex = params.get('Ex', 0.0)
        Ey = params.get('Ey', 0.5)
        step_fraction = params.get('step_fraction', 0.25)
        
        step_idx = int(n_steps * step_fraction)
        applied_field[:step_idx, 0] = Ex
        applied_field[:step_idx, 1] = Ey
        
    elif field_type == 'polynomial':
        # Polynomial modulated: A*(t+offset)^power * sin(2πf*t)
        Ax = params.get('amplitude_x', 180.0)
        Ay = params.get('amplitude_y', 180.0)
        fx = params.get('freq_x', 2.0)
        fy = params.get('freq_y', 2.0)
        power = params.get('power', 2.0)
        offset = params.get('offset', 0.5)
        
        time_mod = (time_vec + offset) ** power
        applied_field[:, 0] = Ax * time_mod * np.sin(2 * np.pi * fx * time_vec)
        applied_field[:, 1] = Ay * time_mod * np.cos(4 * np.pi * fy * time_vec)
        
    elif field_type == 'zero':
        # Zero field (for ground state relaxation)
        pass  # Already zeros
        
    else:
        raise ValueError(f"Unknown field type: {field_type}")
    
    return applied_field

# ============================================================================
# Defect Generation
# ============================================================================

def generate_defects(defect_type: str, n: int, params: dict) -> list:
    """
    Generate defect configurations
    
    Args:
        defect_type: 'none', 'random', 'periodic', 'custom'
        n: Lattice size
        params: Parameters specific to defect type
        
    Returns:
        defect_list: List of (Ex, Ey) tuples for each site
    """
    n_sites = n * n
    
    if defect_type == 'none':
        # No defects
        return [(0.0, 0.0) for _ in range(n_sites)]
        
    elif defect_type == 'random':
        # Random defects at random locations
        num_defects = params.get('num_defects', 5)
        strength_mean = params.get('strength_mean', 15.0)
        strength_std = params.get('strength_std', 0.5)
        
        np.random.seed(params.get('seed', None))
        defect_list = [(0.01, 0.01) for _ in range(n_sites)]
        
        # Randomly place defects
        defect_indices = np.random.choice(n_sites, size=num_defects, replace=False)
        for idx in defect_indices:
            angle = np.random.rand() * 2 * np.pi
            strength = np.random.normal(strength_mean, strength_std)
            Ex = strength * np.cos(angle)
            Ey = strength * np.sin(angle)
            defect_list[idx] = (Ex, Ey)
            
        return defect_list
        
    elif defect_type == 'periodic':
        # Periodic defects on a grid
        row_spacing = params.get('row_spacing', 5)
        col_spacing = params.get('col_spacing', 10)
        strength_mean = params.get('strength_mean', 15.5)
        strength_std = params.get('strength_std', 0.5)
        
        np.random.seed(params.get('seed', 42))
        defect_list = []
        
        for row in range(n):
            for col in range(n):
                Efx = 0.01
                Efy = 0.01
                
                # Place defects at periodic locations
                if row % row_spacing == 0 and col % col_spacing == 0:
                    Efy = np.random.normal(strength_mean, strength_std)
                    
                defect_list.append((Efx, Efy))
                
        return defect_list
        
    else:
        raise ValueError(f"Unknown defect type: {defect_type}")

# ============================================================================
# Visualization Generation
# ============================================================================

def generate_visualization(sim: Ferro2DSim, viz_type: str, timestep: int = -1) -> str:
    """
    Generate visualization and return as base64-encoded PNG
    
    Args:
        sim: FerroSim simulation object
        viz_type: 'summary', 'quiver', 'magnitude_angle'
        timestep: Which timestep to visualize (-1 for last)
        
    Returns:
        base64_image: Base64-encoded PNG image
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import io
    import base64
    
    # Create figure based on visualization type
    if viz_type == 'summary':
        fig = sim.plot_summary()
        
    elif viz_type == 'quiver':
        fig = sim.plot_quiver(time_step=timestep)
        
    elif viz_type == 'magnitude_angle':
        fig, _, _ = sim.plot_mag_ang(time_step=timestep)
        
    else:
        raise ValueError(f"Unknown visualization type: {viz_type}")
    
    # Convert to base64-encoded PNG
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    
    return img_base64

# ============================================================================
# Simulation Manager - Minimal Implementation
# ============================================================================

class SimulationManager:
    """Manages active simulations"""
    
    def __init__(self):
        self.simulations: Dict[str, Dict[str, Any]] = {}
    
    def create_simulation(self, params: dict) -> str:
        """Create new simulation instance with advanced options"""
        sim_id = str(uuid.uuid4())[:8]
        
        # Extract basic parameters with defaults
        n = params.get('n', 10)
        gamma = params.get('gamma', 1.0)
        k = params.get('k', 1.0)
        mode = params.get('mode', 'tetragonal')
        dep_alpha = params.get('dep_alpha', 0.0)
        init_mode = params.get('init', 'pr')  # 'pr', 'random', 'up', 'down'
        
        # Create time vector
        if 'time_vec' in params:
            time_vec = np.array(params['time_vec'])
        else:
            t_start = params.get('t_start', 0.0)
            t_end = params.get('t_end', 1.0)
            n_steps = params.get('n_steps', 1000)
            time_vec = np.linspace(t_start, t_end, n_steps)
        
        # Generate electric field
        field_config = params.get('field_config', {})
        if 'applied_field' in params:
            applied_field = np.array(params['applied_field'])
        elif field_config:
            field_type = field_config.get('type', 'sine')
            field_params = field_config.get('params', {})
            applied_field = generate_electric_field(field_type, time_vec, field_params)
        else:
            # Default: sine wave in y direction
            applied_field = np.zeros((len(time_vec), 2))
            applied_field[:, 1] = 10 * np.sin(time_vec * 2 * np.pi * 2)
        
        # Generate defects
        defect_config = params.get('defect_config', {})
        if 'defects' in params:
            defects = params['defects']
        elif defect_config:
            defect_type = defect_config.get('type', 'none')
            defect_params = defect_config.get('params', {})
            defects = generate_defects(defect_type, n, defect_params)
        else:
            defects = [(0, 0) for _ in range(n * n)]
        
        # Create simulation
        try:
            sim = Ferro2DSim(
                n=n,
                gamma=gamma,
                k=k,
                mode=mode,
                dep_alpha=dep_alpha,
                time_vec=time_vec,
                appliedE=applied_field,
                defects=defects,
                init=init_mode
            )
            
            self.simulations[sim_id] = {
                'sim': sim,
                'params': params,
                'results': None,
                'status': 'created'
            }
            
            return sim_id
            
        except Exception as e:
            raise ValueError(f"Failed to create simulation: {str(e)}")
    
    def run_simulation(self, sim_id: str, verbose: bool = False) -> dict:
        """Run simulation and store results"""
        if sim_id not in self.simulations:
            raise ValueError(f"Simulation {sim_id} not found")
        
        sim_data = self.simulations[sim_id]
        sim = sim_data['sim']
        
        try:
            # Redirect stdout to stderr temporarily to prevent progress bars
            # from interfering with JSON-RPC protocol
            import sys
            old_stdout = sys.stdout
            if verbose:
                sys.stdout = sys.stderr
            
            try:
                # Run simulation
                results = sim.runSim(calc_pr=False, verbose=verbose)
                sim_data['results'] = results
                sim_data['status'] = 'completed'
            finally:
                # Restore stdout
                sys.stdout = old_stdout
            
            # Get final polarization map
            pmat = sim.getPmat()  # Returns shape: (2, timesteps, n, n)
            pmat_final = pmat[:, -1, :, :]  # Get last timestep: (2, n, n)
            
            return {
                'sim_id': sim_id,
                'status': 'completed',
                'total_polarization': safe_serialize(results['Polarization']),
                'final_Px': safe_serialize(pmat_final[0, :, :]),
                'final_Py': safe_serialize(pmat_final[1, :, :])
            }
            
        except Exception as e:
            sim_data['status'] = 'failed'
            raise RuntimeError(f"Simulation failed: {str(e)}")
    
    def get_results(self, sim_id: str, timestep: int = -1) -> dict:
        """Get simulation results"""
        if sim_id not in self.simulations:
            raise ValueError(f"Simulation {sim_id} not found")
        
        sim_data = self.simulations[sim_id]
        if sim_data['status'] != 'completed':
            raise ValueError(f"Simulation not completed yet")
        
        sim = sim_data['sim']
        pmat = sim.getPmat()  # Returns shape: (2, timesteps, n, n)
        
        if timestep == -1:
            # Get last timestep
            pmat_result = pmat[:, -1, :, :]
            return {
                'sim_id': sim_id,
                'timestep': timestep,
                'Px': safe_serialize(pmat_result[0, :, :]),
                'Py': safe_serialize(pmat_result[1, :, :]),
            }
        else:
            # Get specific timestep
            pmat_result = pmat[:, timestep, :, :]
            return {
                'sim_id': sim_id,
                'timestep': timestep,
                'Px': safe_serialize(pmat_result[0, :, :]),
                'Py': safe_serialize(pmat_result[1, :, :]),
            }
    
    def list_simulations(self) -> list:
        """List all simulations"""
        return [
            {
                'sim_id': sim_id,
                'status': data['status'],
                'params': {k: v for k, v in data['params'].items() if k != 'time_vec' and k != 'applied_field'}
            }
            for sim_id, data in self.simulations.items()
        ]
    
    def visualize_simulation(self, sim_id: str, viz_type: str = 'summary', timestep: int = -1) -> str:
        """Generate visualization for a completed simulation"""
        if sim_id not in self.simulations:
            raise ValueError(f"Simulation {sim_id} not found")
        
        sim_data = self.simulations[sim_id]
        if sim_data['status'] != 'completed':
            raise ValueError(f"Simulation not completed yet")
        
        sim = sim_data['sim']
        return generate_visualization(sim, viz_type, timestep)

# ============================================================================
# Comparison Tools - Minimal Implementation
# ============================================================================

def compare_with_afm(sim_data: np.ndarray, afm_data: np.ndarray) -> dict:
    """Compare simulation with AFM data"""
    # Ensure same shape
    if sim_data.shape != afm_data.shape:
        raise ValueError(f"Shape mismatch: sim {sim_data.shape} vs AFM {afm_data.shape}")
    
    # Calculate metrics
    mse = np.mean((sim_data - afm_data) ** 2)
    correlation = np.corrcoef(sim_data.flatten(), afm_data.flatten())[0, 1]
    
    # Normalized RMSE
    rmse = np.sqrt(mse)
    nrmse = rmse / (np.max(afm_data) - np.min(afm_data))
    
    return {
        'mse': float(mse),
        'rmse': float(rmse),
        'nrmse': float(nrmse),
        'correlation': float(correlation),
        'similarity_score': float(correlation)  # Use correlation as main score
    }

# ============================================================================
# MCP Server Setup
# ============================================================================

# Initialize
app = Server("ferrosim-mcp-server")
sim_manager = SimulationManager()

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available MCP tools"""
    return [
        types.Tool(
            name="initialize_simulation",
            description="Create a new FerroSim simulation with basic or advanced parameters. Supports custom electric fields, defects, and ground state calculations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "Lattice size (NxN grid)",
                        "default": 10
                    },
                    "gamma": {
                        "type": "number",
                        "description": "Kinetic coefficient (domain wall mobility)",
                        "default": 1.0
                    },
                    "k": {
                        "type": "number",
                        "description": "Coupling constant for nearest neighbors",
                        "default": 1.0
                    },
                    "mode": {
                        "type": "string",
                        "description": "Material mode",
                        "enum": ["tetragonal", "rhombohedral", "uniaxial", "squareelectric"],
                        "default": "tetragonal"
                    },
                    "dep_alpha": {
                        "type": "number",
                        "description": "Depolarization constant",
                        "default": 0.0
                    },
                    "init": {
                        "type": "string",
                        "description": "Initial condition: 'pr' (positive remnant), 'random' (for ground states), 'up', 'down'",
                        "enum": ["pr", "random", "up", "down"],
                        "default": "pr"
                    },
                    "t_start": {
                        "type": "number",
                        "description": "Start time",
                        "default": 0.0
                    },
                    "t_end": {
                        "type": "number",
                        "description": "End time",
                        "default": 1.0
                    },
                    "n_steps": {
                        "type": "integer",
                        "description": "Number of time steps",
                        "default": 1000
                    },
                    "field_config": {
                        "type": "object",
                        "description": "Electric field configuration: {type: 'sine'|'step'|'polynomial'|'zero', params: {...}}",
                        "properties": {
                            "type": {"type": "string"},
                            "params": {"type": "object"}
                        }
                    },
                    "defect_config": {
                        "type": "object",
                        "description": "Defect configuration: {type: 'none'|'random'|'periodic', params: {...}}",
                        "properties": {
                            "type": {"type": "string"},
                            "params": {"type": "object"}
                        }
                    }
                },
                "required": []
            }
        ),
        
        types.Tool(
            name="run_simulation",
            description="Execute a simulation that was previously initialized",
            inputSchema={
                "type": "object",
                "properties": {
                    "sim_id": {
                        "type": "string",
                        "description": "Simulation ID returned from initialize_simulation"
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Show progress during simulation",
                        "default": False
                    }
                },
                "required": ["sim_id"]
            }
        ),
        
        types.Tool(
            name="get_simulation_results",
            description="Retrieve results from a completed simulation",
            inputSchema={
                "type": "object",
                "properties": {
                    "sim_id": {
                        "type": "string",
                        "description": "Simulation ID"
                    },
                    "timestep": {
                        "type": "integer",
                        "description": "Specific timestep to retrieve (-1 for final)",
                        "default": -1
                    }
                },
                "required": ["sim_id"]
            }
        ),
        
        types.Tool(
            name="compare_with_afm_data",
            description="Compare simulation results with AFM experimental data",
            inputSchema={
                "type": "object",
                "properties": {
                    "sim_id": {
                        "type": "string",
                        "description": "Simulation ID"
                    },
                    "afm_data": {
                        "type": "array",
                        "description": "AFM data as 2D array (flattened)",
                        "items": {"type": "number"}
                    },
                    "component": {
                        "type": "string",
                        "description": "Which polarization component to compare",
                        "enum": ["x", "y", "magnitude"],
                        "default": "magnitude"
                    }
                },
                "required": ["sim_id", "afm_data"]
            }
        ),
        
        types.Tool(
            name="list_simulations",
            description="List all active simulations",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        
        types.Tool(
            name="visualize_simulation",
            description="Generate visualization (plot) of a completed simulation. Returns base64-encoded PNG image.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sim_id": {
                        "type": "string",
                        "description": "Simulation ID"
                    },
                    "viz_type": {
                        "type": "string",
                        "description": "Visualization type: 'summary' (full evolution), 'quiver' (vector field), 'magnitude_angle' (polarization magnitude and angle)",
                        "enum": ["summary", "quiver", "magnitude_angle"],
                        "default": "summary"
                    },
                    "timestep": {
                        "type": "integer",
                        "description": "Timestep to visualize (-1 for final state)",
                        "default": -1
                    }
                },
                "required": ["sim_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls from Claude"""
    
    try:
        if name == "initialize_simulation":
            sim_id = sim_manager.create_simulation(arguments)
            result = {
                "success": True,
                "sim_id": sim_id,
                "message": f"Created simulation {sim_id} with parameters: {arguments}"
            }
            
        elif name == "run_simulation":
            result = sim_manager.run_simulation(
                arguments['sim_id'],
                verbose=arguments.get('verbose', False)
            )
            
        elif name == "get_simulation_results":
            result = sim_manager.get_results(
                arguments['sim_id'],
                timestep=arguments.get('timestep', -1)
            )
            
        elif name == "compare_with_afm_data":
            # Get simulation results
            sim_id = arguments['sim_id']
            sim_results = sim_manager.get_results(sim_id, timestep=-1)
            
            # Extract component
            component = arguments.get('component', 'magnitude')
            if component == 'x':
                sim_data = np.array(sim_results['Px'])
            elif component == 'y':
                sim_data = np.array(sim_results['Py'])
            else:  # magnitude
                px = np.array(sim_results['Px'])
                py = np.array(sim_results['Py'])
                sim_data = np.sqrt(px**2 + py**2)
            
            # Reshape AFM data
            afm_data = np.array(arguments['afm_data'])
            n = int(np.sqrt(len(afm_data)))
            afm_data = afm_data.reshape(n, n)
            
            # Compare
            comparison = compare_with_afm(sim_data, afm_data)
            result = {
                "sim_id": sim_id,
                "comparison": comparison
            }
            
        elif name == "list_simulations":
            result = {
                "simulations": sim_manager.list_simulations()
            }
            
        elif name == "visualize_simulation":
            viz_type = arguments.get('viz_type', 'summary')
            timestep = arguments.get('timestep', -1)
            img_base64 = sim_manager.visualize_simulation(
                arguments['sim_id'],
                viz_type=viz_type,
                timestep=timestep
            )
            result = {
                "sim_id": arguments['sim_id'],
                "visualization_type": viz_type,
                "image_base64": img_base64,
                "message": f"Generated {viz_type} visualization. Display using: data:image/png;base64,{{image_base64}}"
            }
            
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the MCP server"""
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    except KeyboardInterrupt:
        print("Server interrupted by user", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

if __name__ == "__main__":
    print("Starting FerroSim MCP Server...", file=sys.stderr)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server shutdown", file=sys.stderr)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
