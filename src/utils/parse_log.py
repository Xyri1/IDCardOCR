#!/usr/bin/env python3
"""
Log Parser for ID Card Extraction
Analyzes the log file to identify skipped, failed, and problematic files
"""

import re
from pathlib import Path
from collections import defaultdict

# Get project root directory
PROJECT_ROOT = Path(__file__).parent

def parse_log(log_file):
    """
    Parse the log file and extract information about processed files
    """
    log_file = Path(log_file)
    
    if not log_file.exists():
        print(f"Error: Log file not found: {log_file}")
        return None
    
    results = {
        'successful': [],
        'failed': [],
        'errors': defaultdict(list),
        'warnings': defaultdict(list),
        'total_pdfs': 0,
        'success_count': 0,
        'fail_count': 0
    }
    
    current_file = None
    
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Extract processing file name
            match = re.search(r'Processing: (.+\.pdf)', line)
            if match:
                current_file = match.group(1)
                continue
            
            # Check for successful processing
            if current_file and 'Successfully processed:' in line:
                match = re.search(r'Successfully processed: (.+\.pdf)', line)
                if match:
                    results['successful'].append(match.group(1))
                    current_file = None
                continue
            
            # Check for failed processing
            if current_file and 'Failed to process:' in line:
                match = re.search(r'Failed to process: (.+\.pdf)', line)
                if match:
                    results['failed'].append(match.group(1))
                    current_file = None
                continue
            
            # Check for errors
            if 'ERROR' in line:
                # Extract error type and file
                if 'UNSUPPORTED FORMAT:' in line:
                    match = re.search(r'UNSUPPORTED FORMAT: (.+\.pdf) - (.+)', line)
                    if match:
                        filename = match.group(1)
                        reason = match.group(2)
                        results['errors']['UNSUPPORTED FORMAT'].append({
                            'file': filename,
                            'reason': reason
                        })
                        results['failed'].append(filename)
                        current_file = None
                elif current_file:
                    match = re.search(r'ERROR - (.+)', line)
                    if match:
                        error_msg = match.group(1)
                        results['errors']['OTHER'].append({
                            'file': current_file,
                            'error': error_msg
                        })
            
            # Check for warnings
            if 'WARNING' in line and current_file:
                match = re.search(r'WARNING - (.+)', line)
                if match:
                    warning_msg = match.group(1)
                    results['warnings'][current_file].append(warning_msg)
            
            # Extract summary statistics
            if 'Total PDFs:' in line:
                match = re.search(r'Total PDFs: (\d+)', line)
                if match:
                    results['total_pdfs'] = int(match.group(1))
            
            if 'Successfully processed:' in line and 'INFO - Successfully processed:' in line:
                match = re.search(r'Successfully processed: (\d+)', line)
                if match:
                    results['success_count'] = int(match.group(1))
            
            if 'Failed/Skipped:' in line:
                match = re.search(r'Failed/Skipped: (\d+)', line)
                if match:
                    results['fail_count'] = int(match.group(1))
    
    return results


def print_report(results):
    """
    Print a formatted report of the parsing results
    """
    print("=" * 80)
    print("ID CARD EXTRACTION LOG ANALYSIS REPORT")
    print("=" * 80)
    print()
    
    # Summary
    print("SUMMARY:")
    print(f"  Total PDFs processed: {results['total_pdfs']}")
    print(f"  Successfully extracted: {results['success_count']}")
    print(f"  Failed/Skipped: {results['fail_count']}")
    print()
    
    # Failed files by error type
    if results['errors']:
        print("FAILED FILES BY ERROR TYPE:")
        print("-" * 80)
        
        for error_type, error_list in results['errors'].items():
            print(f"\n{error_type} ({len(error_list)} files):")
            for item in error_list:
                if error_type == 'UNSUPPORTED FORMAT':
                    print(f"  - {item['file']}")
                    print(f"    Reason: {item['reason']}")
                else:
                    print(f"  - {item['file']}")
                    print(f"    Error: {item['error']}")
        print()
    
    # List all failed files
    if results['failed']:
        print("ALL FAILED/SKIPPED FILES:")
        print("-" * 80)
        for i, filename in enumerate(results['failed'], 1):
            print(f"  {i}. {filename}")
        print()
    
    # Files with warnings
    if results['warnings']:
        print(f"FILES WITH WARNINGS ({len(results['warnings'])} files):")
        print("-" * 80)
        for filename, warnings in results['warnings'].items():
            print(f"\n  {filename}:")
            for warning in warnings:
                print(f"    - {warning}")
        print()
    
    # Save failed files list to a text file
    if results['failed']:
        failed_file = PROJECT_ROOT / "failed_files.txt"
        with open(failed_file, 'w', encoding='utf-8') as f:
            f.write("Failed/Skipped Files:\n")
            f.write("=" * 80 + "\n\n")
            for filename in results['failed']:
                f.write(f"{filename}\n")
        print(f"Failed files list saved to: {failed_file}")
        print()


def main():
    """
    Main function to parse log and generate report
    """
    import sys
    
    # Set UTF-8 encoding for Windows console output
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    log_file = PROJECT_ROOT / "id_extraction.log"
    
    print(f"Parsing log file: {log_file}")
    print()
    
    results = parse_log(log_file)
    
    if results is None:
        return
    
    print_report(results)
    
    print("=" * 80)


if __name__ == "__main__":
    main()

