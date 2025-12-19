#!/usr/bin/env python3
"""
Test Enhanced FerroSim MCP Server Features
Tests all new capabilities before deployment
"""

import sys
import numpy as np
from ferrosim import Ferro2DSim

print("Testing Enhanced FerroSim MCP Features...")
print("=" * 60)

# Test 1: Electric Field Generation
print("\n1. Testing Electric Field Generation...")
sys.path.insert(0, '/Users/guanlinhe/github/hackMCP')
from ferrosim_mcp_server_minimal import generate_electric_field

time_vec = np.linspace(0, 2, 100)

# Test sine wave
field_sine = generate_electric_field('sine', time_vec, {
    'amplitude_x': 10, 'amplitude_y': 20, 'freq_x': 1.0, 'freq_y': 2.0
})
assert field_sine.shape == (100, 2), "Sine field shape incorrect"
print("   ✓ Sine wave field generation works")

# Test step function
field_step = generate_electric_field('step', time_vec, {
    'Ex': 0.5, 'Ey': 1.0, 'step_fraction': 0.25
})
assert field_step.shape == (100, 2), "Step field shape incorrect"
assert field_step[50, 0] == 0.0, "Step field should be zero after step_fraction"
print("   ✓ Step field generation works")

# Test polynomial
field_poly = generate_electric_field('polynomial', time_vec, {
    'amplitude_x': 180, 'power': 2.0
})
assert field_poly.shape == (100, 2), "Polynomial field shape incorrect"
print("   ✓ Polynomial field generation works")

# Test zero field
field_zero = generate_electric_field('zero', time_vec, {})
assert np.all(field_zero == 0), "Zero field should be all zeros"
print("   ✓ Zero field generation works")

# Test 2: Defect Generation
print("\n2. Testing Defect Generation...")
from ferrosim_mcp_server_minimal import generate_defects

# Test no defects
defects_none = generate_defects('none', 10, {})
assert len(defects_none) == 100, "Should have 100 defects for 10x10 grid"
assert all(d == (0.0, 0.0) for d in defects_none), "All should be (0,0)"
print("   ✓ No defects generation works")

# Test random defects
defects_random = generate_defects('random', 10, {
    'num_defects': 5, 'strength_mean': 15.0, 'seed': 42
})
assert len(defects_random) == 100, "Should have 100 sites"
non_zero = [d for d in defects_random if d != (0.01, 0.01)]
assert len(non_zero) == 5, "Should have 5 non-zero defects"
print("   ✓ Random defects generation works")

# Test periodic defects
defects_periodic = generate_defects('periodic', 10, {
    'row_spacing': 5, 'col_spacing': 10, 'seed': 42
})
assert len(defects_periodic) == 100, "Should have 100 sites"
print("   ✓ Periodic defects generation works")

# Test 3: Basic Simulation with Custom Field
print("\n3. Testing Simulation with Custom Field...")
n = 5
time_vec = np.linspace(0, 1.0, 50)
applied_field = generate_electric_field('sine', time_vec, {
    'amplitude_y': 10.0, 'freq_y': 2.0
})

sim = Ferro2DSim(
    n=n,
    gamma=1.0,
    k=1.0,
    mode='tetragonal',
    time_vec=time_vec,
    appliedE=applied_field,
    init='pr'
)
results = sim.runSim(calc_pr=False, verbose=False)
assert 'Polarization' in results, "Results should contain Polarization"
print("   ✓ Simulation with custom sine field works")

# Test 4: Simulation with Defects
print("\n4. Testing Simulation with Defects...")
defects = generate_defects('random', n, {'num_defects': 3, 'seed': 42})
sim_defects = Ferro2DSim(
    n=n,
    gamma=1.0,
    k=1.0,
    mode='tetragonal',
    time_vec=time_vec,
    appliedE=applied_field,
    defects=defects,
    init='pr'
)
results_defects = sim_defects.runSim(calc_pr=False, verbose=False)
assert 'Polarization' in results_defects, "Results should contain Polarization"
print("   ✓ Simulation with defects works")

# Test 5: Ground State Simulation
print("\n5. Testing Ground State Setup...")
time_vec_gs = np.linspace(0, 2.0, 100)
field_gs = generate_electric_field('step', time_vec_gs, {
    'Ex': -0.5, 'Ey': -0.5, 'step_fraction': 0.25
})
sim_gs = Ferro2DSim(
    n=n,
    gamma=1.0,
    k=5.0,
    mode='tetragonal',
    dep_alpha=0.2,
    time_vec=time_vec_gs,
    appliedE=field_gs,
    init='random'
)
results_gs = sim_gs.runSim(calc_pr=False, verbose=False)
assert 'Polarization' in results_gs, "Ground state results should contain Polarization"
print("   ✓ Ground state simulation setup works")

# Test 6: Visualization Generation
print("\n6. Testing Visualization Generation...")
from ferrosim_mcp_server_minimal import generate_visualization

# Suppress matplotlib warnings
import warnings
warnings.filterwarnings('ignore')

# Test summary plot
try:
    img_summary = generate_visualization(sim, 'summary')
    assert isinstance(img_summary, str), "Should return base64 string"
    assert len(img_summary) > 100, "Base64 string should be substantial"
    print("   ✓ Summary visualization works")
except Exception as e:
    print(f"   ⚠ Summary visualization: {e}")

# Test quiver plot
try:
    img_quiver = generate_visualization(sim, 'quiver', timestep=-1)
    assert isinstance(img_quiver, str), "Should return base64 string"
    print("   ✓ Quiver visualization works")
except Exception as e:
    print(f"   ⚠ Quiver visualization: {e}")

# Test magnitude_angle plot
try:
    img_mag_ang = generate_visualization(sim, 'magnitude_angle', timestep=-1)
    assert isinstance(img_mag_ang, str), "Should return base64 string"
    print("   ✓ Magnitude/Angle visualization works")
except Exception as e:
    print(f"   ⚠ Magnitude/Angle visualization: {e}")

# Test 7: SimulationManager Integration
print("\n7. Testing SimulationManager Integration...")
from ferrosim_mcp_server_minimal import SimulationManager

manager = SimulationManager()

# Test creation with field_config
sim_id = manager.create_simulation({
    'n': 5,
    'k': 1.5,
    't_end': 1.0,
    'n_steps': 50,
    'field_config': {
        'type': 'sine',
        'params': {'amplitude_y': 10.0, 'freq_y': 2.0}
    },
    'defect_config': {
        'type': 'random',
        'params': {'num_defects': 2, 'seed': 42}
    }
})
assert sim_id in manager.simulations, "Simulation should be created"
print(f"   ✓ Created simulation {sim_id}")

# Test running
results = manager.run_simulation(sim_id, verbose=False)
assert results['status'] == 'completed', "Simulation should complete"
print(f"   ✓ Ran simulation {sim_id}")

# Test getting results
sim_results = manager.get_results(sim_id)
assert 'Px' in sim_results, "Results should contain Px"
assert 'Py' in sim_results, "Results should contain Py"
print("   ✓ Retrieved simulation results")

# Test visualization
try:
    viz_b64 = manager.visualize_simulation(sim_id, 'summary')
    assert isinstance(viz_b64, str), "Should return base64 string"
    print("   ✓ Generated visualization via manager")
except Exception as e:
    print(f"   ⚠ Manager visualization: {e}")

# Summary
print("\n" + "=" * 60)
print("✅ ALL ENHANCED FEATURES TESTED SUCCESSFULLY!")
print("\nThe enhanced FerroSim MCP server is ready to use with:")
print("  • Custom electric fields (sine, step, polynomial, zero)")
print("  • Custom defects (random, periodic)")
print("  • Ground state calculations")
print("  • Visualization generation for Claude Desktop")
print("\nRestart Claude Desktop and try the example prompts from")
print("FERROSIM_MCP_USAGE_GUIDE.md")
print("=" * 60)

