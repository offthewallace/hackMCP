"""
Mock AFM Data Generator
Creates synthetic "experimental" AFM data for testing theory-experiment matching
"""

import numpy as np
from ferrosim import Ferro2DSim
import json

def generate_mock_afm_domains(n=20, noise_level=0.05, save_path=None):
    """
    Generate mock AFM piezoresponse data showing domain structure
    
    Args:
        n: Lattice size
        noise_level: Amount of Gaussian noise to add
        save_path: Optional path to save data as JSON
    
    Returns:
        dict with amplitude, phase, and metadata
    """
    print(f"Generating mock AFM data (n={n}, noise={noise_level})...")
    
    # Create reference simulation with known parameters
    time_vec = np.linspace(0, 1.0, 500)
    applied_field = np.zeros((len(time_vec), 2))
    applied_field[:, 1] = 8 * np.sin(time_vec * 2 * np.pi)
    
    sim = Ferro2DSim(
        n=n,
        gamma=1.0,
        k=1.5,  # True coupling constant
        mode='tetragonal',
        dep_alpha=0.1,  # True depolarization
        time_vec=time_vec,
        appliedE=applied_field,
        init='pr'
    )
    
    # Run to equilibrium
    results = sim.runSim(calc_pr=False, verbose=False)
    
    # Get final polarization state
    pmat = sim.getPmat(timestep=-1)
    px = pmat[0, :, :]
    py = pmat[1, :, :]
    
    # Convert to AFM-like signals
    # Amplitude: related to polarization magnitude
    amplitude = np.sqrt(px**2 + py**2)
    
    # Phase: related to polarization direction
    phase = np.arctan2(py, px)
    
    # Add realistic noise
    amplitude += noise_level * np.random.randn(*amplitude.shape) * np.mean(amplitude)
    phase += 0.5 * noise_level * np.random.randn(*phase.shape)
    
    # Add some measurement artifacts
    # 1. Slight spatial drift
    x, y = np.meshgrid(np.arange(n), np.arange(n))
    drift = 0.02 * np.sin(2 * np.pi * x / n) * np.sin(2 * np.pi * y / n)
    amplitude += drift * np.mean(amplitude)
    
    # 2. Edge effects (common in AFM)
    edge_mask = np.ones((n, n))
    edge_mask[0, :] *= 0.8
    edge_mask[-1, :] *= 0.8
    edge_mask[:, 0] *= 0.8
    edge_mask[:, -1] *= 0.8
    amplitude *= edge_mask
    
    # Create metadata
    metadata = {
        'scan_size_nm': [100, 100],
        'resolution': [n, n],
        'measurement_type': 'piezoresponse',
        'true_parameters': {
            'k': 1.5,
            'dep_alpha': 0.1,
            'mode': 'tetragonal'
        },
        'noise_level': noise_level
    }
    
    data = {
        'amplitude': amplitude.tolist(),
        'phase': phase.tolist(),
        'metadata': metadata
    }
    
    if save_path:
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved mock AFM data to {save_path}")
    
    return data


def generate_mock_afm_with_defects(n=20, defect_strength=0.5, num_defects=5, noise_level=0.05):
    """
    Generate mock AFM data with point defects
    
    Args:
        n: Lattice size
        defect_strength: Strength of random field defects
        num_defects: Number of defects to add
        noise_level: Measurement noise
    """
    print(f"Generating mock AFM data with {num_defects} defects...")
    
    # Create defect list
    defects = [(0, 0) for _ in range(n*n)]
    
    # Add random defects
    np.random.seed(42)
    defect_indices = np.random.choice(n*n, num_defects, replace=False)
    for idx in defect_indices:
        # Random field in random direction
        angle = np.random.rand() * 2 * np.pi
        Ex = defect_strength * np.cos(angle)
        Ey = defect_strength * np.sin(angle)
        defects[idx] = (Ex, Ey)
    
    # Run simulation with defects
    time_vec = np.linspace(0, 1.0, 500)
    applied_field = np.zeros((len(time_vec), 2))
    applied_field[:, 1] = 8 * np.sin(time_vec * 2 * np.pi)
    
    sim = Ferro2DSim(
        n=n,
        gamma=1.0,
        k=1.0,
        mode='tetragonal',
        dep_alpha=0.05,
        defects=defects,
        time_vec=time_vec,
        appliedE=applied_field,
        init='pr'
    )
    
    results = sim.runSim(calc_pr=False, verbose=False)
    pmat = sim.getPmat(timestep=-1)
    
    px = pmat[0, :, :]
    py = pmat[1, :, :]
    amplitude = np.sqrt(px**2 + py**2)
    phase = np.arctan2(py, px)
    
    # Add noise
    amplitude += noise_level * np.random.randn(*amplitude.shape) * np.mean(amplitude)
    phase += 0.5 * noise_level * np.random.randn(*phase.shape)
    
    metadata = {
        'scan_size_nm': [100, 100],
        'resolution': [n, n],
        'measurement_type': 'piezoresponse',
        'true_parameters': {
            'k': 1.0,
            'dep_alpha': 0.05,
            'mode': 'tetragonal',
            'num_defects': num_defects,
            'defect_locations': defect_indices.tolist()
        },
        'noise_level': noise_level
    }
    
    return {
        'amplitude': amplitude.tolist(),
        'phase': phase.tolist(),
        'metadata': metadata
    }


def visualize_mock_afm(afm_data, save_path=None):
    """Visualize mock AFM data"""
    import matplotlib.pyplot as plt
    
    amplitude = np.array(afm_data['amplitude'])
    phase = np.array(afm_data['phase'])
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    im1 = axes[0].imshow(amplitude, cmap='viridis')
    axes[0].set_title('AFM Amplitude')
    plt.colorbar(im1, ax=axes[0])
    
    im2 = axes[1].imshow(phase, cmap='twilight')
    axes[1].set_title('AFM Phase')
    plt.colorbar(im2, ax=axes[1])
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved visualization to {save_path}")
    
    return fig


if __name__ == "__main__":
    # Generate different types of mock data
    
    # 1. Clean domain structure
    print("\n1. Generating clean domain structure...")
    afm_clean = generate_mock_afm_domains(
        n=20, 
        noise_level=0.03,
        save_path='mock_afm_clean.json'
    )
    fig = visualize_mock_afm(afm_clean, 'mock_afm_clean.png')
    
    # 2. Noisy data
    print("\n2. Generating noisy data...")
    afm_noisy = generate_mock_afm_domains(
        n=20,
        noise_level=0.15,
        save_path='mock_afm_noisy.json'
    )
    fig = visualize_mock_afm(afm_noisy, 'mock_afm_noisy.png')
    
    # 3. Data with defects
    print("\n3. Generating data with defects...")
    afm_defects = generate_mock_afm_with_defects(
        n=20,
        num_defects=8,
        defect_strength=0.3,
        noise_level=0.05
    )
    with open('mock_afm_defects.json', 'w') as f:
        json.dump(afm_defects, f, indent=2)
    fig = visualize_mock_afm(afm_defects, 'mock_afm_defects.png')
    
    print("\n✓ Generated all mock AFM datasets!")
    print("\nFiles created:")
    print("  - mock_afm_clean.json (+ .png)")
    print("  - mock_afm_noisy.json (+ .png)")
    print("  - mock_afm_defects.json (+ .png)")
