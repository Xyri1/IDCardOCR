#!/usr/bin/env python3
"""
Input/Output Comparison Script
Compares input PDF files with output PNG files to identify which files were skipped or incomplete
"""

import sys
from pathlib import Path
from collections import defaultdict

# Get project root directory
PROJECT_ROOT = Path(__file__).parent

# Set UTF-8 encoding for Windows console output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_input_files(input_dir):
    """
    Get all PDF files from the input directory
    Returns a dictionary with base name as key and file path as value
    """
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return None
    
    pdf_files = {}
    for pdf_file in input_dir.glob("*.pdf"):
        base_name = pdf_file.stem  # Get filename without extension
        pdf_files[base_name] = pdf_file
    
    return pdf_files


def get_output_files(output_dir):
    """
    Get all output PNG files from the output directory
    Groups them by base name (without _front or _back suffix)
    Returns a dictionary with base name as key and list of output files as value
    """
    output_dir = Path(output_dir)
    
    if not output_dir.exists():
        print(f"Error: Output directory not found: {output_dir}")
        return None
    
    output_files = defaultdict(list)
    for png_file in output_dir.glob("*.png"):
        # Extract base name by removing _front.png or _back.png
        file_name = png_file.stem
        
        if file_name.endswith('_front'):
            base_name = file_name[:-6]  # Remove '_front'
            output_files[base_name].append(('front', png_file))
        elif file_name.endswith('_back'):
            base_name = file_name[:-5]  # Remove '_back'
            output_files[base_name].append(('back', png_file))
        else:
            # Unexpected file format
            output_files[file_name].append(('unknown', png_file))
    
    return output_files


def compare_files(input_files, output_files):
    """
    Compare input files with output files to find missing or incomplete extractions
    """
    results = {
        'completely_missing': [],      # No output files at all
        'incomplete': [],               # Missing front or back
        'complete': [],                 # Both front and back exist
        'extra_outputs': []            # Output files with no matching input
    }
    
    # Check each input file
    for base_name, input_file in input_files.items():
        if base_name not in output_files:
            results['completely_missing'].append({
                'name': base_name,
                'input_file': input_file,
                'missing': ['front', 'back']
            })
        else:
            outputs = output_files[base_name]
            output_types = [t for t, _ in outputs]
            
            if 'front' in output_types and 'back' in output_types:
                results['complete'].append({
                    'name': base_name,
                    'input_file': input_file,
                    'outputs': outputs
                })
            else:
                missing = []
                if 'front' not in output_types:
                    missing.append('front')
                if 'back' not in output_types:
                    missing.append('back')
                
                results['incomplete'].append({
                    'name': base_name,
                    'input_file': input_file,
                    'outputs': outputs,
                    'missing': missing
                })
    
    # Check for extra outputs (outputs without matching inputs)
    for base_name, outputs in output_files.items():
        if base_name not in input_files:
            results['extra_outputs'].append({
                'name': base_name,
                'outputs': outputs
            })
    
    return results


def print_report(results, input_count, output_base_count):
    """
    Print a formatted report of the comparison results
    """
    print("=" * 80)
    print("INPUT/OUTPUT COMPARISON REPORT")
    print("=" * 80)
    print()
    
    # Summary
    print("SUMMARY:")
    print(f"  Total input PDFs: {input_count}")
    print(f"  Complete extractions (both front & back): {len(results['complete'])}")
    print(f"  Completely missing outputs: {len(results['completely_missing'])}")
    print(f"  Incomplete extractions (missing front or back): {len(results['incomplete'])}")
    print(f"  Extra output files (no matching input): {len(results['extra_outputs'])}")
    print()
    
    total_skipped = len(results['completely_missing']) + len(results['incomplete'])
    if total_skipped > 0:
        print(f"  TOTAL SKIPPED/INCOMPLETE: {total_skipped}")
        print()
    
    # Completely missing outputs
    if results['completely_missing']:
        print("COMPLETELY MISSING OUTPUTS:")
        print("-" * 80)
        print(f"These {len(results['completely_missing'])} input PDFs have NO output files:")
        print()
        for i, item in enumerate(results['completely_missing'], 1):
            print(f"  {i}. {item['name']}.pdf")
        print()
    
    # Incomplete extractions
    if results['incomplete']:
        print("INCOMPLETE EXTRACTIONS:")
        print("-" * 80)
        print(f"These {len(results['incomplete'])} input PDFs are missing some output files:")
        print()
        for i, item in enumerate(results['incomplete'], 1):
            print(f"  {i}. {item['name']}.pdf")
            print(f"     Missing: {', '.join(item['missing'])}")
            print(f"     Found: {', '.join([t for t, _ in item['outputs']])}")
        print()
    
    # Extra outputs
    if results['extra_outputs']:
        print("EXTRA OUTPUT FILES:")
        print("-" * 80)
        print(f"These {len(results['extra_outputs'])} output sets have no matching input PDF:")
        print()
        for i, item in enumerate(results['extra_outputs'], 1):
            print(f"  {i}. {item['name']}")
            print(f"     Files: {', '.join([t for t, _ in item['outputs']])}")
        print()
    
    # Save skipped files to a text file
    if total_skipped > 0:
        skipped_file = PROJECT_ROOT / "skipped_files.txt"
        with open(skipped_file, 'w', encoding='utf-8') as f:
            f.write("Skipped/Incomplete Files (Based on Input/Output Comparison)\n")
            f.write("=" * 80 + "\n\n")
            
            if results['completely_missing']:
                f.write(f"COMPLETELY MISSING OUTPUTS ({len(results['completely_missing'])} files):\n")
                f.write("-" * 80 + "\n")
                for item in results['completely_missing']:
                    f.write(f"{item['name']}.pdf\n")
                f.write("\n")
            
            if results['incomplete']:
                f.write(f"INCOMPLETE EXTRACTIONS ({len(results['incomplete'])} files):\n")
                f.write("-" * 80 + "\n")
                for item in results['incomplete']:
                    f.write(f"{item['name']}.pdf - Missing: {', '.join(item['missing'])}\n")
                f.write("\n")
        
        print(f"Skipped files list saved to: {skipped_file}")
        print()
    else:
        print("✓ All input files have been successfully processed!")
        print()
    
    print("=" * 80)


def main():
    """
    Main function to compare inputs and outputs
    """
    input_dir = PROJECT_ROOT / "inputs"
    output_dir = PROJECT_ROOT / "outputs"
    
    print(f"Comparing files...")
    print(f"  Input directory:  {input_dir}")
    print(f"  Output directory: {output_dir}")
    print()
    
    # Get input files
    input_files = get_input_files(input_dir)
    if input_files is None:
        return
    
    # Get output files
    output_files = get_output_files(output_dir)
    if output_files is None:
        return
    
    print(f"Found {len(input_files)} input PDF files")
    print(f"Found {len(output_files)} unique output base names")
    print()
    
    # Compare files
    results = compare_files(input_files, output_files)
    
    # Print report
    print_report(results, len(input_files), len(output_files))


if __name__ == "__main__":
    main()

