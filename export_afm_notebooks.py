#!/usr/bin/env python3
"""
Export AFM Jupyter Notebooks to Python Scripts
Converts all .ipynb files in AFM/ folder to .py files
"""

import os
import json
import sys
from pathlib import Path

def extract_code_cells(notebook_path):
    """
    Extract code cells from a Jupyter notebook
    
    Args:
        notebook_path: Path to .ipynb file
        
    Returns:
        List of code cell contents
    """
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        code_cells = []
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                # Get source code (may be list or string)
                source = cell.get('source', [])
                if isinstance(source, list):
                    code = ''.join(source)
                else:
                    code = source
                
                # Skip empty cells
                if code.strip():
                    code_cells.append(code)
            
            elif cell.get('cell_type') == 'markdown':
                # Optionally include markdown as comments
                source = cell.get('source', [])
                if isinstance(source, list):
                    markdown = ''.join(source)
                else:
                    markdown = source
                
                if markdown.strip():
                    # Convert markdown to comments
                    commented = '\n'.join(f'# {line}' if line else '#' 
                                         for line in markdown.split('\n'))
                    code_cells.append(commented)
        
        return code_cells
    
    except Exception as e:
        print(f"Error reading {notebook_path}: {e}")
        return None

def export_notebook_to_py(notebook_path, output_path, include_markdown=True):
    """
    Export a Jupyter notebook to a Python script
    
    Args:
        notebook_path: Path to input .ipynb file
        output_path: Path to output .py file
        include_markdown: Include markdown cells as comments
    """
    print(f"Converting: {notebook_path.name}")
    
    # Extract cells
    if include_markdown:
        cells = extract_code_cells(notebook_path)
    else:
        # Only code cells
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            cells = []
            for cell in notebook.get('cells', []):
                if cell.get('cell_type') == 'code':
                    source = cell.get('source', [])
                    if isinstance(source, list):
                        code = ''.join(source)
                    else:
                        code = source
                    if code.strip():
                        cells.append(code)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    if cells is None:
        return False
    
    # Write to Python file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f'#!/usr/bin/env python3\n')
            f.write(f'"""\n')
            f.write(f'Exported from: {notebook_path.name}\n')
            f.write(f'Original notebook: {notebook_path}\n')
            f.write(f'"""\n\n')
            
            # Write cells
            for i, cell in enumerate(cells):
                if i > 0:
                    f.write('\n\n' + '='*70 + '\n')
                    f.write(f'# Cell {i}\n')
                    f.write('='*70 + '\n\n')
                
                f.write(cell)
                if not cell.endswith('\n'):
                    f.write('\n')
        
        print(f"  ✓ Saved to: {output_path.name}")
        return True
    
    except Exception as e:
        print(f"  ❌ Error writing: {e}")
        return False

def export_afm_notebooks(
    source_dir='AFM',
    output_dir='AFM/exported_scripts',
    include_markdown=True,
    recursive=True
):
    """
    Export all Jupyter notebooks in AFM directory to Python scripts
    
    Args:
        source_dir: Directory containing notebooks
        output_dir: Directory for output Python files
        include_markdown: Include markdown cells as comments
        recursive: Search subdirectories
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    # Validate source directory
    if not source_path.exists():
        print(f"❌ Source directory not found: {source_path}")
        return
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_path}")
    print("="*70)
    
    # Find all notebooks
    if recursive:
        notebooks = list(source_path.rglob('*.ipynb'))
    else:
        notebooks = list(source_path.glob('*.ipynb'))
    
    # Filter out checkpoints
    notebooks = [nb for nb in notebooks if '.ipynb_checkpoints' not in str(nb)]
    
    if not notebooks:
        print(f"No notebooks found in {source_path}")
        return
    
    print(f"\nFound {len(notebooks)} notebook(s):\n")
    
    # Export each notebook
    success_count = 0
    for notebook_path in sorted(notebooks):
        # Generate output filename
        # Preserve relative directory structure
        rel_path = notebook_path.relative_to(source_path)
        output_file = output_path / rel_path.with_suffix('.py')
        
        # Create subdirectories if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Export
        if export_notebook_to_py(notebook_path, output_file, include_markdown):
            success_count += 1
    
    # Summary
    print("\n" + "="*70)
    print(f"✅ Successfully exported: {success_count}/{len(notebooks)} notebooks")
    print(f"📁 Output directory: {output_path}")
    
    # List output files
    py_files = list(output_path.rglob('*.py'))
    if py_files:
        print(f"\n📄 Exported files:")
        for py_file in sorted(py_files):
            size_kb = py_file.stat().st_size / 1024
            print(f"   • {py_file.name} ({size_kb:.1f} KB)")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Export AFM Jupyter notebooks to Python scripts'
    )
    parser.add_argument(
        '--source',
        default='AFM',
        help='Source directory containing notebooks (default: AFM)'
    )
    parser.add_argument(
        '--output',
        default='AFM/exported_scripts',
        help='Output directory for Python files (default: AFM/exported_scripts)'
    )
    parser.add_argument(
        '--no-markdown',
        action='store_true',
        help='Exclude markdown cells (only export code)'
    )
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do not search subdirectories'
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("AFM Notebook Exporter")
    print("="*70)
    print(f"Source: {args.source}")
    print(f"Output: {args.output}")
    print(f"Include markdown: {not args.no_markdown}")
    print(f"Recursive: {not args.no_recursive}")
    print("="*70 + "\n")
    
    export_afm_notebooks(
        source_dir=args.source,
        output_dir=args.output,
        include_markdown=not args.no_markdown,
        recursive=not args.no_recursive
    )

if __name__ == '__main__':
    main()
