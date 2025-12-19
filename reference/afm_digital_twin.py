#!/usr/bin/env python3
"""
DTMicroscope AFM Wrapper for MCP Integration
Wraps DTMicroscope notebook functionality for easy MCP access
"""

import numpy as np
from typing import Dict, Tuple, Optional

class AFMDigitalTwin:
    """
    Wrapper for DTMicroscope AFM capabilities
    Based on notebooks at: github.com/pycroscopy/DTMicroscope/tree/main/notebooks/AFM
    """
    
    def __init__(self, scan_size: Tuple[int, int] = (256, 256)):
        """
        Initialize AFM digital twin
        
        Args:
            scan_size: (width, height) in pixels
        """
        self.scan_size = scan_size
        self.scan_range = (1.0, 1.0)  # microns
        self.tip_radius = 20e-9  # 20 nm
        
        # Store scan results
        self.scans = {}
        
        # Try to import DTMicroscope
        try:
            from dtmicroscope import AFMSimulator
            self.simulator = AFMSimulator()
            self.dtm_available = True
        except ImportError:
            # Fallback: create synthetic data
            self.simulator = None
            self.dtm_available = False
            print("DTMicroscope not available - using synthetic data")
    
    def scan_ferroelectric_surface(
        self,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Simulate PFM scan of ferroelectric surface
        
        Args:
            params: Scan parameters
                - voltage: AC voltage (V)
                - frequency: AC frequency (kHz)
                - scan_rate: lines/second
        
        Returns:
            Dictionary with amplitude, phase, and metadata
        """
        if params is None:
            params = {}
        
        # Extract parameters
        voltage = params.get('voltage', 5.0)  # V
        frequency = params.get('frequency', 300)  # kHz
        scan_rate = params.get('scan_rate', 1.0)  # lines/s
        
        if self.dtm_available:
            # Use actual DTMicroscope
            scan_data = self.simulator.pfm_scan(
                size=self.scan_size,
                voltage=voltage,
                frequency=frequency
            )
            amplitude = scan_data['amplitude']
            phase = scan_data['phase']
        else:
            # Generate synthetic ferroelectric domain structure
            amplitude, phase = self._generate_synthetic_domains()
        
        # Generate scan ID
        import uuid
        scan_id = str(uuid.uuid4())[:8]
        
        # Store scan
        self.scans[scan_id] = {
            'amplitude': amplitude,
            'phase': phase,
            'params': {
                'voltage': voltage,
                'frequency': frequency,
                'scan_rate': scan_rate,
                'scan_size': self.scan_size,
                'scan_range': self.scan_range
            }
        }
        
        return {
            'scan_id': scan_id,
            'amplitude_shape': amplitude.shape,
            'phase_shape': phase.shape,
            'amplitude_range': [float(amplitude.min()), float(amplitude.max())],
            'phase_range': [float(phase.min()), float(phase.max())],
            'mean_amplitude': float(amplitude.mean()),
            'std_amplitude': float(amplitude.std())
        }
    
    def _generate_synthetic_domains(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic ferroelectric domain structure
        Mimics real PFM data
        """
        n = self.scan_size[0]
        
        # Create domain structure using Voronoi-like pattern
        num_domains = np.random.randint(5, 15)
        
        # Random domain centers
        centers = np.random.rand(num_domains, 2) * n
        
        # Create coordinate grids
        x, y = np.meshgrid(np.arange(n), np.arange(n))
        coords = np.stack([x, y], axis=-1)
        
        # Assign each pixel to nearest domain
        distances = np.zeros((n, n, num_domains))
        for i, center in enumerate(centers):
            distances[:, :, i] = np.sqrt(
                (coords[:, :, 0] - center[0])**2 + 
                (coords[:, :, 1] - center[1])**2
            )
        
        domain_map = np.argmin(distances, axis=-1)
        
        # Assign random polarization to each domain
        domain_polarizations = np.random.choice([-1, 1], size=num_domains)
        
        # Create phase map (0° or 180°)
        phase = np.zeros((n, n))
        for i, pol in enumerate(domain_polarizations):
            phase[domain_map == i] = 0 if pol > 0 else 180
        
        # Add phase variation within domains
        phase += np.random.normal(0, 5, (n, n))
        
        # Create amplitude map (related to polarization magnitude)
        # Base amplitude with domain walls having reduced amplitude
        amplitude = np.ones((n, n)) * 0.85
        
        # Add noise
        amplitude += np.random.normal(0, 0.05, (n, n))
        
        # Reduce amplitude at domain walls
        for i in range(n-1):
            for j in range(n-1):
                if domain_map[i, j] != domain_map[i+1, j] or \
                   domain_map[i, j] != domain_map[i, j+1]:
                    amplitude[i, j] *= 0.5
        
        # Smooth slightly
        from scipy.ndimage import gaussian_filter
        amplitude = gaussian_filter(amplitude, sigma=1.0)
        phase = gaussian_filter(phase, sigma=0.5)
        
        return amplitude, phase
    
    def get_piezoresponse(self, scan_id: str) -> Dict:
        """
        Get PFM amplitude and phase data
        
        Args:
            scan_id: Scan identifier
        
        Returns:
            Dictionary with amplitude and phase arrays
        """
        if scan_id not in self.scans:
            raise ValueError(f"Scan {scan_id} not found")
        
        scan = self.scans[scan_id]
        
        return {
            'scan_id': scan_id,
            'amplitude': scan['amplitude'].tolist(),
            'phase': scan['phase'].tolist(),
            'params': scan['params']
        }
    
    def analyze_domain_structure(self, scan_id: str) -> Dict:
        """
        Analyze ferroelectric domain structure from scan
        
        Args:
            scan_id: Scan identifier
        
        Returns:
            Domain statistics
        """
        if scan_id not in self.scans:
            raise ValueError(f"Scan {scan_id} not found")
        
        scan = self.scans[scan_id]
        phase = scan['phase']
        amplitude = scan['amplitude']
        
        # Identify domains by phase thresholding
        # 0-90° → up domains, 90-180° → down domains
        up_domains = (phase < 90)
        down_domains = (phase >= 90)
        
        # Calculate domain areas
        pixel_area = (self.scan_range[0] / self.scan_size[0]) * \
                     (self.scan_range[1] / self.scan_size[1])
        
        up_area = np.sum(up_domains) * pixel_area
        down_area = np.sum(down_domains) * pixel_area
        
        # Find domain walls (edges)
        from scipy.ndimage import sobel
        phase_edges = np.abs(sobel(phase))
        domain_walls = phase_edges > 20  # threshold
        
        wall_density = np.sum(domain_walls) / np.prod(self.scan_size)
        
        return {
            'scan_id': scan_id,
            'num_up_domains': int(np.sum(up_domains)),
            'num_down_domains': int(np.sum(down_domains)),
            'up_domain_area': float(up_area),  # μm²
            'down_domain_area': float(down_area),  # μm²
            'domain_wall_density': float(wall_density),
            'mean_amplitude_up': float(amplitude[up_domains].mean()),
            'mean_amplitude_down': float(amplitude[down_domains].mean())
        }
    
    def extract_hysteresis_loop(
        self,
        position: Optional[Tuple[int, int]] = None
    ) -> Dict:
        """
        Simulate local hysteresis loop measurement
        
        Args:
            position: (x, y) pixel position, or None for average
        
        Returns:
            E-P hysteresis loop data
        """
        # Voltage sweep
        voltages = np.linspace(-10, 10, 100)
        
        # Simulate switching behavior
        # Tanh-like switching curve
        Pr = 0.85  # Remnant polarization
        Ec = 3.0   # Coercive field
        
        polarization = Pr * np.tanh((voltages - Ec) / 2) + \
                       Pr * np.tanh((voltages + Ec) / 2)
        
        # Add hysteresis
        forward = polarization + 0.1 * np.sin(np.linspace(0, np.pi, 100))
        backward = polarization - 0.1 * np.sin(np.linspace(0, np.pi, 100))
        
        return {
            'field': voltages.tolist(),
            'polarization_forward': forward.tolist(),
            'polarization_backward': backward.tolist(),
            'coercive_field': float(Ec),
            'remnant_polarization': float(Pr)
        }
    
    def list_scans(self) -> Dict:
        """List all available scans"""
        return {
            'scans': [
                {
                    'scan_id': sid,
                    'amplitude_shape': self.scans[sid]['amplitude'].shape,
                    'params': self.scans[sid]['params']
                }
                for sid in self.scans.keys()
            ],
            'total_scans': len(self.scans)
        }


# ============================================================================
# Example usage
# ============================================================================

if __name__ == "__main__":
    print("Testing AFM Digital Twin")
    print("="*70)
    
    # Initialize
    afm = AFMDigitalTwin(scan_size=(128, 128))
    
    # Perform scan
    print("\n1. Performing PFM scan...")
    scan_result = afm.scan_ferroelectric_surface({
        'voltage': 5.0,
        'frequency': 300
    })
    
    scan_id = scan_result['scan_id']
    print(f"   Scan ID: {scan_id}")
    print(f"   Amplitude range: {scan_result['amplitude_range']}")
    print(f"   Mean amplitude: {scan_result['mean_amplitude']:.3f}")
    
    # Get piezoresponse
    print("\n2. Getting piezoresponse data...")
    pfm_data = afm.get_piezoresponse(scan_id)
    print(f"   Amplitude shape: {np.array(pfm_data['amplitude']).shape}")
    print(f"   Phase shape: {np.array(pfm_data['phase']).shape}")
    
    # Analyze domains
    print("\n3. Analyzing domain structure...")
    domain_stats = afm.analyze_domain_structure(scan_id)
    print(f"   Up domain area: {domain_stats['up_domain_area']:.3f} μm²")
    print(f"   Down domain area: {domain_stats['down_domain_area']:.3f} μm²")
    print(f"   Domain wall density: {domain_stats['domain_wall_density']:.3f}")
    
    # Extract hysteresis
    print("\n4. Extracting hysteresis loop...")
    hyst = afm.extract_hysteresis_loop()
    print(f"   Coercive field: {hyst['coercive_field']:.2f} V")
    print(f"   Remnant polarization: {hyst['remnant_polarization']:.2f}")
    
    # List scans
    print("\n5. Listing all scans...")
    scan_list = afm.list_scans()
    print(f"   Total scans: {scan_list['total_scans']}")
    
    print("\n" + "="*70)
    print("✅ AFM Digital Twin test completed!")
