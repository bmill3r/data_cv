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
                     company_filters: Optional[List[str]] = None, 
                     tag_filters: Optional[List[str]] = None,
                     filter_logic: str = 'and') -> None:
    """
    Write entries data to a CSV file.
    
    Args:
        data: The JSON data
        output_dir: Directory to write the CSV file
        doc_type: Type of document ('cv' or 'resume')
        company_filters: Optional list of company filters
        tag_filters: Optional list of tag filters
        filter_logic: Logic to apply for filtering ('and' or 'or')
    """
    entries = data.get('entries', [])
    
    # Filter entries based on document type, companies, and tags
    filtered_entries = []
    for entry in entries:
        entry_tags = set(entry.get('tags', []))
        entry_companies = set(entry.get('companies', []))
        
        # Always check if entry is valid for the document type
        if doc_type not in entry_tags:
            continue
            
        # Apply company filters if specified
        if company_filters:
            # Check if any companies match (OR logic) or all companies match (AND logic)
            company_matches = []
            for company in company_filters:
                company_matches.append(company in entry_companies)
                
            if filter_logic.lower() == 'and' and not all(company_matches):
                continue
            elif filter_logic.lower() == 'or' and not any(company_matches):
                continue
                
        # Apply tag filters if specified
        if tag_filters:
            # Check if any tags match (OR logic) or all tags match (AND logic)
            tag_matches = []
            for tag in tag_filters:
                tag_matches.append(tag in entry_tags)
                
            if filter_logic.lower() == 'and' and not all(tag_matches):
                continue
            elif filter_logic.lower() == 'or' and not any(tag_matches):
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
    
    # Define headers using the correct format for the render.r script
    headers = ["loc", "icon", "contact"]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write headers directly - no explanation row needed for 2.0 format
        writer.writerow(headers)
        
        # Write data rows with full contact info
        if contact_info:
            for key, value in contact_info.items():
                # Extract the loc and icon from the key if it's in the format "loc_icon"
                loc = key
                icon = ""
                
                if "_" in key and key.count("_") == 1:
                    parts = key.split("_")
                    loc = parts[0]
                    icon = parts[1]
                
                # Check if value is a dict with the new format (value + icon)
                if isinstance(value, dict) and 'value' in value:
                    # Use the stored icon if available
                    contact_value = value['value']
                    icon = value.get('icon', icon)  # Use stored icon or fallback to parsed icon
                else:
                    # Handle legacy format where value is just a string
                    contact_value = value
                
                writer.writerow([loc, icon, contact_value])
        else:
            # If no contact info found, add placeholders
            common_fields = [
                {"loc": "email", "icon": "envelope", "contact": ""},
                {"loc": "phone", "icon": "phone", "contact": ""},
                {"loc": "website", "icon": "globe", "contact": ""},
                {"loc": "github", "icon": "github", "contact": ""},
                {"loc": "linkedin", "icon": "linkedin", "contact": ""}
            ]
            for field in common_fields:
                writer.writerow([field["loc"], field["icon"], field["contact"]])
    
    print(f"Created contact info CSV file with {len(contact_info) or len(common_fields)} fields: {output_file}")

def write_text_blocks_csv(data: Dict, output_dir: str, doc_type: str) -> None:
    """Write text blocks data to a CSV file."""
    text_blocks = data.get('text_blocks', [])
    
    # First, identify essential blocks (intro and professional_summary)
    essential_blocks = []
    essential_ids = ['intro', 'professional_summary']
    
    # Then get blocks filtered by document type
    type_filtered_blocks = []
    
    # Process all blocks
    for block in text_blocks:
        block_id = block.get('id', '')
        # Check if it's an essential block
        if block_id in essential_ids:
            essential_blocks.append(block)
        # Check if it has the right document type tag
        elif doc_type in block.get('tags', []):
            type_filtered_blocks.append(block)
    
    # Combine the lists, with essential blocks first
    # Use a dictionary to eliminate duplicates (in case an essential block also has the right tag)
    combined_blocks = {}
    for block in essential_blocks + type_filtered_blocks:
        block_id = block.get('id', '')
        if block_id and block_id not in combined_blocks:
            combined_blocks[block_id] = block
    
    # Convert back to a list
    filtered_blocks = list(combined_blocks.values())
    
    # Log what blocks we're including
    print(f"Including text blocks: {', '.join([block.get('id', 'Unknown') for block in filtered_blocks])}")
    
    output_file = os.path.join(output_dir, "text_blocks.csv")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Skip explanation row, just write direct headers
        # The R code expects 'loc' and 'text' as column names
        writer.writerow(["loc", "text"])
        
        # Write data rows with lots of validation
        for block in filtered_blocks:
            # Map 'id' to 'loc' and 'content' to 'text' to match what the R code expects
            loc = block.get('id', '')
            text_content = block.get('content', '')
            
            # Ensure we have valid data
            if not loc:
                print(f"WARNING: Block missing ID/loc value: {block}")
                continue
                
            if not text_content:
                print(f"WARNING: Block '{loc}' has empty content")
                text_content = "(No content provided)"
                
            writer.writerow([loc, text_content])
            print(f"  - Added block '{loc}' with {len(text_content)} chars of content")
            
        print(f"Text blocks conversion details:")
        for block in filtered_blocks:
            print(f"  - Block ID '{block.get('id', '')}': {len(block.get('content', ''))} characters")
    
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
    skills_data = data.get('skills', [])
    
    # Check if the JSON has skills data
    if not skills_data:
        print("No skills data found in the JSON file.")
        return
    
    # Create aside_sections.csv - with proper format matching the original CSV
    sections_file = os.path.join(output_dir, "aside_sections.csv")
    with open(sections_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Original CSV headers
        writer.writerow(["category", "display_name", "is_code", "sort_order"])
        
        # Write each skill category
        for i, category in enumerate(skills_data):
            # Default is_code to FALSE
            is_code = "FALSE"
            # If the category name contains keywords related to code, mark as TRUE
            code_keywords = ["software", "coding", "programming", "development", "package", "script"]
            if any(keyword in category.get('category', '').lower() for keyword in code_keywords):
                is_code = "TRUE"
                
            writer.writerow([
                # Create slug from category name
                category.get('category', '').lower().replace(' ', '_').replace('/', '_'),
                category.get('category', ''),  # display_name is the full category name
                is_code,
                i + 1  # sort_order
            ])
    
    print(f"Created aside sections CSV file with {len(skills_data)} categories: {sections_file}")
    
    # Create aside_entries.csv - with proper format matching the original CSV
    entries_file = os.path.join(output_dir, "aside_entries.csv")
    with open(entries_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Original CSV headers
        writer.writerow(["category", "entry", "sort_order"])
        
        # Write all skill entries
        entry_count = 0
        for category_data in skills_data:
            # Get the category slug
            category_slug = category_data.get('category', '').lower().replace(' ', '_').replace('/', '_')
            
            # Add each skill in this category
            for i, skill in enumerate(category_data.get('entries', [])):
                writer.writerow([
                    category_slug,
                    skill.get('name', ''),
                    i + 1  # sort_order within this category
                ])
                entry_count += 1
    
    print(f"Created aside entries CSV file with {entry_count} skills: {entries_file}")

def convert_json_to_csv(json_path: str, output_dir: str, doc_type: str, 
                       company_filters: Optional[List[str]] = None,
                       tag_filters: Optional[List[str]] = None,
                       filter_logic: str = 'and') -> None:
    """
    Convert the JSON data to CSV files.
    
    Args:
        json_path: Path to the JSON file
        output_dir: Directory to write CSV files
        doc_type: Type of document ('cv' or 'resume')
        company_filters: Optional filter for company
        tag_filters: Optional filter for tag
        filter_logic: Logic to apply for filtering multiple tags/companies: "and" requires all filters to match, "or" requires any filter to match
    """
    # Load JSON data
    data = load_json_data(json_path)
    
    # Ensure output directory exists
    ensure_output_dir(output_dir)
    
    # Write CSV files
    write_entries_csv(data, output_dir, doc_type, company_filters, tag_filters, filter_logic)
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
    parser.add_argument('--filter-company', help='Filter entries by company. Use comma-separated values for multiple companies')
    parser.add_argument('--filter-tag', help='Filter entries by tag. Use comma-separated values for multiple tags')
    parser.add_argument('--filter-logic', choices=['and', 'or'], default='and',
                       help='Logic to apply for filtering multiple tags/companies: "and" requires all filters to match, "or" requires any filter to match')
    
    args = parser.parse_args()
    
    # Convert comma-separated filters to lists if provided
    company_filters = None
    if args.filter_company:
        company_filters = [company.strip() for company in args.filter_company.split(',')]
        
    tag_filters = None
    if args.filter_tag:
        tag_filters = [tag.strip() for tag in args.filter_tag.split(',')]
    
    convert_json_to_csv(
        args.json, 
        args.output_dir, 
        args.type,
        company_filters,
        tag_filters,
        args.filter_logic
    )

if __name__ == "__main__":
    main()
