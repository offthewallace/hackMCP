#!/usr/bin/env python3
"""
AFM Digital Twin - Real Data Loader
Simplified version that only loads and serves real AFM experimental data
Based on DTMicroscope workflow
"""

import numpy as np
from typing import Dict, Tuple, Optional, List
import uuid
import os


class AFMDigitalTwin:
    """
    AFM Digital Twin for loading and analyzing real experimental AFM data
    Supports .ibw (Igor), .h5 (USID format), .npy, and .mat files
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize AFM digital twin
        
        Args:
            data_path: Path to AFM data file (optional, can load later)
        """
        # Store loaded scans
        self.scans = {}
        self.current_scan_id = None
        self.data_path = data_path
        
        # Scan parameters (will be set when data is loaded)
        self.scan_size = None
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None
        
        # Probe position
        self.x = 0.0
        self.y = 0.0
        
        # Auto-load if path provided
        if data_path and os.path.exists(data_path):
            self.load_data(data_path)
    
    def initialize_microscope(self, microscope_type: str = "AFM", data_path: Optional[str] = None):
        """
        Initialize microscope with data file (matches DTMicroscope API)
        
        Args:
            microscope_type: Type of microscope (usually "AFM")
            data_path: Path to dataset file
        """
        if data_path:
            self.data_path = data_path
            if os.path.exists(data_path):
                self.load_data(data_path)
            else:
                print(f"Warning: Data file not found: {data_path}")
    
    def setup_microscope(self, data_source: Optional[str] = None):
        """
        Setup microscope with specific data source/channel
        
        Args:
            data_source: Dataset identifier or channel name
        """
        if self.current_scan_id and data_source:
            # Store metadata about data source
            if self.current_scan_id in self.scans:
                self.scans[self.current_scan_id]['params']['data_source'] = data_source
    
    def load_data(self, filepath: str, data_format: Optional[str] = None) -> Dict:
        """
        Load real AFM scan data from file
        
        Args:
            filepath: Path to AFM data file
            data_format: File format ('ibw', 'h5', 'npy', 'mat', 'txt')
                        If None, auto-detect from extension
        
        Returns:
            Dictionary with scan_id and metadata
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"AFM file not found: {filepath}")
        
        # Auto-detect format from extension if not specified
        if data_format is None:
            ext = os.path.splitext(filepath)[1].lower()
            format_map = {
                '.ibw': 'ibw',
                '.h5': 'h5',
                '.hdf5': 'h5',
                '.npy': 'npy',
                '.mat': 'mat',
                '.txt': 'txt',
                '.dat': 'txt'
            }
            data_format = format_map.get(ext, 'ibw')
        
        # Load based on format
        if data_format == 'ibw':
            amplitude, phase, metadata = self._load_ibw(filepath)
        elif data_format == 'h5':
            amplitude, phase, metadata = self._load_h5(filepath)
        elif data_format == 'npy':
            amplitude, phase, metadata = self._load_npy(filepath)
        elif data_format == 'mat':
            amplitude, phase, metadata = self._load_mat(filepath)
        elif data_format == 'txt':
            amplitude, phase, metadata = self._load_txt(filepath)
        else:
            raise ValueError(f"Unsupported format: {data_format}")
        
        # Generate scan ID
        scan_id = str(uuid.uuid4())[:8]
        
        # Set scan size from loaded data
        self.scan_size = amplitude.shape
        
        # Set default scan range if not in metadata
        if 'x_range' in metadata:
            self.x_min, self.x_max = metadata['x_range']
        else:
            self.x_min, self.x_max = -2e-6, 2e-6
        
        if 'y_range' in metadata:
            self.y_min, self.y_max = metadata['y_range']
        else:
            self.y_min, self.y_max = -2e-6, 2e-6
        
        # Store scan
        self.scans[scan_id] = {
            'amplitude': amplitude,
            'phase': phase,
            'params': {
                'source': 'real_afm_file',
                'filepath': filepath,
                'format': data_format,
                'scan_size': amplitude.shape,
                'data_type': 'experimental',
                'x_range': [self.x_min, self.x_max],
                'y_range': [self.y_min, self.y_max],
                **metadata
            }
        }
        
        self.current_scan_id = scan_id
        
        return {
            'scan_id': scan_id,
            'source': 'real_file',
            'filepath': filepath,
            'format': data_format,
            'amplitude_shape': amplitude.shape,
            'amplitude_range': [float(amplitude.min()), float(amplitude.max())],
            'mean_amplitude': float(amplitude.mean()),
            'std_amplitude': float(amplitude.std()),
            'data_type': 'experimental'
        }
    
    def _load_ibw(self, filepath: str) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Load Igor Binary Wave (.ibw) file"""
        try:
            import igor2.binarywave as bw
        except ImportError:
            raise ImportError("Install igor2 package: pip install igor2")
        
        data = bw.load(filepath)
        wData = data['wave']['wData']
        
        # Handle multi-channel data
        if wData.ndim == 3:
            # Identify amplitude and phase channels by value ranges
            amplitude_idx, phase_idx = self._identify_pfm_channels(wData)
            amplitude = wData[:, :, amplitude_idx]
            phase = wData[:, :, phase_idx] if phase_idx is not None else np.zeros_like(amplitude)
        elif wData.ndim == 2:
            amplitude = wData
            phase = np.zeros_like(amplitude)
        else:
            raise ValueError(f"Unexpected data dimensions: {wData.shape}")
        
        # Extract metadata from note
        metadata = {}
        if 'note' in data['wave']:
            note = data['wave']['note']
            if isinstance(note, bytes):
                note = note.decode('utf-8', errors='ignore')
            metadata = self._parse_igor_note(note)
        
        return amplitude, phase, metadata
    
    def _load_h5(self, filepath: str) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Load HDF5/USID format file (DTMicroscope format)"""
        try:
            import h5py
        except ImportError:
            raise ImportError("Install h5py: pip install h5py")
        
        with h5py.File(filepath, 'r') as f:
            # USID/sidpy format: Measurement_000/Channel_XXX/generic/generic
            # Typically: Channel_005 = amplitude, Channel_003/004 = phase
            
            amplitude = None
            phase = None
            metadata = {}
            
            # Collect all channel datasets
            channels = []
            for i in range(20):  # Check up to 20 channels
                channel_path = f'Measurement_000/Channel_{i:03d}/generic/generic'
                if channel_path in f:
                    data = f[channel_path][()]
                    if data.ndim == 2:  # Only 2D scan data
                        channels.append((i, data))
            
            if not channels:
                # Fallback: search for any 2D datasets
                def find_2d_datasets(name, obj):
                    if isinstance(obj, h5py.Dataset) and obj.ndim == 2:
                        channels.append((name, obj[()]))
                
                f.visititems(find_2d_datasets)
            
            if not channels:
                raise ValueError("No 2D scan data found in H5 file")
            
            # Identify amplitude and phase by data ranges
            for idx, data in channels:
                data_min, data_max = data.min(), data.max()
                data_range = data_max - data_min
                
                # Phase: angular range (typically -90 to 270 or 0 to 360)
                if 100 < data_range < 500 and -200 < data_min < 300:
                    if phase is None:
                        phase = data
                        metadata['phase_channel'] = idx
                
                # Amplitude: large values or large range
                elif data_range > 1000 or data_max > 1000:
                    if amplitude is None:
                        amplitude = data
                        metadata['amplitude_channel'] = idx
            
            # Fallback: use first two channels
            if amplitude is None and channels:
                amplitude = channels[0][1]
            
            if phase is None:
                phase = np.zeros_like(amplitude)
            
            # Try to extract spatial calibration
            try:
                x_path = f'Measurement_000/Channel_000/generic/x'
                y_path = f'Measurement_000/Channel_000/generic/y'
                if x_path in f and y_path in f:
                    x_vals = f[x_path][()]
                    y_vals = f[y_path][()]
                    metadata['x_range'] = [float(x_vals.min()), float(x_vals.max())]
                    metadata['y_range'] = [float(y_vals.min()), float(y_vals.max())]
            except:
                pass
        
        return amplitude, phase, metadata
    
    def _load_npy(self, filepath: str) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Load NumPy array file"""
        amplitude = np.load(filepath)
        
        # Ensure 2D
        if amplitude.ndim > 2:
            amplitude = amplitude[0, :, :] if amplitude.shape[0] < 10 else amplitude[:, :, 0]
        
        phase = np.zeros_like(amplitude)
        return amplitude, phase, {}
    
    def _load_mat(self, filepath: str) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Load MATLAB .mat file"""
        try:
            from scipy.io import loadmat
        except ImportError:
            raise ImportError("Install scipy: pip install scipy")
        
        data = loadmat(filepath)
        
        # Find amplitude and phase
        amplitude = None
        phase = None
        
        for key in data.keys():
            if not key.startswith('__'):
                if 'amplitude' in key.lower() or 'height' in key.lower():
                    amplitude = data[key]
                elif 'phase' in key.lower():
                    phase = data[key]
        
        if amplitude is None:
            # Use first non-metadata variable
            for key in data.keys():
                if not key.startswith('__'):
                    amplitude = data[key]
                    break
        
        if amplitude is None:
            raise ValueError("No data found in MAT file")
        
        # Ensure 2D
        if amplitude.ndim > 2:
            amplitude = amplitude[:, :, 0]
        
        if phase is None:
            phase = np.zeros_like(amplitude)
        
        return amplitude, phase, {}
    
    def _load_txt(self, filepath: str) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Load text file"""
        amplitude = np.loadtxt(filepath)
        phase = np.zeros_like(amplitude)
        return amplitude, phase, {}
    
    def _identify_pfm_channels(self, wData: np.ndarray) -> Tuple[int, Optional[int]]:
        """
        Identify amplitude and phase channels in multi-channel PFM data
        
        Returns:
            (amplitude_idx, phase_idx)
        """
        n_channels = wData.shape[2]
        
        amplitude_candidates = []
        phase_candidates = []
        
        for i in range(n_channels):
            channel = wData[:, :, i]
            ch_min, ch_max = channel.min(), channel.max()
            ch_range = ch_max - ch_min
            
            # Phase typically in range -180 to 180 or 0 to 360
            if 100 < ch_range < 500 and -200 < ch_min < 200:
                phase_candidates.append((i, ch_range))
            # Amplitude typically larger values
            elif ch_range > 1000 or ch_max > 1000:
                amplitude_candidates.append((i, ch_range))
        
        # Select best candidates
        if amplitude_candidates:
            amp_idx = max(amplitude_candidates, key=lambda x: x[1])[0]
        else:
            # Fallback: channel with largest range
            ranges = [(i, wData[:, :, i].max() - wData[:, :, i].min()) for i in range(n_channels)]
            amp_idx = max(ranges, key=lambda x: x[1])[0]
        
        phase_idx = phase_candidates[0][0] if phase_candidates else None
        
        return amp_idx, phase_idx
    
    def _parse_igor_note(self, note: str) -> Dict:
        """Parse Igor note string to extract metadata"""
        metadata = {}
        lines = note.split('\r')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                try:
                    # Try to convert to number
                    if 'e' in value.lower() or '.' in value:
                        metadata[key] = float(value)
                    else:
                        metadata[key] = int(value)
                except:
                    metadata[key] = value
        
        # Extract scan range if available
        if 'ScanSize' in metadata:
            scan_size = metadata['ScanSize']
            metadata['x_range'] = [-scan_size/2, scan_size/2]
            metadata['y_range'] = [-scan_size/2, scan_size/2]
        
        return metadata
    
    def get_scan(self, scan_id: Optional[str] = None, channels: Optional[List[str]] = None) -> Tuple[List, Tuple, str]:
        """
        Get scan data (matches DTMicroscope API)
        
        Args:
            scan_id: Scan identifier (uses current if None)
            channels: Channel names (e.g., ['Amplitude', 'Phase'])
        
        Returns:
            (array_list, shape, dtype)
        """
        if scan_id is None:
            scan_id = self.current_scan_id
        
        if scan_id not in self.scans:
            raise ValueError(f"Scan {scan_id} not found")
        
        scan = self.scans[scan_id]
        amplitude = scan['amplitude']
        phase = scan['phase']
        
        if channels is None:
            channels = ['Amplitude', 'Phase']
        
        # Build data array
        data_arrays = []
        for channel in channels:
            if 'amplitude' in channel.lower() or 'height' in channel.lower():
                data_arrays.append(amplitude.flatten().tolist())
            elif 'phase' in channel.lower():
                data_arrays.append(phase.flatten().tolist())
            else:
                # Unknown channel - return zeros
                data_arrays.append(np.zeros_like(amplitude).flatten().tolist())
        
        shape = (len(channels),) + amplitude.shape
        dtype = 'float64'
        
        return (data_arrays, shape, dtype)
    
    def scanning_emulator(self, scan_id: Optional[str] = None, scanning_rate: float = 10):
        """
        Emulate line-by-line scanning (matches DTMicroscope API)
        
        Args:
            scan_id: Scan identifier
            scanning_rate: Lines per second (not used in emulation)
        
        Yields:
            Line data for each scan line
        """
        if scan_id is None:
            scan_id = self.current_scan_id
        
        if scan_id not in self.scans:
            raise ValueError(f"Scan {scan_id} not found")
        
        scan = self.scans[scan_id]
        amplitude = scan['amplitude']
        phase = scan['phase']
        
        for line_idx in range(amplitude.shape[0]):
            line_data = [
                amplitude[line_idx, :].tolist(),
                phase[line_idx, :].tolist()
            ]
            yield line_data
    
    def get_piezoresponse(self, scan_id: Optional[str] = None) -> Dict:
        """Get PFM amplitude and phase data"""
        if scan_id is None:
            scan_id = self.current_scan_id
        
        if scan_id not in self.scans:
            raise ValueError(f"Scan {scan_id} not found")
        
        scan = self.scans[scan_id]
        
        return {
            'scan_id': scan_id,
            'amplitude': scan['amplitude'].tolist(),
            'phase': scan['phase'].tolist(),
            'params': scan['params']
        }
    
    def analyze_domain_structure(self, scan_id: Optional[str] = None) -> Dict:
        """Analyze ferroelectric domain structure from scan"""
        if scan_id is None:
            scan_id = self.current_scan_id
        
        if scan_id not in self.scans:
            raise ValueError(f"Scan {scan_id} not found")
        
        scan = self.scans[scan_id]
        phase = scan['phase']
        amplitude = scan['amplitude']
        
        # Identify domains by phase thresholding
        up_domains = (phase < 90)
        down_domains = (phase >= 90)
        
        # Calculate domain areas
        x_range = self.x_max - self.x_min if self.x_max and self.x_min else 4e-6
        y_range = self.y_max - self.y_min if self.y_max and self.y_min else 4e-6
        pixel_area = (x_range / self.scan_size[0]) * (y_range / self.scan_size[1])
        
        up_area = np.sum(up_domains) * pixel_area
        down_area = np.sum(down_domains) * pixel_area
        
        # Find domain walls
        from scipy.ndimage import sobel
        phase_edges = np.abs(sobel(phase))
        domain_walls = phase_edges > 20
        wall_density = np.sum(domain_walls) / np.prod(self.scan_size)
        
        return {
            'scan_id': scan_id,
            'num_up_domains': int(np.sum(up_domains)),
            'num_down_domains': int(np.sum(down_domains)),
            'up_domain_area': float(up_area),
            'down_domain_area': float(down_area),
            'domain_wall_density': float(wall_density),
            'mean_amplitude_up': float(amplitude[up_domains].mean()) if np.any(up_domains) else 0.0,
            'mean_amplitude_down': float(amplitude[down_domains].mean()) if np.any(down_domains) else 0.0
        }
    
    def go_to(self, x: float, y: float):
        """Move probe to position"""
        self.x = x
        self.y = y
    
    def get_position(self) -> Dict:
        """Get current probe position"""
        return {
            'x': self.x,
            'y': self.y,
            'x_range': [self.x_min, self.x_max] if self.x_min and self.x_max else None,
            'y_range': [self.y_min, self.y_max] if self.y_min and self.y_max else None
        }
    
    def list_scans(self) -> Dict:
        """List all loaded scans"""
        return {
            'scans': [
                {
                    'scan_id': sid,
                    'amplitude_shape': self.scans[sid]['amplitude'].shape,
                    'params': self.scans[sid]['params']
                }
                for sid in self.scans.keys()
            ],
            'total_scans': len(self.scans),
            'current_scan_id': self.current_scan_id
        }


if __name__ == "__main__":
    print("AFM Digital Twin - Real Data Loader")
    print("="*70)
    
    # Example: Load IBW file
    afm = AFMDigitalTwin()
    
    test_file = "AFM/temp/scan_0001.ibw"
    if os.path.exists(test_file):
        print(f"\nLoading: {test_file}")
        result = afm.load_data(test_file)
        print(f"Scan ID: {result['scan_id']}")
        print(f"Shape: {result['amplitude_shape']}")
        print(f"Range: {result['amplitude_range']}")
        
        # Analyze
        domains = afm.analyze_domain_structure()
        print(f"\nDomain Analysis:")
        print(f"Up domain area: {domains['up_domain_area']:.3e} m²")
        print(f"Down domain area: {domains['down_domain_area']:.3e} m²")
        print(f"Wall density: {domains['domain_wall_density']:.3f}")
    else:
        print(f"Test file not found: {test_file}")
