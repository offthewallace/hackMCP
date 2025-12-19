#!/usr/bin/env python3
"""
Test loading HDF5 AFM data (DTMicroscope format)
"""

from afm_digital_twin import AFMDigitalTwin
import numpy as np

print('='*70)
print('Loading HDF5 AFM Data (DTMicroscope format)')
print('='*70)

# Load H5 data
afm = AFMDigitalTwin()
result = afm.load_data('data/dset_spm1.h5')

print(f'\n✓ LOADED FILE')
print('-'*70)
print(f'Filepath: {result["filepath"]}')
print(f'Scan ID: {result["scan_id"]}')
print(f'Format: {result["format"]}')
print(f'Shape: {result["amplitude_shape"]}')
print(f'Data Type: {result["data_type"]}')
print(f'Amplitude Range: [{result["amplitude_range"][0]:.2e}, {result["amplitude_range"][1]:.2e}]')
print(f'Mean: {result["mean_amplitude"]:.2e}')
print(f'Std: {result["std_amplitude"]:.2e}')

# Analyze domains
print(f'\n{"="*70}')
print('DOMAIN STRUCTURE ANALYSIS')
print('='*70)
domains = afm.analyze_domain_structure()

print(f'\nDomain Pixel Counts:')
print(f'  Up domains: {domains["num_up_domains"]:,} pixels')
print(f'  Down domains: {domains["num_down_domains"]:,} pixels')

print(f'\nDomain Areas:')
print(f'  Up domain area: {domains["up_domain_area"]*1e12:.3f} μm²')
print(f'  Down domain area: {domains["down_domain_area"]*1e12:.3f} μm²')
print(f'  Total: {(domains["up_domain_area"] + domains["down_domain_area"])*1e12:.3f} μm²')

print(f'\nDomain Wall Statistics:')
print(f'  Wall density: {domains["domain_wall_density"]:.3f}')

print(f'\nAmplitude by Domain:')
print(f'  Mean amplitude (up): {domains["mean_amplitude_up"]:.2e}')
print(f'  Mean amplitude (down): {domains["mean_amplitude_down"]:.2e}')

# Get piezoresponse
print(f'\n{"="*70}')
print('PIEZORESPONSE DATA')
print('='*70)
pfm = afm.get_piezoresponse()
amp = np.array(pfm['amplitude'])
phase = np.array(pfm['phase'])

print(f'\nAmplitude Channel:')
print(f'  Shape: {amp.shape}')
print(f'  Range: [{amp.min():.2e}, {amp.max():.2e}]')
print(f'  Mean: {amp.mean():.2e}, Std: {amp.std():.2e}')

print(f'\nPhase Channel:')
print(f'  Shape: {phase.shape}')
print(f'  Range: [{phase.min():.2f}, {phase.max():.2f}]')
print(f'  Mean: {phase.mean():.2f}, Std: {phase.std():.2f}')

# Test DTMicroscope API
print(f'\n{"="*70}')
print('DTMICROSCOPE API COMPATIBILITY')
print('='*70)
array_list, shape, dtype = afm.get_scan(channels=['Amplitude', 'Phase'])
print(f'\n✓ get_scan() returned:')
print(f'  Shape: {shape}')
print(f'  Dtype: {dtype}')

# Test scanning emulator
print(f'\n✓ scanning_emulator():')
line_count = 0
for line_data in afm.scanning_emulator():
    line_count += 1
    if line_count <= 3:
        print(f'  Line {line_count}: Amplitude={len(line_data[0])} points, Phase={len(line_data[1])} points')
    if line_count >= 3:
        break

print(f'\n{"="*70}')
print('✅ HDF5 DATA SUCCESSFULLY LOADED AND ANALYZED')
print('='*70)
