"""
Visual Guide: How Claude Desktop Connects to Your MCP Server
"""

connection_diagram = """
┌─────────────────────────────────────────────────────────────────────┐
│                         CLAUDE DESKTOP APP                          │
│                      (Your local application)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  You type: "Create a simulation with n=20"                         │
│                                                                     │
│  Claude sees: You have these MCP tools available:                  │
│    • initialize_simulation                                          │
│    • run_simulation                                                 │
│    • compare_with_afm_data                                         │
│    • ...                                                            │
│                                                                     │
│  Claude decides: I'll use 'initialize_simulation'                  │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ JSON-RPC over stdin/stdout
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    claude_desktop_config.json                       │
│                    (Configuration file)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  {                                                                  │
│    "mcpServers": {                                                  │
│      "ferrosim": {                                                  │
│        "command": "/path/to/python",                               │
│        "args": ["/path/to/ferrosim_mcp_server_minimal.py"]        │
│      }                                                              │
│    }                                                                │
│  }                                                                  │
│                                                                     │
│  This tells Claude Desktop how to start your server                │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Spawns subprocess
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│              ferrosim_mcp_server_minimal.py                         │
│                   (Your MCP Server)                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Receives: {                                                        │
│    "method": "tools/call",                                          │
│    "params": {                                                      │
│      "name": "initialize_simulation",                              │
│      "arguments": {"n": 20, "k": 1.0}                             │
│    }                                                                │
│  }                                                                  │
│                                                                     │
│  Server executes:                                                   │
│    sim_id = sim_manager.create_simulation(params)                  │
│                                                                     │
│  Returns: {                                                         │
│    "result": {                                                      │
│      "sim_id": "abc123",                                           │
│      "status": "created"                                            │
│    }                                                                │
│  }                                                                  │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Python import
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       FerroSim Library                              │
│                   (Actual simulation code)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  from ferrosim import Ferro2DSim                                   │
│                                                                     │
│  sim = Ferro2DSim(n=20, k=1.0, ...)                               │
│  results = sim.runSim()                                            │
│  pmat = sim.getPmat()                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
"""

print(connection_diagram)

print("\n" + "="*70)
print("KEY POINTS")
print("="*70)

key_points = """
1. CLAUDE DESKTOP is just a chat interface
   • It's the UI where you talk to Claude
   • When you type, Claude can see available MCP tools
   • Claude decides which tools to use

2. CONFIG FILE tells Claude Desktop about your server
   • Location: ~/Library/Application Support/Claude/claude_desktop_config.json (macOS)
   • Contains: Command to start your MCP server
   • Claude Desktop reads this on startup

3. YOUR MCP SERVER runs as a subprocess
   • Claude Desktop starts it using the command in config
   • Communicates via JSON-RPC over stdin/stdout
   • Stays running as long as Claude Desktop is open

4. FERROSIM LIBRARY does the actual simulation
   • Your MCP server is just a wrapper
   • It translates between Claude and FerroSim
   • FerroSim doesn't know about MCP or Claude

The magic happens in the CONFIG FILE - that's what connects everything!
"""

print(key_points)

print("\n" + "="*70)
print("COMMUNICATION FLOW")
print("="*70)

communication_flow = """
STEP-BY-STEP: What happens when you ask Claude to create a simulation

1. You type in Claude Desktop:
   "Create a simulation with n=20, k=1.5"

2. Claude Desktop sends your message to Claude API (Anthropic's servers)

3. Claude API sees: 
   • Your message
   • Available tools (from your MCP server)

4. Claude decides:
   "I should use initialize_simulation tool with n=20, k=1.5"

5. Claude Desktop receives Claude's decision to use a tool

6. Claude Desktop sends JSON-RPC to your MCP server:
   {
     "method": "tools/call",
     "params": {
       "name": "initialize_simulation",
       "arguments": {"n": 20, "k": 1.5}
     }
   }

7. Your MCP server receives this, executes:
   sim_manager.create_simulation({"n": 20, "k": 1.5})

8. This creates a Ferro2DSim instance:
   Ferro2DSim(n=20, k=1.5, ...)

9. Your server returns result:
   {
     "result": {
       "sim_id": "abc123",
       "status": "created"
     }
   }

10. Claude Desktop sends this back to Claude API

11. Claude API formats a response:
    "I've created simulation abc123 with n=20 and k=1.5"

12. You see this response in Claude Desktop!

The entire round trip takes ~1-2 seconds.
"""

print(communication_flow)

print("\n" + "="*70)
print("WHERE EACH PIECE LIVES")
print("="*70)

locations = """
COMPONENT                          LOCATION
─────────────────────────────────────────────────────────────────────

Claude Desktop App                 /Applications/Claude.app (macOS)
                                  C:\\Program Files\\Claude\\ (Windows)

Config File                       ~/Library/Application Support/Claude/
                                  %APPDATA%\\Claude\\

Your MCP Server                   /path/to/ferrosim-mcp-hackathon/
                                  ferrosim_mcp_server_minimal.py

FerroSim Library                  Your virtualenv site-packages/
                                  venv/lib/python3.x/site-packages/ferrosim/

Claude API                        Anthropic's servers (claude.ai)
                                  (Not on your computer)

Logs                              ~/Library/Logs/Claude/ (macOS)
                                  %APPDATA%\\Claude\\Logs\\ (Windows)
"""

print(locations)

print("\n" + "="*70)
print("QUICK START COMMANDS")
print("="*70)

commands = """
# 1. Configure Claude Desktop (automated)
python3 configure_claude_desktop.py

# 2. Or manually edit config
# macOS:
nano ~/Library/Application\\ Support/Claude/claude_desktop_config.json

# Windows:
notepad %APPDATA%\\Claude\\claude_desktop_config.json

# 3. Test your server manually
python3 ferrosim_mcp_server_minimal.py
# (Should wait for input - press Ctrl+C to exit)

# 4. Check if server can start
/path/to/venv/bin/python ferrosim_mcp_server_minimal.py

# 5. Validate config JSON
python3 -m json.tool ~/Library/Application\\ Support/Claude/claude_desktop_config.json

# 6. View Claude Desktop logs
# macOS:
tail -f ~/Library/Logs/Claude/mcp*.log

# Windows:
type %APPDATA%\\Claude\\Logs\\mcp*.log

# 7. Restart Claude Desktop
# macOS:
killall Claude && open -a Claude

# Windows:
taskkill /IM Claude.exe /F && start Claude
"""

print(commands)

print("\n" + "="*70)
print("TESTING CHECKLIST")
print("="*70)

checklist = """
□ Python 3.8+ installed
□ Virtual environment created
□ FerroSim installed (pip install git+https://github.com/ramav87/FerroSim.git@rama-dev)
□ MCP SDK installed (pip install mcp)
□ Other dependencies installed (numpy, matplotlib, etc.)
□ ferrosim_mcp_server_minimal.py exists
□ Server runs without errors when started manually
□ Claude Desktop app installed
□ Config file created at correct location
□ Config file has valid JSON syntax
□ Config uses ABSOLUTE paths (not relative)
□ Config points to correct Python (in venv if using venv)
□ Claude Desktop restarted after config change
□ New conversation started in Claude Desktop
□ Hammer icon (🔨) visible in input area
□ Clicking hammer shows your tools
□ Test: "What MCP tools do you have?" works
□ Test: "Create a simulation" triggers tool use
"""

print(checklist)
