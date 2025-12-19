# FerroSim MCP Server with Real AFM Data Integration

A Model Context Protocol (MCP) server integrating FerroSim ferroelectric simulations with real AFM experimental data analysis.

## References

This project builds upon:
- **DTMicroscope Digital Twin Framework**: [https://github.com/pycroscopy/DTMicroscope](https://github.com/pycroscopy/DTMicroscope/tree/main)
- **AFM Hackathon Colab Notebook**: [https://colab.research.google.com/drive/1yR698-_qoAKoiK6VRVbU5UFJUkV5tS_l](https://colab.research.google.com/drive/1yR698-_qoAKoiK6VRVbU5UFJUkV5tS_l)

## Features

### FerroSim Theory Side
- Create and run ferroelectric domain simulations
- Configure electric fields, defects, and material properties
- Visualize polarization dynamics
- Export simulation results

### AFM Experiment Side  
- **Load real AFM data** from multiple formats (.ibw, .h5, .npy, .mat, .txt)
- Analyze ferroelectric domain structures
- Extract domain areas, wall density, and statistics
- DTMicroscope-compatible API
- Line-by-line scanning emulator

### Theory-Experiment Matching
- Compare simulation results with AFM experimental data
- Calculate correlation, MSE, RMSE metrics
- Assess match quality

## Quick Start

### Installation

```bash
# Activate conda environment
source /Users/guanlinhe/miniconda3/bin/activate ferrosim_mcp

# Install dependencies
pip install mcp ferrosim git+https://github.com/ramav87/FerroSim.git@rama-dev
pip install igor2 scipy h5py numpy
```

### Usage

#### 1. Load Real AFM Data

```python
from afm_digital_twin import AFMDigitalTwin

# Initialize
afm = AFMDigitalTwin()

# Load data (format auto-detected from extension)
result = afm.load_data("AFM/temp/scan_0001.ibw")  # Igor format
# OR
result = afm.load_data("data/dset_spm1.h5")       # HDF5/USID format

print(f"Loaded scan: {result['scan_id']}")
print(f"Format: {result['format']}")
```

#### 2. Analyze Domains

```python
# Analyze domain structure
domains = afm.analyze_domain_structure()
print(f"Up domain area: {domains['up_domain_area']*1e12:.2f} μm²")
print(f"Down domain area: {domains['down_domain_area']*1e12:.2f} μm²")
print(f"Wall density: {domains['domain_wall_density']:.3f}")
```

#### 3. Run MCP Server

```bash
python ferrosim_mcp_server_minimal.py
```

## Supported File Formats

| Format | Extension | Description | Status |
|--------|-----------|-------------|--------|
| Igor Binary Wave | `.ibw` | PFM data from Igor Pro | ✅ Tested |
| HDF5/USID | `.h5`, `.hdf5` | DTMicroscope/sidpy format | ✅ Tested |
| NumPy | `.npy` | Binary NumPy arrays | ✅ Working |
| MATLAB | `.mat` | MATLAB data files | ✅ Working |
| Text | `.txt`, `.dat` | Plain text arrays | ✅ Working |

**Multi-channel support:** Automatically detects amplitude and phase channels in PFM data.

## API Reference

### AFMDigitalTwin

#### `load_data(filepath, data_format=None)`
Load real AFM scan data from file.

**Parameters:**
- `filepath` (str): Path to data file
- `data_format` (str, optional): Format ('ibw', 'h5', 'npy', 'mat', 'txt'). Auto-detected if None.

**Returns:** Dictionary with scan_id and metadata

#### `analyze_domain_structure(scan_id=None)`
Analyze ferroelectric domain structure.

**Returns:** Dictionary with:
- `num_up_domains`: Pixel count
- `num_down_domains`: Pixel count  
- `up_domain_area`: Area in m²
- `down_domain_area`: Area in m²
- `domain_wall_density`: Wall density metric
- `mean_amplitude_up/down`: Average amplitude by domain

#### `get_piezoresponse(scan_id=None)`
Get PFM amplitude and phase data.

**Returns:** Dictionary with amplitude and phase arrays

#### `get_scan(scan_id=None, channels=None)`
Get scan data (DTMicroscope-compatible API).

**Returns:** (array_list, shape, dtype) tuple

#### `scanning_emulator(scan_id=None, scanning_rate=10)`
Emulate line-by-line scanning.

**Yields:** Line data for each scan line

## MCP Tools

### AFM Tools

- `afm_load_real_scan`: Load real AFM data file
- `afm_analyze_domains`: Analyze domain structure  
- `afm_get_piezoresponse`: Get amplitude/phase data
- `afm_list_scans`: List all loaded scans
- `afm_get_scan`: Get scan data (DTMicroscope API)
- `afm_go_to`: Move probe to position
- `afm_get_position`: Get current probe position

### FerroSim Tools

- `initialize_simulation`: Create new simulation
- `run_simulation`: Execute simulation
- `get_simulation_results`: Retrieve results
- `visualize_simulation`: Generate plots
- `list_simulations`: List all simulations

### Theory-Experiment Matching

- `match_simulation_to_afm`: Compare simulation with AFM data

## Example Workflow

### Complete Analysis Pipeline

```python
from afm_digital_twin import AFMDigitalTwin
import numpy as np

# 1. Initialize and load data
afm = AFMDigitalTwin()
result = afm.load_data("AFM/temp/scan_0001.ibw")
scan_id = result['scan_id']

# 2. Analyze domains
domains = afm.analyze_domain_structure(scan_id)
print(f"Domain Analysis Results:")
print(f"  Up domain area: {domains['up_domain_area']*1e12:.3f} μm²")
print(f"  Down domain area: {domains['down_domain_area']*1e12:.3f} μm²")
print(f"  Wall density: {domains['domain_wall_density']:.3f}")

# 3. Get piezoresponse
pfm = afm.get_piezoresponse(scan_id)
amplitude = np.array(pfm['amplitude'])
phase = np.array(pfm['phase'])

# 4. Use DTMicroscope API
array_list, shape, dtype = afm.get_scan(scan_id, channels=['Amplitude', 'Phase'])
data = np.array(array_list, dtype=dtype).reshape(shape)

# 5. Emulate scanning
for line_idx, line_data in enumerate(afm.scanning_emulator(scan_id)):
    # Process line-by-line
    amplitude_line, phase_line = line_data
    # ... process data
    if line_idx >= 10:
        break
```

## Test Scripts

### `test_real_afm_workflow.py`
Comprehensive workflow test demonstrating:
- Data loading
- Domain analysis
- Piezoresponse extraction
- DTMicroscope API compatibility
- Scanning emulator

Run:
```bash
source /Users/guanlinhe/miniconda3/bin/activate ferrosim_mcp
python test_real_afm_workflow.py
```

## Data Directory Structure

```
AFM/
├── temp/
│   └── scan_0001.ibw          # Real experimental PFM data
├── 0_AFM_Basic_functionality_COLAB_Hackaton.ipynb
├── 1_AFM_Imperfect_Probe_COLAB_Hackaton.ipynb
└── ...
```

## Architecture

### Simplified Design

The system has been streamlined to focus on real data:

1. **No Synthetic Data Generation**: Removed all synthetic/mock data generation
2. **Real Data Only**: AFM Digital Twin only loads and serves experimental data
3. **DTMicroscope Compatibility**: Follows DTMicroscope API patterns
4. **Clean API**: Simplified tool set with essential functionality

### Core Components

```
ferrosim_mcp_server_minimal.py  # MCP server with FerroSim + AFM tools
afm_digital_twin.py             # Real AFM data loader and analyzer
```

## Configuration

### Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ferrosim-afm": {
      "command": "/Users/guanlinhe/miniconda3/envs/ferrosim_mcp/bin/python",
      "args": [
        "/Users/guanlinhe/github/hackMCP/ferrosim_mcp_server_minimal.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/guanlinhe/github/hackMCP"
      }
    }
  }
}
```

## Requirements

```
mcp>=0.1.0
numpy>=1.20.0
scipy>=1.7.0
igor2>=0.5.0
h5py>=3.0.0
ferrosim
```

## License

Research use only. See individual component licenses for details.

## Citation

If you use this code, please cite:
- FerroSim: [github.com/ramav87/FerroSim](https://github.com/ramav87/FerroSim)
- DTMicroscope: [github.com/pycroscopy/DTMicroscope](https://github.com/pycroscopy/DTMicroscope)
