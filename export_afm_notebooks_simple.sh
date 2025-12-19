#!/bin/bash
# Simple script to export AFM notebooks using jupyter nbconvert
# Requires: pip install nbconvert

set -e

SOURCE_DIR="AFM"
OUTPUT_DIR="AFM/exported_scripts"

echo "========================================================================"
echo "AFM Notebook Exporter (using nbconvert)"
echo "========================================================================"
echo "Source: $SOURCE_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if nbconvert is available
if ! command -v jupyter &> /dev/null; then
    echo "❌ Error: jupyter not found"
    echo "Install with: pip install jupyter nbconvert"
    exit 1
fi

# Find and convert all notebooks
count=0
for notebook in "$SOURCE_DIR"/*.ipynb; do
    if [ -f "$notebook" ]; then
        basename=$(basename "$notebook" .ipynb)
        echo "Converting: $basename.ipynb"
        
        # Convert to Python script
        jupyter nbconvert --to script "$notebook" --output-dir="$OUTPUT_DIR"
        
        count=$((count + 1))
    fi
done

# Also check old_notebooks subdirectory
if [ -d "$SOURCE_DIR/old_notebooks" ]; then
    echo ""
    echo "Processing old_notebooks subdirectory..."
    mkdir -p "$OUTPUT_DIR/old_notebooks"
    
    for notebook in "$SOURCE_DIR/old_notebooks"/*.ipynb; do
        if [ -f "$notebook" ]; then
            basename=$(basename "$notebook" .ipynb)
            echo "Converting: old_notebooks/$basename.ipynb"
            
            jupyter nbconvert --to script "$notebook" --output-dir="$OUTPUT_DIR/old_notebooks"
            
            count=$((count + 1))
        fi
    done
fi

echo ""
echo "========================================================================"
echo "✅ Exported $count notebook(s) to $OUTPUT_DIR"
echo "========================================================================"
echo ""
echo "📄 Output files:"
ls -lh "$OUTPUT_DIR"/*.py 2>/dev/null || echo "  (none in main directory)"

if [ -d "$OUTPUT_DIR/old_notebooks" ]; then
    echo ""
    echo "📄 Old notebooks:"
    ls -lh "$OUTPUT_DIR/old_notebooks"/*.py 2>/dev/null || echo "  (none)"
fi
