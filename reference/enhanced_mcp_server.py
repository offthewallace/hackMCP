#!/usr/bin/env python3
"""
Enhanced FerroSim MCP Server with AFM Digital Twin Integration
Demonstrates how to add AFM tools to existing FerroSim MCP server
"""

# This is a demonstration of how to enhance your existing
# ferrosim_mcp_server_minimal.py with AFM capabilities
#
# To integrate:
# 1. Copy the AFMDigitalTwin import and initialization
# 2. Add the AFM tools to your @app.list_tools()
# 3. Add the AFM tool handlers to your @app.call_tool()

import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import your existing FerroSim manager
# (assuming ferrosim_mcp_server_minimal.py is in same directory)
try:
    from ferrosim_mcp_server_minimal import SimulationManager
except ImportError:
    print("Warning: Could not import SimulationManager")
    SimulationManager = None

# NEW: Import AFM Digital Twin
try:
    from afm_digital_twin import AFMDigitalTwin
    AFM_AVAILABLE = True
except ImportError:
    print("Warning: AFMDigitalTwin not available")
    AFM_AVAILABLE = False

import numpy as np

# ============================================================================
# Server Setup
# ============================================================================

app = Server("enhanced-ferrosim-afm-server")

# Initialize managers
if SimulationManager:
    sim_manager = SimulationManager()
else:
    sim_manager = None

if AFM_AVAILABLE:
    afm_manager = AFMDigitalTwin(scan_size=(256, 256))
else:
    afm_manager = None

# ============================================================================
# Tools Definition
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools"""
    
    tools = []
    
    # ========================================================================
    # FerroSim Tools (your existing tools)
    # ========================================================================
    
    if sim_manager:
        tools.extend([
            Tool(
                name="initialize_simulation",
                description="Create a new FerroSim simulation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "n": {
                            "type": "integer",
                            "description": "Lattice size (NxN grid)"
                        },
                        "k": {
                            "type": "number",
                            "description": "Coupling constant"
                        },
                        "mode": {
                            "type": "string",
                            "description": "Material mode: tetragonal, rhombohedral, etc."
                        }
                    },
                    "required": ["n"]
                }
            ),
            Tool(
                name="run_simulation",
                description="Execute a FerroSim simulation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sim_id": {
                            "type": "string",
                            "description": "Simulation ID"
                        }
                    },
                    "required": ["sim_id"]
                }
            ),
            Tool(
                name="get_simulation_results",
                description="Get polarization data from simulation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sim_id": {"type": "string"},
                        "timestep": {"type": "integer"}
                    },
                    "required": ["sim_id"]
                }
            )
        ])
    
    # ========================================================================
    # AFM Tools (NEW - added for DTMicroscope integration)
    # ========================================================================
    
    if afm_manager:
        tools.extend([
            Tool(
                name="afm_scan_surface",
                description="Perform AFM PFM scan of ferroelectric surface",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "voltage": {
                            "type": "number",
                            "description": "AC voltage in Volts (default: 5.0)"
                        },
                        "scan_size": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Scan size [width, height] in pixels"
                        }
                    }
                }
            ),
            Tool(
                name="afm_get_piezoresponse",
                description="Get PFM amplitude and phase data from scan",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scan_id": {
                            "type": "string",
                            "description": "Scan identifier"
                        }
                    },
                    "required": ["scan_id"]
                }
            ),
            Tool(
                name="afm_analyze_domains",
                description="Analyze ferroelectric domain structure from AFM scan",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scan_id": {
                            "type": "string",
                            "description": "Scan identifier"
                        }
                    },
                    "required": ["scan_id"]
                }
            ),
            Tool(
                name="afm_list_scans",
                description="List all available AFM scans",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ])
    
    # ========================================================================
    # Theory-Experiment Matching Tool (NEW - combines both)
    # ========================================================================
    
    if sim_manager and afm_manager:
        tools.append(
            Tool(
                name="match_simulation_to_afm",
                description="Compare FerroSim simulation with AFM scan data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sim_id": {
                            "type": "string",
                            "description": "Simulation ID"
                        },
                        "scan_id": {
                            "type": "string",
                            "description": "AFM scan ID"
                        }
                    },
                    "required": ["sim_id", "scan_id"]
                }
            )
        )
    
    return tools

# ============================================================================
# Tool Implementations
# ============================================================================

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    try:
        # ====================================================================
        # FerroSim Tools (your existing implementations)
        # ====================================================================
        
        if name == "initialize_simulation" and sim_manager:
            result = sim_manager.create_simulation(arguments)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "run_simulation" and sim_manager:
            result = sim_manager.run_simulation(arguments['sim_id'])
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "get_simulation_results" and sim_manager:
            result = sim_manager.get_results(
                arguments['sim_id'],
                arguments.get('timestep', -1)
            )
            return [TextContent(type="text", text=json.dumps(result))]
        
        # ====================================================================
        # AFM Tools (NEW implementations)
        # ====================================================================
        
        elif name == "afm_scan_surface" and afm_manager:
            # Extract scan parameters
            scan_size = arguments.get('scan_size', [256, 256])
            voltage = arguments.get('voltage', 5.0)
            
            # Create new AFM instance with specified size
            afm = AFMDigitalTwin(scan_size=tuple(scan_size))
            
            # Perform scan
            result = afm.scan_ferroelectric_surface({
                'voltage': voltage
            })
            
            # Store AFM instance globally for later access
            global afm_manager
            afm_manager = afm
            
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "afm_get_piezoresponse" and afm_manager:
            result = afm_manager.get_piezoresponse(arguments['scan_id'])
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "afm_analyze_domains" and afm_manager:
            result = afm_manager.analyze_domain_structure(arguments['scan_id'])
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "afm_list_scans" and afm_manager:
            result = afm_manager.list_scans()
            return [TextContent(type="text", text=json.dumps(result))]
        
        # ====================================================================
        # Theory-Experiment Matching (NEW - uses both managers)
        # ====================================================================
        
        elif name == "match_simulation_to_afm":
            if not sim_manager or not afm_manager:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Managers not available"})
                )]
            
            # Get simulation results
            sim_results = sim_manager.get_results(arguments['sim_id'])
            sim_data = np.array(sim_results['polarization_magnitude'])
            
            # Get AFM data
            afm_results = afm_manager.get_piezoresponse(arguments['scan_id'])
            afm_data = np.array(afm_results['amplitude'])
            
            # Resize simulation to match AFM resolution
            from scipy.ndimage import zoom
            if sim_data.shape != afm_data.shape:
                zoom_factor = afm_data.shape[0] / sim_data.shape[0]
                sim_data = zoom(sim_data, zoom_factor, order=1)
            
            # Calculate comparison metrics
            correlation = float(np.corrcoef(
                sim_data.flatten(),
                afm_data.flatten()
            )[0, 1])
            
            mse = float(np.mean((sim_data - afm_data) ** 2))
            rmse = float(np.sqrt(mse))
            
            # Normalized RMSE
            nrmse = rmse / (afm_data.max() - afm_data.min())
            
            result = {
                "sim_id": arguments['sim_id'],
                "scan_id": arguments['scan_id'],
                "correlation": correlation,
                "mse": mse,
                "rmse": rmse,
                "nrmse": float(nrmse),
                "match_quality": "excellent" if correlation > 0.9 else
                                "good" if correlation > 0.8 else
                                "fair" if correlation > 0.7 else "poor"
            }
            
            return [TextContent(type="text", text=json.dumps(result))]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool or manager unavailable: {name}"})
            )]
    
    except Exception as e:
        import traceback
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        return [TextContent(type="text", text=json.dumps(error_details))]

# ============================================================================
# Main
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
    print("Starting Enhanced FerroSim+AFM MCP Server...")
    print("Available capabilities:")
    if sim_manager:
        print("  ✓ FerroSim simulation tools")
    else:
        print("  ✗ FerroSim not available")
    
    if afm_manager:
        print("  ✓ AFM digital twin tools")
    else:
        print("  ✗ AFM not available")
    
    print("\nWaiting for requests...")
    asyncio.run(main())
