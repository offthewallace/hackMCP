#!/usr/bin/env python3
"""Test JSON serialization of simulation results"""

import json
import numpy as np
from ferrosim import Ferro2DSim

print("Testing JSON serialization...")

# Create a simple simulation
sim = Ferro2DSim(n=5, gamma=1.0, k=1.0, mode='tetragonal')
print("✓ Simulation created")

# Run it
results = sim.runSim(calc_pr=False, verbose=False)
print("✓ Simulation run")

# Get polarization matrix
pmat = sim.getPmat()
pmat_final = pmat[:, -1, :, :]
print(f"✓ Got Pmat shape: {pmat_final.shape}")

# Test serialization
test_result = {
    'sim_id': 'test123',
    'status': 'completed',
    'timestep': -1,
    'final_Px': pmat_final[0, :, :].tolist(),
    'final_Py': pmat_final[1, :, :].tolist()
}

# Try to serialize to JSON
try:
    json_str = json.dumps(test_result, indent=2)
    print("✓ JSON serialization successful")
    print(f"\nJSON length: {len(json_str)} chars")
    print(f"First 100 chars: {json_str[:100]}")
    
    # Try to parse it back
    parsed = json.loads(json_str)
    print("✓ JSON parsing successful")
    print(f"\nKeys in result: {list(parsed.keys())}")
    
except Exception as e:
    print(f"✗ JSON error: {e}")
    import traceback
    traceback.print_exc()

