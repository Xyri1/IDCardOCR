#!/usr/bin/env python3
"""
Fix ID numbers in existing CSV file
Changes tab prefix to apostrophe prefix for better Excel compatibility
"""

import csv
from pathlib import Path

def fix_id_numbers_in_csv(input_csv, output_csv=None):
    """
    Replace tab prefix with apostrophe prefix for id_num column
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file (if None, overwrites input)
    """
    if output_csv is None:
        output_csv = input_csv
    
    # Read the CSV
    with open(input_csv, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    
    # Process each row
    fixed_count = 0
    for row in rows:
        if 'id_num' in row and row['id_num']:
            # Remove tab prefix if present
            id_num = row['id_num'].lstrip('\t')
            
            # Add apostrophe prefix if not empty
            if id_num:
                row['id_num'] = f"'{id_num}"
                fixed_count += 1
    
    # Write the fixed CSV
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"[OK] Fixed {fixed_count} ID numbers")
    print(f"[OK] Output saved to: {output_csv}")
    
    return fixed_count


if __name__ == "__main__":
    # Fix the current results file
    csv_file = Path(__file__).parent / "id_card_results.csv"
    
    if not csv_file.exists():
        print(f"Error: {csv_file} not found")
        print("Please run the main script first to generate the CSV file")
        exit(1)
    
    # Create backup
    backup_file = csv_file.parent / "id_card_results_backup.csv"
    print(f"Creating backup: {backup_file}")
    
    import shutil
    shutil.copy2(csv_file, backup_file)
    print(f"[OK] Backup created")
    
    # Fix the ID numbers
    print(f"\nProcessing: {csv_file}")
    fixed_count = fix_id_numbers_in_csv(csv_file)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Original file backed up to: {backup_file}")
    print(f"Fixed file: {csv_file}")
    print(f"ID numbers fixed: {fixed_count}")
    print(f"\nThe CSV now uses apostrophe prefix (') instead of tab.")
    print(f"ID numbers will display correctly in Excel without the tab character.")
    print(f"{'='*60}")

