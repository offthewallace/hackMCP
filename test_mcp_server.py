#!/usr/bin/env python3
"""
Test MCP Server - Debug Connection Issues
This script simulates how Claude Desktop connects to the MCP server
"""

import subprocess
import json
import sys

print("Testing MCP Server Connection...")
print("=" * 50)

# Path to your conda python and server script
PYTHON_PATH = "/Users/guanlinhe/miniconda3/envs/ferrosim_mcp/bin/python"
SERVER_SCRIPT = "/Users/guanlinhe/github/hackMCP/ferrosim_mcp_server_minimal.py"

print(f"Python: {PYTHON_PATH}")
print(f"Server: {SERVER_SCRIPT}")
print()

try:
    # Start the server process
    print("Starting MCP server...")
    process = subprocess.Popen(
        [PYTHON_PATH, SERVER_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send initialization request (JSON-RPC format)
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0"
            }
        }
    }
    
    print("Sending initialization request...")
    request_str = json.dumps(init_request) + "\n"
    print(f"Request: {request_str[:100]}...")
    
    # Send request
    process.stdin.write(request_str)
    process.stdin.flush()
    
    # Try to read response (with timeout)
    import select
    import time
    
    print("\nWaiting for response...")
    time.sleep(2)  # Give it time to process
    
    # Check stderr for any errors
    stderr_data = ""
    if select.select([process.stderr], [], [], 0)[0]:
        stderr_data = process.stderr.read()
        if stderr_data:
            print(f"\nStderr output:\n{stderr_data}")
    
    # Try to read stdout
    stdout_data = ""
    if select.select([process.stdout], [], [], 0)[0]:
        stdout_data = process.stdout.readline()
        if stdout_data:
            print(f"\nStdout response:\n{stdout_data}")
            
            # Try to parse as JSON
            try:
                response = json.loads(stdout_data)
                print("\n✓ Valid JSON response received!")
                print(json.dumps(response, indent=2))
            except json.JSONDecodeError as e:
                print(f"\n✗ JSON Parse Error: {e}")
                print(f"Raw data: {repr(stdout_data)}")
                print(f"First 200 chars: {stdout_data[:200]}")
        else:
            print("\n⚠ No stdout data received")
    else:
        print("\n⚠ No data available on stdout")
    
    # Cleanup
    process.terminate()
    process.wait(timeout=2)
    print("\n✓ Server terminated cleanly")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    if 'process' in locals():
        process.kill()

print("\n" + "=" * 50)
print("Test complete")

