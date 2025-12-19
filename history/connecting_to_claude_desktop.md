z# Connecting Your FerroSim MCP Server to Claude Desktop

## 🎯 Overview

There are 3 ways to use your MCP server:

1. **Claude Desktop App** ⭐ (Easiest for testing)
2. **Claude API with MCP Client** (For programmatic use)
3. **Custom Integration** (Advanced)

Let's start with #1 since it's the easiest for your hackathon demo.

---

## 🖥️ Method 1: Claude Desktop App (RECOMMENDED)

### **Step 1: Install Claude Desktop**

Download from: https://claude.ai/download

Available for:
- macOS (Apple Silicon or Intel)
- Windows
- Linux (AppImage)

### **Step 2: Configure MCP Server**

Claude Desktop uses a config file to know about your MCP servers.

**Config file location:**

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Create/edit this file:**

```json
{
  "mcpServers": {
    "ferrosim": {
      "command": "python3",
      "args": [
        "/absolute/path/to/ferrosim_mcp_server_minimal.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/your/venv/lib/python3.x/site-packages"
      }
    }
  }
}
```

**Replace with your actual paths:**
```json
{
  "mcpServers": {
    "ferrosim": {
      "command": "/Users/wallace/ferrosim-mcp-hackathon/venv/bin/python",
      "args": [
        "/Users/wallace/ferrosim-mcp-hackathon/ferrosim_mcp_server_minimal.py"
      ]
    }
  }
}
```

### **Step 3: Restart Claude Desktop**

1. Quit Claude Desktop completely
2. Reopen it
3. Start a new conversation

### **Step 4: Verify Connection**

In Claude Desktop, you should see:
- A 🔨 (hammer) icon in the input area → indicates MCP tools available
- Click it to see your tools listed

Type:
```
What MCP tools do you have available?
```

Claude should respond with your FerroSim tools!

---

## 🐛 Troubleshooting Claude Desktop Connection

### **Problem: No hammer icon appears**

**Check 1: Config file syntax**
```bash
# Validate JSON syntax
python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Check 2: Python path is correct**
```bash
# Test that your Python can run the server
/path/to/your/venv/bin/python /path/to/ferrosim_mcp_server_minimal.py
# Should wait for input (Ctrl+C to exit)
```

**Check 3: All dependencies installed in that Python**
```bash
/path/to/your/venv/bin/python -c "import mcp; import ferrosim; print('OK')"
```

**Check 4: Check Claude Desktop logs**
- **macOS**: `~/Library/Logs/Claude/`
- **Windows**: `%APPDATA%\Claude\Logs\`
- Look for errors about MCP server startup

### **Problem: Server starts but tools don't work**

**Check server logs:**
```bash
# Add logging to your server
import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Goes to Claude Desktop logs
)
```

### **Problem: Permission denied**

```bash
# Make sure script is executable
chmod +x /path/to/ferrosim_mcp_server_minimal.py

# Check file permissions
ls -la /path/to/ferrosim_mcp_server_minimal.py
```

---

## 💻 Method 2: Claude API with MCP Client (Programmatic)

If you want to test via Python script instead of Claude Desktop:

### **Install MCP Client SDK**

```bash
pip install anthropic-mcp
```

### **Create Test Script**

```python
#!/usr/bin/env python3
"""
Test FerroSim MCP Server with Claude API
"""

import os
import asyncio
import json
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_with_claude():
    # Start MCP server
    server_params = StdioServerParameters(
        command="python3",
        args=["/path/to/ferrosim_mcp_server_minimal.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Now use with Claude
            client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
            
            # Convert MCP tools to Claude format
            claude_tools = []
            for tool in tools.tools:
                claude_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            
            # Call Claude with tools
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                tools=claude_tools,
                messages=[{
                    "role": "user",
                    "content": "Create a small ferroelectric simulation with n=10"
                }]
            )
            
            print(f"\nClaude response: {response.content}")
            
            # Handle tool calls
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\nClaude wants to use: {block.name}")
                    print(f"Parameters: {block.input}")
                    
                    # Call MCP tool
                    result = await session.call_tool(
                        block.name,
                        arguments=block.input
                    )
                    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_mcp_with_claude())
```

**Run it:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
python test_mcp_client.py
```

---

## 🎬 Method 3: Quick Test Without Claude Desktop

For quick testing during development:

### **Create Manual Test Script**

```python
#!/usr/bin/env python3
"""
Manually test MCP server without Claude
Simulates what Claude would do
"""

import subprocess
import json
import sys

def test_mcp_server():
    # Start server
    process = subprocess.Popen(
        ['python3', 'ferrosim_mcp_server_minimal.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Test 1: List tools
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    process.stdin.write(json.dumps(request) + '\n')
    process.stdin.flush()
    
    response = process.stdout.readline()
    print("Tools available:")
    print(json.dumps(json.loads(response), indent=2))
    
    # Test 2: Initialize simulation
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "initialize_simulation",
            "arguments": {
                "n": 10,
                "k": 1.0,
                "mode": "tetragonal"
            }
        }
    }
    
    process.stdin.write(json.dumps(request) + '\n')
    process.stdin.flush()
    
    response = process.stdout.readline()
    print("\nSimulation created:")
    print(json.dumps(json.loads(response), indent=2))
    
    # Cleanup
    process.terminate()

if __name__ == "__main__":
    test_mcp_server()
```

---

## 📋 Complete Setup Checklist

Use this checklist for Claude Desktop setup:

```
□ Claude Desktop installed
□ Config file created at correct location
□ Python path is absolute (not relative)
□ Server script path is absolute
□ Virtual environment Python specified (if using venv)
□ JSON syntax validated
□ All dependencies installed (mcp, ferrosim, numpy, etc.)
□ Server script runs manually without errors
□ Claude Desktop restarted
□ Hammer icon visible in new conversation
□ Tools list shows your FerroSim tools
□ Test tool call works
```

---

## 🎯 Example Claude Desktop Session

Once connected, you can chat naturally:

**You:**
```
I have AFM data from a ferroelectric sample. Can you help me 
find the simulation parameters that match it?

The data is a 20x20 amplitude map with values around 0.8-0.9.
I think it's a tetragonal ferroelectric.
```

**Claude:** (will automatically see your MCP tools)
```
I can help you with that! I have access to FerroSim simulation tools.

Let me start by creating a simulation with reasonable initial parameters
for a tetragonal ferroelectric...

[Calls initialize_simulation]
[Calls run_simulation]
[Calls compare_with_afm_data]

The initial parameters give a correlation of 0.72. Let me try adjusting...
```

---

## 🔧 Advanced: Multiple MCP Servers

You can connect multiple MCP servers:

```json
{
  "mcpServers": {
    "ferrosim": {
      "command": "python3",
      "args": ["/path/to/ferrosim_mcp_server_minimal.py"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/data"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token"
      }
    }
  }
}
```

Then Claude can use all of them together!

---

## 📊 Verifying It Works

### **Test 1: List Tools**
```
You: "What MCP tools do you have?"

Claude should list:
- initialize_simulation
- run_simulation
- get_simulation_results
- compare_with_afm_data
- list_simulations
```

### **Test 2: Simple Simulation**
```
You: "Create a small simulation with n=10, k=1.0"

Claude should:
1. Call initialize_simulation
2. Report the sim_id
3. Confirm creation
```

### **Test 3: Full Workflow**
```
You: "Create simulation, run it, and get the final polarization map"

Claude should:
1. Call initialize_simulation
2. Call run_simulation  
3. Call get_simulation_results
4. Show you the results
```

---

## 🚀 Ready to Go!

Once you have the hammer icon in Claude Desktop and can see your tools,
you're ready to run your hackathon demo!

**Quick Start Command:**
```
Hi! I have AFM data showing ferroelectric domains. Can you help me
find which simulation parameters (k and dep_alpha) best match this data?

AFM amplitude values (20x20): [0.82, 0.85, 0.83, ...]

Target correlation > 0.90
```

Claude will automatically use your MCP tools to solve this!

---

## 📞 Help Resources

**If stuck:**
1. Check Claude Desktop logs: `~/Library/Logs/Claude/`
2. Test server manually: `python3 ferrosim_mcp_server_minimal.py`
3. Validate JSON: `python3 -m json.tool config.json`
4. Check MCP docs: https://modelcontextprotocol.io

**Common issues:**
- Wrong Python path → Use absolute path to venv Python
- Missing dependencies → Install in same Python as specified in config
- Syntax errors in config → Use JSON validator
- Server crashes → Check stderr logs in Claude Desktop logs folder
