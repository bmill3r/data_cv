#!/usr/bin/env python3
"""
CSV to JSON Converter for CV/Resume Data

This script converts CSV files in the format expected by the render.r script
into a structured JSON file that can be used as a master database.

Usage:
    python csv_to_json_converter.py --input-dir my_resume_data --output-file cv_database.json
"""

import argparse
import csv
import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

def read_csv_file(file_path: str, has_explanation_row: bool = False) -> List[Dict]:
    """Read a CSV file and return its data as a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file
        has_explanation_row: If True, skip the first row (explanation row)
    """
    if not os.path.exists(file_path):
        print(f"Warning: File {file_path} does not exist. Skipping.")
        return []
    
    # Try different encodings in order of likelihood
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            # Handle files with or without explanation rows
            if has_explanation_row:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Skip the explanation row
                    lines = f.readlines()
                    if len(lines) <= 2:  # Need at least header row and one data row
                        print(f"File {file_path} doesn't have enough rows")
                        return []
                    
                    # Create a new CSV reader from the remaining lines
                    csv_data = "".join(lines[1:])  # Skip the first line
                    reader = csv.DictReader(csv_data.splitlines())
                    data = [row for row in reader if any(row.values())]  # Skip empty rows
            else:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Regular CSV reading (for aside files)
                    reader = csv.DictReader(f)
                    data = [row for row in reader if any(row.values())]  # Skip empty rows
            
            print(f"Successfully read {file_path} using {encoding} encoding with {len(data)} rows")
            return data
        except UnicodeDecodeError:
            # Try the next encoding
            continue
        except Exception as e:
            print(f"Error reading CSV file {file_path}: {e}")
            return []
    
    print(f"Failed to read {file_path} with any of the attempted encodings")
    return []

def parse_entries_csv(entries_data: List[Dict]) -> List[Dict]:
    """
    Convert entries.csv data into JSON structure.
    
    This handles the main content entries like work experience, education, etc.
    """
    result = []
    
    print(f"Processing {len(entries_data)} entries from entries.csv")
    if entries_data and len(entries_data) > 0:
        # Print column names for debugging
        print(f"Available columns: {', '.join(entries_data[0].keys())}")
    
    for i, entry in enumerate(entries_data):
        # Extract and process descriptions (description_1, description_2, etc.)
        descriptions = []
        for key in sorted([k for k in entry.keys() if k.startswith('description_')]):
            if entry[key]:
                descriptions.append(entry[key])
        
        # Extract companies from company_* fields
        companies = []
        for key in entry.keys():
            if key.startswith('company_') and entry[key].upper() in ['TRUE', 'T', 'YES', 'Y', '1']:
                company_name = key.replace('company_', '')
                companies.append(company_name)
        
        # Determine tags based on in_resume field and section
        tags = []
        if entry.get('in_resume', '').upper() in ['TRUE', 'T', 'YES', 'Y', '1']:
            tags.append('resume')
        tags.append('cv')  # We assume all entries belong in the CV
        
        # Add section as a tag too for better filtering
        section = entry.get('section', '')
        if section and section not in tags:
            tags.append(section)
        
        # Create the structured entry
        json_entry = {
            'section': section,
            'title': entry.get('title', ''),
            'loc': entry.get('loc', ''),
            'institution': entry.get('institution', ''),
            'start': entry.get('start', ''),
            'end': entry.get('end', ''),
            'descriptions': descriptions,
            'companies': companies,
            'tags': tags,
            'importance': len(entries_data) - i  # Higher importance for earlier entries
        }
        
        result.append(json_entry)
    
    print(f"Converted {len(result)} entries with their descriptions and tags")
    return result

def parse_contact_info_csv(contact_data: List[Dict], input_dir: str) -> Dict:
    """Convert contact info CSV data into JSON structure."""
    result = {}
    
    # Try the direct CSV reading approach first - more reliable than Dict parsing
    contact_info_path = os.path.join(input_dir, "contact_info.csv")
    if os.path.exists(contact_info_path):
        try:
            with open(contact_info_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip header row
                
                print(f"Reading contact info directly from CSV using column indices")
                print(f"Headers: {headers}")
                
                # Locate the correct columns
                loc_index = 0     # First column - loc
                icon_index = 1     # Second column - icon
                contact_index = 2  # Third column - contact
                
                # Read each row
                row_count = 0
                for row in reader:
                    if len(row) >= max(loc_index, icon_index, contact_index) + 1:
                        loc = row[loc_index]
                        icon = row[icon_index]
                        contact = row[contact_index]
                        
                        if loc and contact:
                            # For duplicate 'loc' values, append the icon to make the key unique
                            key = loc
                            if loc in result and icon:
                                # Format as website_globe, website_book, etc.
                                key = f"{loc}_{icon}"
                            
                            # Store both contact value and icon information
                            result[key] = {
                                'value': contact,
                                'icon': icon
                            }
                            print(f"  Added contact entry: {key} = {contact} (icon: {icon})")
                            row_count += 1
                
                if row_count > 0:
                    print(f"Successfully parsed {row_count} contact entries directly from CSV")
                    return result
        except Exception as e:
            print(f"Error with direct CSV parsing: {e}, falling back to Dict method")
    
    # Fall back to Dict-based parsing if direct method fails
    print(f"Processing {len(contact_data)} contact info entries using Dict method")
    if contact_data and len(contact_data) > 0:
        print(f"Available columns: {', '.join(contact_data[0].keys())}")
    
    for item in contact_data:
        # Check for standard format with loc/icon/contact
        if 'loc' in item and 'contact' in item:
            loc = item.get('loc', '')
            contact = item.get('contact', '')
            
            if loc and contact:
                result[loc] = contact
                print(f"  Added contact entry: {loc} = {contact}")
        # Fall back to id/value format if available
        elif 'id' in item and 'value' in item:
            result[item['id']] = item['value']
    
    print(f"Processed {len(result)} contact info entries")
    return result

def parse_text_blocks_csv(text_blocks_data: List[Dict]) -> List[Dict]:
    """Convert text blocks CSV data into JSON structure."""
    result = []
    
    print(f"Processing {len(text_blocks_data)} text blocks")
    if text_blocks_data and len(text_blocks_data) > 0:
        print(f"Available columns: {', '.join(text_blocks_data[0].keys())}")
    
    for block in text_blocks_data:
        # Look for standard columns first
        if 'loc' in block and 'text' in block:
            json_block = {
                'id': block['loc'],
                'content': block['text'],
                'tags': ['cv', 'resume']  # Assume all text blocks are used in both CV and resume
            }
            result.append(json_block)
        # Try alternate column names
        elif len(block) >= 2:
            columns = list(block.keys())
            # Assume first column is ID/location and second is text content
            json_block = {
                'id': block[columns[0]], 
                'content': block[columns[1]],
                'tags': ['cv', 'resume']
            }
            result.append(json_block)
    
    print(f"Processed {len(result)} text blocks")
    return result

def parse_aside_sections_and_entries(sections_data: List[Dict], entries_data: List[Dict]) -> List[Dict]:
    """
    Convert aside sections and entries CSV data into JSON structure.
    
    This handles the skills categories and entries in the aside section.
    """
    # Using a more direct approach for conversion based on column names actually in the CSV files
    
    # First, organize entries by category
    entries_by_category = {}
    for entry in entries_data:
        # In the CSV, 'category' is the key field
        category = entry.get('category', '')
        if not category:  # Skip entries without a category
            continue
            
        if category not in entries_by_category:
            entries_by_category[category] = []
        
        # In the CSV, 'entry' contains the skill name
        entries_by_category[category].append({
            'name': entry.get('entry', ''),
            'level': ''  # We'll leave level empty since it's not in the CSV
        })
    
    # Create skills list from sections data
    result = []
    for section in sections_data:
        category_id = section.get('category', '')
        if not category_id:  # Skip sections without a category
            continue
            
        # Only include categories that have entries
        if category_id in entries_by_category:
            skill_category = {
                'category': section.get('display_name', ''),  # Use display_name for the category title
                'entries': entries_by_category[category_id],
                'tags': ['cv', 'resume']  # Include in both CV and resume
            }
            result.append(skill_category)
    
    # Print some debug information
    print(f"Processed {len(sections_data)} skill categories with {sum(len(entries) for _, entries in entries_by_category.items())} total skills")
    for category_id, entries in entries_by_category.items():
        print(f"  - {category_id}: {len(entries)} skills")
            
    return result

def convert_csv_to_json(input_dir: str, output_file: str) -> None:
    """
    Convert CSV files to a structured JSON file.
    
    Args:
        input_dir: Directory containing the CSV files
        output_file: Path to save the JSON file
    """
    print(f"Reading CSV files from {input_dir}...")
    
    # Define paths to CSV files
    entries_path = os.path.join(input_dir, "entries.csv")
    contact_info_path = os.path.join(input_dir, "contact_info.csv")
    text_blocks_path = os.path.join(input_dir, "text_blocks.csv")
    aside_sections_path = os.path.join(input_dir, "aside_sections.csv")
    aside_entries_path = os.path.join(input_dir, "aside_entries.csv")
    
    # Read CSV files - entries CSV has an explanation row
    entries_data = read_csv_file(entries_path, has_explanation_row=True)
    contact_info_data = read_csv_file(contact_info_path, has_explanation_row=True)
    text_blocks_data = read_csv_file(text_blocks_path, has_explanation_row=True)
    
    # Aside files don't have explanation rows
    aside_sections_data = read_csv_file(aside_sections_path)
    aside_entries_data = read_csv_file(aside_entries_path)
    
    # Parse data
    json_data = {
        'meta': {
            'last_updated': datetime.now().strftime("%Y-%m-%d"),
            'generated_by': 'csv_to_json_converter.py'
        },
        'contact_info': parse_contact_info_csv(contact_info_data, input_dir),
        'entries': parse_entries_csv(entries_data),
        'text_blocks': parse_text_blocks_csv(text_blocks_data),
        'skills': parse_aside_sections_and_entries(aside_sections_data, aside_entries_data)
    }
    
    # Write JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"Successfully created {output_file}")
        print(f"Included {len(json_data['entries'])} entries, {len(json_data['skills'])} skill categories, and {len(json_data['text_blocks'])} text blocks")
        
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        sys.exit(1)

def main():
    """Main function to parse arguments and run the conversion."""
    parser = argparse.ArgumentParser(description='Convert CV/resume CSV files to JSON format.')
    parser.add_argument('--input-dir', required=True, help='Directory containing CSV files')
    parser.add_argument('--output-file', default='cv_database.json', help='Path to save the JSON file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory {args.input_dir} does not exist")
        sys.exit(1)
    
    convert_csv_to_json(args.input_dir, args.output_file)

if __name__ == "__main__":
    main()
