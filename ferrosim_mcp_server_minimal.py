#!/usr/bin/env python3
"""
Minimal FerroSim MCP Server - Quick Start Template
Run this to test basic MCP server functionality
"""

import asyncio
import json
import sys
import uuid
from typing import Dict, Any
import numpy as np

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
# Simulation Manager - Minimal Implementation
# ============================================================================

class SimulationManager:
    """Manages active simulations"""
    
    def __init__(self):
        self.simulations: Dict[str, Dict[str, Any]] = {}
    
    def create_simulation(self, params: dict) -> str:
        """Create new simulation instance"""
        sim_id = str(uuid.uuid4())[:8]
        
        # Extract parameters with defaults
        n = params.get('n', 10)
        gamma = params.get('gamma', 1.0)
        k = params.get('k', 1.0)
        mode = params.get('mode', 'tetragonal')
        dep_alpha = params.get('dep_alpha', 0.0)
        
        # Create time vector if not provided
        if 'time_vec' in params:
            time_vec = np.array(params['time_vec'])
        else:
            time_vec = np.linspace(0, 1.0, 1000)
        
        # Create applied field if not provided
        if 'applied_field' in params:
            applied_field = np.array(params['applied_field'])
        else:
            applied_field = np.zeros((len(time_vec), 2))
            # Default: sine wave in y direction
            applied_field[:, 1] = 10 * np.sin(time_vec * 2 * np.pi * 2)
        
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
                init='pr'
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
            # Run simulation
            results = sim.runSim(calc_pr=False, verbose=verbose)
            sim_data['results'] = results
            sim_data['status'] = 'completed'
            
            # Get final polarization map
            pmat = sim.getPmat(timestep=-1)
            
            return {
                'sim_id': sim_id,
                'status': 'completed',
                'total_polarization': results['Polarization'].tolist(),
                'final_Px': pmat[0, :, :].tolist(),
                'final_Py': pmat[1, :, :].tolist()
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
        pmat = sim.getPmat(timestep=timestep)
        
        return {
            'sim_id': sim_id,
            'timestep': timestep,
            'Px': pmat[0, :, :].tolist() if timestep is not None else pmat[0, :, :, :].tolist(),
            'Py': pmat[1, :, :].tolist() if timestep is not None else pmat[1, :, :, :].tolist(),
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
            description="Create a new FerroSim simulation with specified parameters",
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
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    print("Starting FerroSim MCP Server...", file=sys.stderr)
    asyncio.run(main())
