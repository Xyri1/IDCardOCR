#!/usr/bin/env python3
"""
Convert Skipped Files to Images
Converts skipped PDF files to images (all pages) and saves them in a separate directory
"""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import fitz  # PyMuPDF
except ImportError as e:
    print("Error: PyMuPDF is not installed or improperly installed.")
    print(f"Import error: {e}")
    print("\nPlease ensure PyMuPDF is installed correctly.")
    print("If you see 'No module named frontend', try:")
    print("  1. pip uninstall -y fitz")
    print("  2. pip install --proxy=socks5://127.0.0.1:10808 PyMuPDF")
    sys.exit(1)

# Get project root directory
PROJECT_ROOT = Path(__file__).parent


def read_skipped_files(skipped_file):
    """
    Read the list of skipped files from the text file
    """
    skipped_file = Path(skipped_file)
    
    if not skipped_file.exists():
        print(f"Error: Skipped files list not found: {skipped_file}")
        return None
    
    skipped_files = []
    with open(skipped_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip headers, separators, and empty lines
            if line and not line.startswith('=') and not line.startswith('-') and \
               not line.startswith('Skipped') and not line.startswith('COMPLETELY') and \
               not line.startswith('INCOMPLETE') and line.endswith('.pdf'):
                skipped_files.append(line)
    
    return skipped_files


def convert_pdf_to_images(pdf_path, output_dir, dpi=300):
    """
    Convert all pages of a PDF to images
    Returns the number of pages converted
    """
    try:
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        
        if not pdf_path.exists():
            print(f"  Error: File not found: {pdf_path}")
            return 0
        
        # Open PDF
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        
        base_name = pdf_path.stem
        
        print(f"  Converting {page_count} page(s)...")
        
        # Convert each page to image
        for page_num in range(page_count):
            page = doc[page_num]
            
            # Render page to image at specified DPI
            matrix = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=matrix)
            
            # Save image
            output_file = output_dir / f"{base_name}_page{page_num + 1}.png"
            pix.save(str(output_file))
            print(f"    Saved: {output_file.name}")
        
        doc.close()
        return page_count
        
    except Exception as e:
        print(f"  Error converting {pdf_path}: {str(e)}")
        return 0


def main():
    """
    Main function to convert skipped files
    """
    # Configuration
    skipped_file = PROJECT_ROOT / "skipped_files.txt"
    input_dir = PROJECT_ROOT / "inputs"
    output_dir = PROJECT_ROOT / "manual_review"
    dpi = 300  # Resolution for output images
    
    print("=" * 80)
    print("CONVERT SKIPPED FILES TO IMAGES")
    print("=" * 80)
    print()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Input directory:  {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Resolution:       {dpi} DPI")
    print()
    
    # Read skipped files list
    print(f"Reading skipped files from: {skipped_file}")
    skipped_files = read_skipped_files(skipped_file)
    
    if skipped_files is None:
        return
    
    if not skipped_files:
        print("No skipped files found in the list.")
        return
    
    print(f"Found {len(skipped_files)} skipped file(s)")
    print()
    
    # Process each skipped file
    success_count = 0
    error_count = 0
    total_pages = 0
    
    for i, filename in enumerate(skipped_files, 1):
        print(f"[{i}/{len(skipped_files)}] Processing: {filename}")
        
        pdf_path = input_dir / filename
        pages = convert_pdf_to_images(pdf_path, output_dir, dpi)
        
        if pages > 0:
            success_count += 1
            total_pages += pages
        else:
            error_count += 1
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files processed: {len(skipped_files)}")
    print(f"Successfully converted: {success_count}")
    print(f"Failed: {error_count}")
    print(f"Total pages extracted: {total_pages}")
    print(f"Output directory: {output_dir}")
    print("=" * 80)
    print()
    print("All images have been saved to the 'manual_review' directory.")
    print("You can now manually review and process these files.")


if __name__ == "__main__":
    main()

