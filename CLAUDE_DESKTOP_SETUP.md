# FerroSim MCP Server - Claude Desktop Integration

This guide shows you how to connect the FerroSim MCP Server with Claude Desktop.

## What You've Built

Your `ferrosim_mcp_server_minimal.py` is already configured to work with Claude Desktop! It uses **stdio (standard input/output)** communication, which is exactly what Claude Desktop needs.

## Quick Setup

### Step 1: Run the Setup Script

```bash
./setup_claude_desktop.sh
```

This will:
- Create the Claude Desktop configuration file
- Set up the correct paths to your conda environment
- Backup any existing configuration

### Step 2: Restart Claude Desktop

1. **Quit Claude Desktop completely** (⌘+Q on Mac)
2. **Reopen Claude Desktop**

### Step 3: Verify Connection

In Claude Desktop, you can now ask:

```
"Can you list the available FerroSim tools?"
```

or

```
"Can you run a FerroSim simulation with n=15, k=1.5, and dep_alpha=0.1?"
```

## Available MCP Tools

Once connected, Claude Desktop will have access to these tools:

1. **initialize_simulation** - Create a new FerroSim simulation
   - Parameters: `n`, `gamma`, `k`, `mode`, `dep_alpha`
   
2. **run_simulation** - Execute a created simulation
   - Parameters: `sim_id`, `verbose`
   
3. **get_simulation_results** - Retrieve simulation results
   - Parameters: `sim_id`, `timestep`
   
4. **compare_with_afm_data** - Compare with experimental AFM data
   - Parameters: `sim_id`, `afm_data`, `component`
   
5. **list_simulations** - List all active simulations

## Configuration File Location

The configuration is stored at:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

## Manual Configuration (Alternative)

If you prefer to manually edit the config, add this to your Claude Desktop config:

```json
{
  "mcpServers": {
    "ferrosim": {
      "command": "/Users/guanlinhe/miniconda3/envs/ferrosim_mcp/bin/python",
      "args": [
        "/Users/guanlinhe/github/hackMCP/ferrosim_mcp_server_minimal.py"
      ],
      "env": {}
    }
  }
}
```

## Troubleshooting

### Server Not Showing Up

1. **Check Developer Console** in Claude Desktop (if available)
2. **Verify paths** in the config file match your actual file locations
3. **Ensure conda environment** has all dependencies installed
4. **Check permissions** - make sure the script is executable

### Test the Server Manually

You can test if the server works by running it directly:

```bash
conda activate ferrosim_mcp
python ferrosim_mcp_server_minimal.py
```

You should see: `Starting FerroSim MCP Server...`

Press Ctrl+C to stop it.

### Common Issues

**Issue**: "Python not found"
- **Solution**: Run `./setup.sh` first to create the conda environment

**Issue**: "Module not found: mcp"
- **Solution**: Activate the environment and run `pip install mcp`

**Issue**: "Module not found: ferrosim"
- **Solution**: Run `pip install git+https://github.com/ramav87/FerroSim.git@rama-dev`

## Example Workflow with Claude Desktop

Once connected, you can have conversations like:

```
You: "I have AFM data showing ferroelectric domains. Can you help me 
      find the best simulation parameters to match it?"

Claude: [Uses initialize_simulation tool]
        "I've created a simulation with initial parameters. Let me run it..."
        
        [Uses run_simulation tool]
        "The simulation completed. Now let me compare it with your AFM data..."
        
        [Uses compare_with_afm_data tool]
        "The correlation is 0.65. Let me try adjusting the coupling constant k..."
```

## Key Differences from API-Based Approach

| Feature | API Key (Previous) | Claude Desktop (Now) |
|---------|-------------------|----------------------|
| Connection | HTTP requests | stdio (pipes) |
| Setup | Need ANTHROPIC_API_KEY | Just config file |
| Usage | Python scripts | Natural conversation |
| Tools | Manual API calls | Automatic tool discovery |
| State | Stateless | Persistent during session |

## What Was Fixed

1. ✅ Fixed `getPmat()` API calls (removed `timestep` parameter)
2. ✅ Updated both `run_simulation` and `get_results` methods
3. ✅ Created Claude Desktop configuration
4. ✅ Made scripts executable

## Next Steps

Try these example prompts in Claude Desktop:

1. "Create a tetragonal ferroelectric simulation with 20x20 lattice"
2. "Run the simulation and show me the final polarization pattern"
3. "Compare this simulation with my AFM data [paste data]"
4. "Try different k values to improve the match"

Happy simulating! 🎉

