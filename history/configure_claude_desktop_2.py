#!/usr/bin/env python3
"""
Automated Claude Desktop MCP Configuration
This script configures Claude Desktop to use your FerroSim MCP server
"""

import json
import os
import sys
import platform
from pathlib import Path
import shutil

def get_claude_config_path():
    """Get Claude Desktop config file path for current OS"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    else:
        raise OSError(f"Unsupported OS: {system}")

def get_python_path():
    """Get absolute path to current Python interpreter"""
    return sys.executable

def get_script_dir():
    """Get directory where this script is located"""
    return Path(__file__).parent.absolute()

def backup_config(config_path):
    """Backup existing config if it exists"""
    if config_path.exists():
        backup_path = config_path.with_suffix('.json.backup')
        shutil.copy(config_path, backup_path)
        print(f"✓ Backed up existing config to: {backup_path}")
        return True
    return False

def create_config(config_path, server_path, python_path):
    """Create or update Claude Desktop config"""
    
    # Load existing config if it exists
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {"mcpServers": {}}
    
    # Add FerroSim MCP server
    config["mcpServers"]["ferrosim"] = {
        "command": str(python_path),
        "args": [str(server_path)]
    }
    
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Config written to: {config_path}")

def validate_setup():
    """Validate that everything is set up correctly"""
    print("\n" + "="*70)
    print("VALIDATION")
    print("="*70)
    
    # Check if FerroSim is installed
    try:
        import ferrosim
        print("✓ FerroSim installed")
    except ImportError:
        print("✗ FerroSim NOT installed")
        print("  Install with: pip install git+https://github.com/ramav87/FerroSim.git@rama-dev")
        return False
    
    # Check if MCP is installed
    try:
        import mcp
        print("✓ MCP SDK installed")
    except ImportError:
        print("✗ MCP SDK NOT installed")
        print("  Install with: pip install mcp")
        return False
    
    # Check if server script exists
    script_dir = get_script_dir()
    server_path = script_dir / "ferrosim_mcp_server_minimal.py"
    
    if server_path.exists():
        print(f"✓ Server script found: {server_path}")
    else:
        print(f"✗ Server script NOT found: {server_path}")
        return False
    
    # Check if server runs
    import subprocess
    try:
        proc = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        proc.terminate()
        proc.wait(timeout=2)
        print("✓ Server script can run")
    except Exception as e:
        print(f"✗ Server script failed to run: {e}")
        return False
    
    return True

def print_next_steps():
    """Print instructions for next steps"""
    print("\n" + "="*70)
    print("SETUP COMPLETE! 🎉")
    print("="*70)
    
    print("\nNext steps:")
    print("\n1. RESTART CLAUDE DESKTOP")
    print("   - Quit Claude Desktop completely")
    print("   - Reopen it")
    
    print("\n2. VERIFY CONNECTION")
    print("   - Start a new conversation")
    print("   - Look for 🔨 (hammer) icon in the input area")
    print("   - Click it to see your FerroSim tools")
    
    print("\n3. TEST IT")
    print("   - Type: 'What MCP tools do you have?'")
    print("   - Claude should list: initialize_simulation, run_simulation, etc.")
    
    print("\n4. RUN YOUR HACKATHON DEMO")
    print("   - Say: 'I have AFM data. Help me find matching simulation parameters.'")
    print("   - Watch Claude use your tools automatically!")
    
    print("\n" + "="*70)
    print("TROUBLESHOOTING")
    print("="*70)
    
    system = platform.system()
    if system == "Darwin":
        log_path = Path.home() / "Library" / "Logs" / "Claude"
    elif system == "Windows":
        log_path = Path(os.environ["APPDATA"]) / "Claude" / "Logs"
    else:
        log_path = Path.home() / ".config" / "Claude" / "logs"
    
    print(f"\nIf tools don't appear, check logs at:")
    print(f"  {log_path}")
    
    print("\nCommon issues:")
    print("  • No hammer icon → Check config file syntax")
    print("  • Tools listed but don't work → Check server logs")
    print("  • Server won't start → Check dependencies")
    
    config_path = get_claude_config_path()
    print(f"\nYour config file:")
    print(f"  {config_path}")

def main():
    print("="*70)
    print("CLAUDE DESKTOP MCP CONFIGURATION")
    print("FerroSim MCP Server Setup")
    print("="*70)
    
    # Detect OS
    system = platform.system()
    print(f"\nDetected OS: {system}")
    
    # Get paths
    config_path = get_claude_config_path()
    python_path = get_python_path()
    script_dir = get_script_dir()
    server_path = script_dir / "ferrosim_mcp_server_minimal.py"
    
    print(f"Config path: {config_path}")
    print(f"Python path: {python_path}")
    print(f"Server path: {server_path}")
    
    # Validate setup
    print("\n" + "="*70)
    print("VALIDATING SETUP")
    print("="*70)
    
    if not validate_setup():
        print("\n❌ Validation failed. Please fix issues above before continuing.")
        sys.exit(1)
    
    # Ask for confirmation
    print("\n" + "="*70)
    print("CONFIGURATION")
    print("="*70)
    
    print(f"\nThis will configure Claude Desktop to use:")
    print(f"  Server: {server_path}")
    print(f"  Python: {python_path}")
    
    response = input("\nProceed? [y/N]: ").strip().lower()
    if response not in ['y', 'yes']:
        print("Aborted.")
        sys.exit(0)
    
    # Backup existing config
    if config_path.exists():
        backup_config(config_path)
    
    # Create/update config
    create_config(config_path, server_path, python_path)
    
    print("\n✅ Configuration complete!")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
