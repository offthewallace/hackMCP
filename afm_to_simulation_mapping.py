#!/usr/bin/env python3
"""
AFM to FerroSim Parameter Mapping Guide
========================================

This module provides utilities to extract AFM scan metadata and
map it to appropriate FerroSim simulation parameters for
theory-experiment matching.
"""

import numpy as np
from typing import Dict, Tuple, Optional
from afm_digital_twin import AFMDigitalTwin


class AFMParameterMapper:
    """
    Maps AFM experimental parameters to FerroSim simulation parameters

    Key Mappings:
    -------------
    AFM Parameter          → FerroSim Parameter
    -------------------------------------------------
    Scan size (µm)        → Lattice constant (a₀)
    Image resolution      → Lattice size (n)
    Applied voltage (V)   → Electric field (kV/cm)
    Scan rate (Hz)        → Time evolution
    Material (BTO, PZT)   → mode, gamma, k
    """

    def __init__(self):
        self.afm = AFMDigitalTwin()

    def analyze_afm_scan(self, filepath: str, data_format: Optional[str] = None) -> Dict:
        """
        Load AFM scan and extract all relevant parameters

        Returns:
            Dictionary with AFM parameters and suggested simulation parameters
        """
        # Load AFM data
        result = self.afm.load_data(filepath, data_format)
        scan_id = result['scan_id']
        scan = self.afm.scans[scan_id]

        # Extract AFM parameters
        amplitude = scan['amplitude']
        phase = scan['phase']
        params = scan['params']

        # Get spatial dimensions
        x_range = params.get('x_range', [-2e-6, 2e-6])  # Default: 4 µm
        y_range = params.get('y_range', [-2e-6, 2e-6])

        x_size = x_range[1] - x_range[0]  # meters
        y_size = y_range[1] - y_range[0]

        # Get resolution
        n_pixels_x, n_pixels_y = amplitude.shape

        # Calculate pixel size (lattice constant)
        pixel_size_x = x_size / n_pixels_x  # meters
        pixel_size_y = y_size / n_pixels_y
        pixel_size_avg = (pixel_size_x + pixel_size_y) / 2

        # Extract material parameters if available
        material = params.get('Material', 'Unknown')
        voltage = params.get('DriveAmplitude', None)  # Volts
        frequency = params.get('DriveFrequency', None)  # Hz

        # Calculate derived parameters
        analysis = {
            # AFM Parameters
            'afm': {
                'filepath': filepath,
                'scan_id': scan_id,
                'resolution': (n_pixels_x, n_pixels_y),
                'scan_size_x_um': x_size * 1e6,  # Convert to µm
                'scan_size_y_um': y_size * 1e6,
                'pixel_size_nm': pixel_size_avg * 1e9,  # Convert to nm
                'material': material,
                'drive_voltage_V': voltage,
                'drive_frequency_Hz': frequency,
                'amplitude_range': [float(amplitude.min()), float(amplitude.max())],
                'phase_range': [float(phase.min()), float(phase.max())],
            },

            # Suggested Simulation Parameters
            'simulation': self._suggest_simulation_params(
                pixel_size_avg, n_pixels_x, n_pixels_y,
                voltage, material
            )
        }

        return analysis

    def _suggest_simulation_params(
        self,
        pixel_size: float,  # meters
        n_pixels_x: int,
        n_pixels_y: int,
        voltage: Optional[float],
        material: str
    ) -> Dict:
        """
        Suggest FerroSim parameters based on AFM scan metadata

        Strategy:
        ---------
        1. Lattice size (n): Match AFM resolution or downsample
        2. Lattice constant: Match pixel size
        3. Electric field: Scale from applied voltage
        4. Material parameters: Use literature values
        """

        # ============================================================
        # 1. LATTICE SIZE MAPPING
        # ============================================================
        # AFM scans are typically 128×128, 256×256, 512×512
        # FerroSim is computationally intensive - suggest smaller n

        resolution = max(n_pixels_x, n_pixels_y)

        if resolution >= 256:
            suggested_n = 64  # Downsample for speed
        elif resolution >= 128:
            suggested_n = 32
        elif resolution >= 64:
            suggested_n = resolution  # Match exactly
        else:
            suggested_n = resolution

        # ============================================================
        # 2. SPATIAL SCALE MAPPING
        # ============================================================
        # FerroSim uses dimensionless units scaled by lattice constant a₀
        # Typical ferroelectric lattice constant: 3-4 Å (0.3-0.4 nm)

        # Physical lattice constant for common ferroelectrics:
        lattice_constants = {
            'BaTiO3': 4.0e-10,   # 4 Å
            'PbTiO3': 3.97e-10,  # 3.97 Å
            'PZT': 4.0e-10,      # ~4 Å
            'BiFeO3': 3.96e-10,  # 3.96 Å
        }

        # Determine material from metadata or use default
        a0 = lattice_constants.get(material, 4.0e-10)  # Default: 4 Å

        # Number of unit cells per AFM pixel
        unit_cells_per_pixel = pixel_size / a0

        # ============================================================
        # 3. ELECTRIC FIELD MAPPING
        # ============================================================
        # AFM voltage → Electric field in simulation
        # E = V / (film_thickness)
        # Typical PFM: 1-10 V AC, film thickness 100-500 nm

        if voltage is not None:
            # Assume film thickness of 200 nm (typical)
            film_thickness = 200e-9  # meters
            E_field_V_per_m = voltage / film_thickness
            E_field_kV_per_cm = E_field_V_per_m / 1e5  # Convert to kV/cm

            # Map to FerroSim amplitude (dimensionless, typically 0.1-100)
            # Scale: 100 kV/cm → amplitude ~10
            field_amplitude_y = E_field_kV_per_cm / 10.0
        else:
            # Default: moderate field
            E_field_kV_per_cm = 50.0
            field_amplitude_y = 5.0

        # ============================================================
        # 4. MATERIAL PARAMETERS
        # ============================================================
        # gamma: Kinetic coefficient (domain wall mobility)
        # k: Coupling constant (nearest neighbor interaction)
        # mode: Crystal structure

        material_params = {
            'BaTiO3': {'mode': 'tetragonal', 'gamma': 1.0, 'k': 1.0},
            'PbTiO3': {'mode': 'tetragonal', 'gamma': 1.2, 'k': 1.2},
            'PZT': {'mode': 'tetragonal', 'gamma': 1.0, 'k': 1.0},
            'BiFeO3': {'mode': 'rhombohedral', 'gamma': 0.8, 'k': 0.9},
        }

        mat_params = material_params.get(
            material,
            {'mode': 'tetragonal', 'gamma': 1.0, 'k': 1.0}
        )

        # ============================================================
        # 5. TIME EVOLUTION
        # ============================================================
        # Map scan rate to simulation time
        # Typical AFM scan: 0.5-2 Hz (0.5-2 seconds per frame)
        # Simulation time should capture domain dynamics (0.1-10 time units)

        t_end = 1.0  # Dimensionless time units
        n_steps = 1000  # Time resolution

        # ============================================================
        # RETURN SUGGESTED PARAMETERS
        # ============================================================
        return {
            # Core parameters
            'n': suggested_n,
            'gamma': mat_params['gamma'],
            'k': mat_params['k'],
            'mode': mat_params['mode'],
            'dep_alpha': 0.0,  # Depolarization (0 = disabled)
            'init': 'random',  # Initial state: 'random', 'pr', 'up', 'down'

            # Time parameters
            't_start': 0.0,
            't_end': t_end,
            'n_steps': n_steps,

            # Electric field
            'field_config': {
                'type': 'sine',  # 'sine', 'step', 'polynomial', 'zero'
                'params': {
                    'amplitude_x': 0.0,
                    'amplitude_y': field_amplitude_y,
                    'freq_x': 1.0,
                    'freq_y': 2.0,  # Typical PFM frequency
                    'phase': 0.0
                }
            },

            # Defects (optional)
            'defect_config': {
                'type': 'none',  # 'none', 'random', 'periodic'
                'params': {}
            },

            # Scaling information
            'scaling': {
                'lattice_constant_m': a0,
                'unit_cells_per_pixel': unit_cells_per_pixel,
                'physical_scan_size_m': pixel_size * suggested_n,
                'E_field_kV_per_cm': E_field_kV_per_cm,
                'note': f'Simulation {suggested_n}×{suggested_n} represents {pixel_size*suggested_n*1e9:.1f} nm physical size'
            }
        }

    def create_matched_simulation(self, filepath: str) -> Tuple[str, Dict]:
        """
        Convenience function: Analyze AFM scan and return ready-to-use simulation parameters

        Returns:
            (scan_id, simulation_params)
        """
        analysis = self.analyze_afm_scan(filepath)

        print("=" * 70)
        print("AFM SCAN ANALYSIS")
        print("=" * 70)
        print(f"\nAFM Parameters:")
        print(f"  Resolution: {analysis['afm']['resolution']}")
        print(f"  Scan size: {analysis['afm']['scan_size_x_um']:.2f} × {analysis['afm']['scan_size_y_um']:.2f} µm")
        print(f"  Pixel size: {analysis['afm']['pixel_size_nm']:.2f} nm")
        print(f"  Material: {analysis['afm']['material']}")
        if analysis['afm']['drive_voltage_V']:
            print(f"  Drive voltage: {analysis['afm']['drive_voltage_V']:.2f} V")

        print(f"\nSuggested Simulation Parameters:")
        sim = analysis['simulation']
        print(f"  Lattice size (n): {sim['n']}")
        print(f"  Material mode: {sim['mode']}")
        print(f"  γ (gamma): {sim['gamma']}")
        print(f"  k (coupling): {sim['k']}")
        print(f"  Electric field amplitude: {sim['field_config']['params']['amplitude_y']:.2f}")
        print(f"  Time steps: {sim['n_steps']}")

        print(f"\nPhysical Scaling:")
        print(f"  {sim['scaling']['note']}")
        print(f"  Lattice constant: {sim['scaling']['lattice_constant_m']*1e10:.2f} Å")
        print(f"  Unit cells per AFM pixel: {sim['scaling']['unit_cells_per_pixel']:.0f}")
        print(f"  E-field: {sim['scaling']['E_field_kV_per_cm']:.1f} kV/cm")
        print("=" * 70)

        return analysis['afm']['scan_id'], sim


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Create mapper
    mapper = AFMParameterMapper()

    # Analyze AFM scan and get simulation parameters
    afm_file = "AFM/temp/scan_0001.ibw"

    try:
        scan_id, sim_params = mapper.create_matched_simulation(afm_file)

        print("\n\nReady to use with MCP:")
        print("-" * 70)
        print("# Step 1: Load AFM data")
        print(f'scan_id = afm_load_real_scan(filepath="{afm_file}")["scan_id"]')
        print(f'# scan_id = "{scan_id}"')

        print("\n# Step 2: Create matched simulation")
        print(f"sim_id = initialize_simulation(**{sim_params})")

        print("\n# Step 3: Run simulation")
        print("run_simulation(sim_id=sim_id)")

        print("\n# Step 4: Match with experiment")
        print('match_simulation_to_afm(sim_id=sim_id, scan_id=scan_id, component="magnitude")')

    except FileNotFoundError:
        print(f"Test file not found: {afm_file}")
        print("\nTo use this script, provide a valid AFM data file path.")
