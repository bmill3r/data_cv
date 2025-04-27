#!/usr/bin/env python3
"""
JSON to CSV Converter for CV/Resume Data

This script converts a structured JSON file containing resume/CV data into
the CSV format expected by the render.r script.

Usage:
    python json_to_csv_converter.py --json cv_data.json --output-dir my_cv_data --type cv
    python json_to_csv_converter.py --json cv_data.json --output-dir my_resume_data --type resume
    python json_to_csv_converter.py --json cv_data.json --output-dir my_cv_data --type cv --filter-company biotech
"""

import argparse
import json
import os
import csv
import sys
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

def load_json_data(json_path: str) -> Dict:
    """Load and parse the JSON data from the specified file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        sys.exit(1)

def ensure_output_dir(output_dir: str) -> None:
    """Ensure the output directory exists."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

def write_entries_csv(data: Dict, output_dir: str, doc_type: str, 
                     company_filter: Optional[str] = None, 
                     tag_filter: Optional[str] = None) -> None:
    """
    Write entries data to a CSV file.
    
    Args:
        data: The JSON data
        output_dir: Directory to write the CSV file
        doc_type: Type of document ('cv' or 'resume')
        company_filter: Optional filter for company
        tag_filter: Optional filter for tag
    """
    entries = data.get('entries', [])
    
    # Filter entries based on document type, company, and tag
    filtered_entries = []
    for entry in entries:
        entry_tags = set(entry.get('tags', []))
        entry_companies = set(entry.get('companies', []))
        
        # Check if entry is valid for the document type
        if doc_type in entry_tags:
            # Apply company filter if specified
            if company_filter and company_filter not in entry_companies:
                continue
                
            # Apply tag filter if specified
            if tag_filter and tag_filter not in entry_tags:
                continue
                
            filtered_entries.append(entry)
    
    # Sort entries by importance and then by end date (most recent first)
    filtered_entries.sort(key=lambda x: (
        -x.get('importance', 0),
        # Sort "Current" at the top
        0 if x.get('end', '') == 'Current' else 1,
        # Sort by year in descending order 
        -int(x.get('end', '0')) if x.get('end', '').isdigit() else 0
    ))
    
    output_file = os.path.join(output_dir, "entries.csv")
    
    # Define CSV headers - match the existing format
    headers = [
        "section", "title", "loc", "institution", "start", "end",
    ]
    
    # Add description columns
    max_descriptions = max([len(entry.get('descriptions', [])) for entry in filtered_entries], default=0)
    description_headers = [f"description_{i+1}" for i in range(max_descriptions)]
    
    # Add in_resume column and company columns
    headers.extend(description_headers)
    headers.append("in_resume")
    
    # Find all unique company names
    all_companies = set()
    for entry in entries:
        all_companies.update(entry.get('companies', []))
    
    company_headers = [f"company_{company}" for company in all_companies]
    headers.extend(company_headers)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header explanation row (first row in the original CSV)
        header_explanation = ["Where in your CV this entry belongs", 
                             "Main title of the entry", 
                             "Location the entry occured", 
                             "Primary institution affiliation for entry", 
                             "Start date of entry (year)", 
                             "\"End year of entry. Set to \"\"current\"\" if entry is still ongoing.\""]
        
        # Add description explanations
        header_explanation.extend(["Each description column is a separate bullet point for the entry. If you need more description bullet points simply add a new column with title \"description_{4,5,..}\""] * len(description_headers))
        
        # Add in_resume explanation and company explanations
        header_explanation.append("A filter variable that is used to decide if entry is in the smaller resume. ")
        header_explanation.extend(["Maybe use these columns to choose which entries used for a given company?"] * len(company_headers))
        
        writer.writerow(header_explanation)
        writer.writerow(headers)
        
        # Write data rows
        for entry in filtered_entries:
            row = [
                entry.get('section', ''),
                entry.get('title', ''),
                entry.get('loc', ''),
                entry.get('institution', ''),
                entry.get('start', ''),
                entry.get('end', '')
            ]
            
            # Add descriptions, padding with empty strings if needed
            descriptions = entry.get('descriptions', [])
            row.extend(descriptions + [''] * (max_descriptions - len(descriptions)))
            
            # Add in_resume flag (defaulting to TRUE for resume-tagged entries)
            row.append('TRUE' if 'resume' in entry.get('tags', []) else 'FALSE')
            
            # Add company flags
            for company in all_companies:
                is_company_match = company in entry.get('companies', [])
                row.append('TRUE' if is_company_match else 'FALSE')
            
            writer.writerow(row)
    
    print(f"Created entries CSV file: {output_file}")
    print(f"Wrote {len(filtered_entries)} entries")

def write_contact_info_csv(data: Dict, output_dir: str) -> None:
    """Write contact info data to a CSV file."""
    contact_info = data.get('contact_info', {})
    output_file = os.path.join(output_dir, "contact_info.csv")
    
    # Define headers and create placeholder for the first row of explanations
    headers = ["id", "value"]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header explanation row
        writer.writerow(["Contact information identifier", "Value for the contact information field"])
        
        # Write headers
        writer.writerow(headers)
        
        # Write data rows
        for key, value in contact_info.items():
            writer.writerow([key, value])
    
    print(f"Created contact info CSV file: {output_file}")

def write_text_blocks_csv(data: Dict, output_dir: str, doc_type: str) -> None:
    """Write text blocks data to a CSV file."""
    text_blocks = data.get('text_blocks', [])
    
    # Filter text blocks based on document type
    filtered_blocks = [block for block in text_blocks 
                      if doc_type in block.get('tags', [])]
    
    output_file = os.path.join(output_dir, "text_blocks.csv")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header explanation row
        writer.writerow(["Text block identifier", "The actual text content of the block"])
        
        # Write headers
        writer.writerow(["loc", "text"])
        
        # Write data rows
        for block in filtered_blocks:
            writer.writerow([block.get('id', ''), block.get('content', '')])
    
    print(f"Created text blocks CSV file: {output_file}")

def write_skills_csv(data: Dict, output_dir: str) -> None:
    """Write skills data to a CSV file."""
    skills_data = data.get('skills', [])
    output_file = os.path.join(output_dir, "language_skills.csv")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header explanation row
        writer.writerow(["Category", "Skill name", "Level (1-5)"])
        
        # Write headers
        writer.writerow(["category", "skill", "level"])
        
        # Write data rows
        for category_data in skills_data:
            category = category_data.get('category', '')
            for skill in category_data.get('skills', []):
                writer.writerow([
                    category,
                    skill.get('name', ''),
                    skill.get('level', 0)
                ])
    
    print(f"Created skills CSV file: {output_file}")

def write_aside_entries_csv(data: Dict, output_dir: str, doc_type: str) -> None:
    """
    Write aside entries data to CSV files.
    This creates both aside_sections.csv and aside_entries.csv.
    """
    # Check if the JSON has aside_entries and aside_sections
    # For now, we'll create placeholder files
    
    # Create aside_sections.csv
    sections_file = os.path.join(output_dir, "aside_sections.csv")
    with open(sections_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Section ID", "Section Title"])
        writer.writerow(["section", "title"])
        writer.writerow(["skills", "Skills & Expertise"])
        writer.writerow(["languages", "Languages"])
    
    print(f"Created aside sections CSV file: {sections_file}")
    
    # Create aside_entries.csv
    entries_file = os.path.join(output_dir, "aside_entries.csv")
    with open(entries_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Section ID", "Entry Title", "Entry Details (optional)"])
        writer.writerow(["section", "title", "detail"])
        
        # Add skills entries based on the skills data
        skills_data = data.get('skills', [])
        for category_data in skills_data:
            category = category_data.get('category', '')
            for skill in category_data.get('skills', []):
                writer.writerow([
                    "skills",
                    f"{category}: {skill.get('name', '')}",
                    f"Level: {skill.get('level', 0)}/5"
                ])
    
    print(f"Created aside entries CSV file: {entries_file}")

def convert_json_to_csv(json_path: str, output_dir: str, doc_type: str, 
                       company_filter: Optional[str] = None,
                       tag_filter: Optional[str] = None) -> None:
    """
    Convert the JSON data to CSV files.
    
    Args:
        json_path: Path to the JSON file
        output_dir: Directory to write CSV files
        doc_type: Type of document ('cv' or 'resume')
        company_filter: Optional filter for company
        tag_filter: Optional filter for tag
    """
    # Load JSON data
    data = load_json_data(json_path)
    
    # Ensure output directory exists
    ensure_output_dir(output_dir)
    
    # Write CSV files
    write_entries_csv(data, output_dir, doc_type, company_filter, tag_filter)
    write_contact_info_csv(data, output_dir)
    write_text_blocks_csv(data, output_dir, doc_type)
    write_skills_csv(data, output_dir)
    write_aside_entries_csv(data, output_dir, doc_type)
    
    print(f"Conversion completed. CSV files created in {output_dir}")

def main():
    """Main function to parse arguments and run the conversion."""
    parser = argparse.ArgumentParser(description='Convert JSON CV/Resume data to CSV format.')
    parser.add_argument('--json', required=True, help='Path to the JSON data file')
    parser.add_argument('--output-dir', required=True, help='Directory to output CSV files')
    parser.add_argument('--type', choices=['cv', 'resume'], required=True, 
                       help='Type of document to generate (cv or resume)')
    parser.add_argument('--filter-company', help='Filter entries by company')
    parser.add_argument('--filter-tag', help='Filter entries by tag')
    
    args = parser.parse_args()
    
    convert_json_to_csv(
        args.json, 
        args.output_dir, 
        args.type,
        args.filter_company,
        args.filter_tag
    )

if __name__ == "__main__":
    main()
