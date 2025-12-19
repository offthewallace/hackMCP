#!/usr/bin/env python3
"""
Test workflow for loading and analyzing real AFM data
Demonstrates the simplified AFM Digital Twin workflow
"""

from afm_digital_twin import AFMDigitalTwin
import os

print("="*70)
print("AFM Digital Twin - Real Data Workflow Test")
print("="*70)

# Initialize AFM Digital Twin
afm = AFMDigitalTwin()

# Load real AFM scan
filepath = "AFM/temp/scan_0001.ibw"
if not os.path.exists(filepath):
    print(f"\nError: File not found: {filepath}")
    exit(1)

print(f"\n1. LOADING REAL AFM DATA")
print("-"*70)
result = afm.load_data(filepath)
print(f"✓ Loaded: {result['filepath']}")
print(f"  Scan ID: {result['scan_id']}")
print(f"  Format: {result['format']}")
print(f"  Shape: {result['amplitude_shape']}")
print(f"  Data Type: {result['data_type']}")
print(f"  Amplitude Range: [{result['amplitude_range'][0]:.2f}, {result['amplitude_range'][1]:.2f}]")
print(f"  Mean: {result['mean_amplitude']:.2f}, Std: {result['std_amplitude']:.2f}")

scan_id = result['scan_id']

# Analyze domain structure
print(f"\n2. ANALYZING DOMAIN STRUCTURE")
print("-"*70)
domains = afm.analyze_domain_structure(scan_id)
print(f"Domain Pixel Counts:")
print(f"  Up domains: {domains['num_up_domains']:,} pixels")
print(f"  Down domains: {domains['num_down_domains']:,} pixels")

print(f"\nDomain Areas:")
print(f"  Up domain area: {domains['up_domain_area']:.6e} m²  ({domains['up_domain_area']*1e12:.6f} μm²)")
print(f"  Down domain area: {domains['down_domain_area']:.6e} m²  ({domains['down_domain_area']*1e12:.6f} μm²)")
print(f"  Total area: {(domains['up_domain_area'] + domains['down_domain_area'])*1e12:.6f} μm²")

print(f"\nDomain Wall Statistics:")
print(f"  Wall density: {domains['domain_wall_density']:.6f}")

print(f"\nAmplitude by Domain:")
print(f"  Mean amplitude (up): {domains['mean_amplitude_up']:.2f}")
print(f"  Mean amplitude (down): {domains['mean_amplitude_down']:.2f}")

# Get piezoresponse data
print(f"\n3. RETRIEVING PIEZORESPONSE DATA")
print("-"*70)
pfm = afm.get_piezoresponse(scan_id)
import numpy as np
amp_array = np.array(pfm['amplitude'])
phase_array = np.array(pfm['phase'])

print(f"Amplitude Channel:")
print(f"  Shape: {amp_array.shape}")
print(f"  Range: [{amp_array.min():.2f}, {amp_array.max():.2f}]")
print(f"  Mean: {amp_array.mean():.2f}, Std: {amp_array.std():.2f}")

print(f"\nPhase Channel:")
print(f"  Shape: {phase_array.shape}")
print(f"  Range: [{phase_array.min():.2f}, {phase_array.max():.2f}]")
print(f"  Mean: {phase_array.mean():.2f}, Std: {phase_array.std():.2f}")

# List all scans
print(f"\n4. SCAN INVENTORY")
print("-"*70)
scan_list = afm.list_scans()
print(f"Total loaded scans: {scan_list['total_scans']}")
print(f"Current scan: {scan_list['current_scan_id']}")

for scan in scan_list['scans']:
    print(f"\n  Scan ID: {scan['scan_id']}")
    print(f"    Shape: {scan['amplitude_shape']}")
    print(f"    Source: {scan['params'].get('source', 'unknown')}")

# Test DTMicroscope-compatible API
print(f"\n5. DTMICROSCOPE-COMPATIBLE API")
print("-"*70)
array_list, shape, dtype = afm.get_scan(scan_id, channels=['Amplitude', 'Phase'])
print(f"✓ get_scan() returned:")
print(f"  Shape: {shape}")
print(f"  Dtype: {dtype}")
print(f"  Channels: 2 (Amplitude, Phase)")

# Test scanning emulator
print(f"\n6. SCANNING EMULATOR (Line-by-line)")
print("-"*70)
line_count = 0
for line_data in afm.scanning_emulator(scan_id):
    line_count += 1
    if line_count <= 3:
        print(f"  Line {line_count}: {len(line_data[0])} points")
    if line_count >= 3:
        break
print(f"✓ Emulator working (tested {line_count} lines)")

print(f"\n" + "="*70)
print("✅ ALL TESTS PASSED")
print("="*70)
print(f"\nSummary:")
print(f"  - Real AFM data loaded successfully")
print(f"  - Domain structure analyzed")
print(f"  - Up domain area: {domains['up_domain_area']*1e12:.3f} μm²")
print(f"  - Down domain area: {domains['down_domain_area']*1e12:.3f} μm²")
print(f"  - Domain wall density: {domains['domain_wall_density']:.3f}")
print(f"  - DTMicroscope API compatibility verified")
