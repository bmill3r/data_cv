#!/usr/bin/env python3
"""
CV Database Editor

This script provides a simple way to add new entries to your cv_database.json file
or edit existing ones without manually editing the JSON.

Usage:
    # Add a new entry
    python cv_database_editor.py add-entry --database cv_database.json
    
    # Edit an existing entry
    python cv_database_editor.py edit-entry --database cv_database.json --entry-id 5
    
    # Add a new skill category
    python cv_database_editor.py add-skill-category --database cv_database.json
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime

def load_database(database_path: str) -> Dict:
    """Load the CV database from a JSON file."""
    try:
        if os.path.exists(database_path):
            with open(database_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create a new database structure if the file doesn't exist
            return {
                'meta': {
                    'last_updated': datetime.now().strftime("%Y-%m-%d"),
                    'generated_by': 'cv_database_editor.py'
                },
                'contact_info': {},
                'entries': [],
                'text_blocks': [],
                'skills': []
            }
    except Exception as e:
        print(f"Error loading database: {e}")
        sys.exit(1)

def save_database(database: Dict, database_path: str) -> None:
    """Save the CV database to a JSON file."""
    try:
        # Update last_updated timestamp
        database['meta']['last_updated'] = datetime.now().strftime("%Y-%m-%d")
        
        with open(database_path, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved database to {database_path}")
    except Exception as e:
        print(f"Error saving database: {e}")
        sys.exit(1)

def add_entry(database: Dict) -> None:
    """Add a new entry to the database."""
    new_entry = {}
    
    # Show available sections in a user-friendly format
    sections = sorted(set(entry.get('section', '') for entry in database.get('entries', []) if entry.get('section')))
    
    if sections:
        print("\nAvailable sections:")
        for i, section in enumerate(sections, 1):
            print(f"  {i}. {section}")
    else:
        print("\nNo existing sections. You can create a new one.")
    
    # Prompt for section with options to use existing or create new
    print("\nChoose a section:")
    print("  [number] - Use an existing section (enter the number)")
    print("  [name] - Create a new section (enter a new name)")
    print("  [n] - Create a new section (you'll be prompted for the name)")
    
    section_choice = input("Section choice: ")
    
    # Process section choice
    if section_choice.lower() == 'n':
        # User wants to create a new section
        new_section = input("Enter new section name: ")
        new_entry['section'] = new_section
        print(f"Created new section: '{new_section}'")
    else:
        try:
            # Check if the input is a number referencing an existing section
            section_index = int(section_choice) - 1
            if 0 <= section_index < len(sections):
                new_entry['section'] = sections[section_index]
                print(f"Using existing section: '{sections[section_index]}'")
            else:
                print(f"Invalid section number. Creating new section: '{section_choice}'")
                new_entry['section'] = section_choice
        except ValueError:
            # Input is not a number, treat it as a new section name
            new_entry['section'] = section_choice
            print(f"Creating new section: '{section_choice}'")
    
    # Continue with other entry details
    new_entry['title'] = input("\nTitle: ")
    new_entry['institution'] = input("Institution/Company: ")
    new_entry['loc'] = input("Location: ")
    new_entry['start'] = input("Start date (e.g., 2020): ")
    new_entry['end'] = input("End date (e.g., 2022, or 'Current'): ")
    
    # Get descriptions
    descriptions = []
    while True:
        desc = input("Description (leave empty to finish): ")
        if not desc:
            break
        descriptions.append(desc)
    new_entry['descriptions'] = descriptions
    
    # Get companies
    companies = []
    while True:
        company = input("Company tag (leave empty to finish): ")
        if not company:
            break
        companies.append(company)
    new_entry['companies'] = companies
    
    # Get tags
    tags = []
    cv_tag = input("Include in CV? (y/n): ").lower()
    if cv_tag == 'y':
        tags.append('cv')
    resume_tag = input("Include in resume? (y/n): ").lower()
    if resume_tag == 'y':
        tags.append('resume')
    
    while True:
        tag = input("Additional tag (leave empty to finish): ")
        if not tag:
            break
        tags.append(tag)
    new_entry['tags'] = tags
    
    # Set importance
    importance_str = input("Importance (0-10, higher values are more important): ")
    try:
        importance = int(importance_str) if importance_str else 5
        new_entry['importance'] = importance
    except ValueError:
        print("Invalid importance value, defaulting to 5")
        new_entry['importance'] = 5
    
    # Add entry to database
    database['entries'].append(new_entry)
    print("Entry added successfully!")

def edit_entry(database: Dict, entry_id: int) -> None:
    """Edit an existing entry in the database."""
    entries = database.get('entries', [])
    
    if not entries:
        print("No entries in the database.")
        return
    
    if entry_id < 0 or entry_id >= len(entries):
        print(f"Invalid entry ID. Valid IDs are 0-{len(entries)-1}")
        return
    
    entry = entries[entry_id]
    print(f"\nEditing entry {entry_id}:")
    print(f"Current value: {json.dumps(entry, indent=2)}")
    
    # Show available sections in a user-friendly format
    current_section = entry.get('section', '')
    sections = sorted(set(e.get('section', '') for e in database.get('entries', []) if e.get('section')))
    
    if sections:
        print("\nAvailable sections:")
        for i, section in enumerate(sections, 1):
            indicator = "*" if section == current_section else " "
            print(f"  {indicator} {i}. {section}")
        print("  (* = current section)")
    else:
        print("\nNo existing sections.")
    
    # Prompt for section with options to use existing or create new
    print("\nChoose a section:")
    print(f"  [Enter] - Keep current section '{current_section}'")
    print("  [number] - Use an existing section (enter the number)")
    print("  [name] - Create a new section (enter a new name)")
    print("  [n] - Create a new section (you'll be prompted for the name)")
    
    section_choice = input("Section choice: ")
    
    # Process section choice
    if not section_choice:
        # Keep current section
        print(f"Keeping current section: '{current_section}'")
    elif section_choice.lower() == 'n':
        # User wants to create a new section
        new_section = input("Enter new section name: ")
        entry['section'] = new_section
        print(f"Created new section: '{new_section}'")
    else:
        try:
            # Check if the input is a number referencing an existing section
            section_index = int(section_choice) - 1
            if 0 <= section_index < len(sections):
                entry['section'] = sections[section_index]
                print(f"Using existing section: '{sections[section_index]}'")
            else:
                print(f"Invalid section number. Creating new section: '{section_choice}'")
                entry['section'] = section_choice
        except ValueError:
            # Input is not a number, treat it as a new section name
            entry['section'] = section_choice
            print(f"Creating new section: '{section_choice}'")
    
    # Continue with other entry details
    entry['title'] = input(f"\nTitle [{entry.get('title', '')}]: ") or entry.get('title', '')
    entry['institution'] = input(f"Institution/Company [{entry.get('institution', '')}]: ") or entry.get('institution', '')
    entry['loc'] = input(f"Location [{entry.get('loc', '')}]: ") or entry.get('loc', '')
    entry['start'] = input(f"Start date [{entry.get('start', '')}]: ") or entry.get('start', '')
    entry['end'] = input(f"End date [{entry.get('end', '')}]: ") or entry.get('end', '')
    
    # Update descriptions
    current_descriptions = entry.get('descriptions', [])
    print("Current descriptions:")
    for i, desc in enumerate(current_descriptions):
        print(f"  {i}: {desc}")
    
    edit_descriptions = input("Edit descriptions? (y/n): ").lower()
    if edit_descriptions == 'y':
        new_descriptions = []
        i = 0
        while True:
            default = current_descriptions[i] if i < len(current_descriptions) else ""
            desc = input(f"Description {i} [{default}] (leave empty to finish if adding new): ")
            if not desc and i >= len(current_descriptions):
                break
            if desc or i < len(current_descriptions):
                new_descriptions.append(desc or default)
                i += 1
            else:
                break
        entry['descriptions'] = new_descriptions
    
    # Update companies
    current_companies = entry.get('companies', [])
    print("Current companies:", ', '.join(current_companies) if current_companies else "None")
    
    edit_companies = input("Edit companies? (y/n): ").lower()
    if edit_companies == 'y':
        new_companies = []
        while True:
            company = input("Company tag (leave empty to finish): ")
            if not company:
                break
            new_companies.append(company)
        entry['companies'] = new_companies
    
    # Update tags
    current_tags = entry.get('tags', [])
    print("Current tags:", ', '.join(current_tags) if current_tags else "None")
    
    edit_tags = input("Edit tags? (y/n): ").lower()
    if edit_tags == 'y':
        tags = []
        cv_tag = input("Include in CV? (y/n): ").lower()
        if cv_tag == 'y':
            tags.append('cv')
        resume_tag = input("Include in resume? (y/n): ").lower()
        if resume_tag == 'y':
            tags.append('resume')
        
        while True:
            tag = input("Additional tag (leave empty to finish): ")
            if not tag:
                break
            tags.append(tag)
        entry['tags'] = tags
    
    # Update importance
    current_importance = entry.get('importance', 0)
    importance_str = input(f"Importance (0-10, current: {current_importance}): ")
    if importance_str:
        try:
            entry['importance'] = int(importance_str)
        except ValueError:
            print("Invalid importance value, keeping current value")
    
    print("Entry updated successfully!")

def list_entries(database: Dict) -> None:
    """List all entries in the database with their IDs."""
    entries = database.get('entries', [])
    
    if not entries:
        print("No entries in the database.")
        return
    
    print(f"\nFound {len(entries)} entries:")
    for i, entry in enumerate(entries):
        print(f"{i}: {entry.get('title', 'Untitled')} - {entry.get('institution', 'No institution')} ({entry.get('start', '')} - {entry.get('end', '')})")
        print(f"   Section: {entry.get('section', 'None')}, Tags: {', '.join(entry.get('tags', []))}")
        print()

def add_skill_category(database: Dict) -> None:
    """Add a new skill category and its entries."""
    new_category = {}
    
    # Prompt for category details
    new_category['category'] = input("Skill category name: ")
    
    # Get entries
    entries = []
    print("Add skills to this category (name and level):")
    while True:
        name = input("Skill name (leave empty to finish): ")
        if not name:
            break
        
        level = input("Skill level (e.g., Proficient, 5/5): ")
        entries.append({
            'name': name,
            'level': level
        })
    
    new_category['entries'] = entries
    
    # Get tags
    tags = []
    cv_tag = input("Include in CV? (y/n): ").lower()
    if cv_tag == 'y':
        tags.append('cv')
    resume_tag = input("Include in resume? (y/n): ").lower()
    if resume_tag == 'y':
        tags.append('resume')
    new_category['tags'] = tags
    
    # Add category to database
    database['skills'].append(new_category)
    print("Skill category added successfully!")

def edit_contact_info(database: Dict) -> None:
    """Edit contact information in the database."""
    contact_info = database.get('contact_info', {})
    
    print("Current contact information:")
    for key, value in contact_info.items():
        print(f"  {key}: {value}")
    
    print("\nEdit contact information (leave empty to keep current value):")
    
    # Common contact fields
    fields = [
        'name', 'position', 'email', 'phone', 'website',
        'github', 'linkedin', 'address', 'twitter'
    ]
    
    # Ask about each field
    for field in fields:
        current_value = contact_info.get(field, '')
        new_value = input(f"{field} [{current_value}]: ") or current_value
        if new_value:
            contact_info[field] = new_value
    
    # Ask for any additional fields
    while True:
        field = input("Additional field name (leave empty to finish): ")
        if not field:
            break
        
        current_value = contact_info.get(field, '')
        new_value = input(f"{field} [{current_value}]: ") or current_value
        contact_info[field] = new_value
    
    database['contact_info'] = contact_info
    print("Contact information updated successfully!")

def list_skill_categories(database: Dict) -> None:
    """List all skill categories in the database with their IDs."""
    skills = database.get('skills', [])
    
    if not skills:
        print("No skill categories in the database.")
        return
    
    print("\nSkill Categories:")
    for i, skill in enumerate(skills):
        print(f"ID: {i} - {skill.get('category', '(No name)')} - Tags: {', '.join(skill.get('tags', []))}")
        entries = skill.get('entries', [])
        if entries:
            print(f"  Entries: {len(entries)} skills")

def edit_skill_category(database: Dict, category_id: int) -> None:
    """Edit an existing skill category in the database."""
    skills = database.get('skills', [])
    
    if not skills:
        print("No skill categories in the database.")
        return
    
    if category_id < 0 or category_id >= len(skills):
        print(f"Invalid skill category ID. Valid IDs are 0-{len(skills)-1}")
        return
    
    category = skills[category_id]
    print(f"\nEditing skill category {category_id}:")
    print(f"Current category: {json.dumps(category, indent=2)}")
    
    # Prompt for new values, defaulting to current values
    category['category'] = input(f"Category name [{category.get('category', '')}]: ") or category.get('category', '')
    
    # Update entries
    current_entries = category.get('entries', [])
    print("\nCurrent skills:")
    for i, entry in enumerate(current_entries):
        print(f"  {i}: {entry.get('name', '')} - {entry.get('level', '')}")
    
    edit_entries = input("\nEdit skills? (y/n): ").lower()
    if edit_entries == 'y':
        # Option to add, edit, or remove entries
        while True:
            print("\nOptions:")
            print("1. Add a new skill")
            print("2. Edit an existing skill")
            print("3. Remove a skill")
            print("4. Done editing skills")
            choice = input("Choose an option (1-4): ")
            
            if choice == '1':
                # Add a new skill
                name = input("Skill name: ")
                level = input("Skill level (e.g., Proficient, 5/5): ")
                current_entries.append({
                    'name': name,
                    'level': level
                })
                print("Skill added.")
            elif choice == '2':
                # Edit an existing skill
                try:
                    entry_id = int(input(f"Skill ID to edit (0-{len(current_entries)-1}): "))
                    if 0 <= entry_id < len(current_entries):
                        entry = current_entries[entry_id]
                        entry['name'] = input(f"Skill name [{entry.get('name', '')}]: ") or entry.get('name', '')
                        entry['level'] = input(f"Skill level [{entry.get('level', '')}]: ") or entry.get('level', '')
                        print("Skill updated.")
                    else:
                        print("Invalid skill ID.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            elif choice == '3':
                # Remove a skill
                try:
                    entry_id = int(input(f"Skill ID to remove (0-{len(current_entries)-1}): "))
                    if 0 <= entry_id < len(current_entries):
                        removed = current_entries.pop(entry_id)
                        print(f"Removed skill: {removed.get('name', '')}.")
                    else:
                        print("Invalid skill ID.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please select 1-4.")
        
        category['entries'] = current_entries
    
    # Update tags
    current_tags = category.get('tags', [])
    print(f"\nCurrent tags: {', '.join(current_tags) if current_tags else 'None'}")
    
    edit_tags = input("Edit tags? (y/n): ").lower()
    if edit_tags == 'y':
        tags = []
        cv_tag = input("Include in CV? (y/n): ").lower()
        if cv_tag == 'y':
            tags.append('cv')
        resume_tag = input("Include in resume? (y/n): ").lower()
        if resume_tag == 'y':
            tags.append('resume')
        
        while True:
            tag = input("Additional tag (leave empty to finish): ")
            if not tag:
                break
            tags.append(tag)
        category['tags'] = tags
    
    print("Skill category updated successfully!")

def list_text_blocks(database: Dict) -> None:
    """List all text blocks in the database with their IDs."""
    text_blocks = database.get('text_blocks', [])
    
    if not text_blocks:
        print("No text blocks in the database.")
        return
    
    print("\nText Blocks:")
    for i, block in enumerate(text_blocks):
        print(f"ID: {i} - {block.get('id', '(No ID)')} - Tags: {', '.join(block.get('tags', []))}")
        content_preview = block.get('content', '')[:50] + ('...' if len(block.get('content', '')) > 50 else '')
        print(f"  Content: {content_preview}")

def edit_text_block(database: Dict, block_id: int) -> None:
    """Edit an existing text block in the database."""
    text_blocks = database.get('text_blocks', [])
    
    if not text_blocks:
        print("No text blocks in the database.")
        return
    
    if block_id < 0 or block_id >= len(text_blocks):
        print(f"Invalid text block ID. Valid IDs are 0-{len(text_blocks)-1}")
        return
    
    block = text_blocks[block_id]
    print(f"\nEditing text block {block_id}:")
    print(f"Current text block ID: {block.get('id', '')}")
    print(f"Current content: {block.get('content', '')}")
    print(f"Current tags: {', '.join(block.get('tags', []))}")
    
    # Prompt for new values, defaulting to current values
    block['id'] = input(f"Block ID [{block.get('id', '')}]: ") or block.get('id', '')
    
    # Update content
    edit_content = input("\nEdit content? (y/n): ").lower()
    if edit_content == 'y':
        print("Enter new content (press Enter then Ctrl+D or Ctrl+Z on empty line to finish):")
        content_lines = []
        while True:
            try:
                line = input()
                content_lines.append(line)
            except EOFError:
                break
        
        # If we got at least one line or the user deliberately cleared the content
        if content_lines or edit_content == 'y':
            block['content'] = '\n'.join(content_lines)
    
    # Update tags
    current_tags = block.get('tags', [])
    print(f"\nCurrent tags: {', '.join(current_tags) if current_tags else 'None'}")
    
    edit_tags = input("Edit tags? (y/n): ").lower()
    if edit_tags == 'y':
        tags = []
        cv_tag = input("Include in CV? (y/n): ").lower()
        if cv_tag == 'y':
            tags.append('cv')
        resume_tag = input("Include in resume? (y/n): ").lower()
        if resume_tag == 'y':
            tags.append('resume')
        
        while True:
            tag = input("Additional tag (leave empty to finish): ")
            if not tag:
                break
            tags.append(tag)
        block['tags'] = tags
    
    print("Text block updated successfully!")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='CV Database Editor')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add entry command
    add_entry_parser = subparsers.add_parser('add-entry', help='Add a new entry')
    add_entry_parser.add_argument('--database', default='cv_database.json', help='Path to the database file')
    
    # Edit entry command
    edit_entry_parser = subparsers.add_parser('edit-entry', help='Edit an existing entry')
    edit_entry_parser.add_argument('--database', default='cv_database.json', help='Path to the database file')
    edit_entry_parser.add_argument('--entry-id', type=int, required=True, help='ID of the entry to edit')
    
    # List entries command
    list_entries_parser = subparsers.add_parser('list-entries', help='List all entries with their IDs')
    list_entries_parser.add_argument('--database', default='cv_database.json', help='Path to the database file')
    
    # Add skill category command
    add_skill_parser = subparsers.add_parser('add-skill-category', help='Add a new skill category')
    add_skill_parser.add_argument('--database', default='cv_database.json', help='Path to the database file')
    
    # List skill categories command
    list_skills_parser = subparsers.add_parser('list-skill-categories', help='List all skill categories with their IDs')
    list_skills_parser.add_argument('--database', default='cv_database.json', help='Path to the database file')
    
    # Edit skill category command
    edit_skill_parser = subparsers.add_parser('edit-skill-category', help='Edit an existing skill category')
    edit_skill_parser.add_argument('--database', default='cv_database.json', help='Path to the database file')
    edit_skill_parser.add_argument('--category-id', type=int, required=True, help='ID of the skill category to edit')
    
    # List text blocks command
    list_text_blocks_parser = subparsers.add_parser('list-text-blocks', help='List all text blocks with their IDs')
    list_text_blocks_parser.add_argument('--database', default='cv_database.json', help='Path to the database file')
    
    # Edit text block command
    edit_text_block_parser = subparsers.add_parser('edit-text-block', help='Edit an existing text block')
    edit_text_block_parser.add_argument('--database', default='cv_database.json', help='Path to the database file')
    edit_text_block_parser.add_argument('--block-id', type=int, required=True, help='ID of the text block to edit')
    
    # Edit contact info command
    edit_contact_parser = subparsers.add_parser('edit-contact', help='Edit contact information')
    edit_contact_parser.add_argument('--database', default='cv_database.json', help='Path to the database file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load the database
    database = load_database(args.database)
    
    # Execute the requested command
    if args.command == 'add-entry':
        add_entry(database)
        save_database(database, args.database)
    elif args.command == 'edit-entry':
        edit_entry(database, args.entry_id)
        save_database(database, args.database)
    elif args.command == 'list-entries':
        list_entries(database)
    elif args.command == 'add-skill-category':
        add_skill_category(database)
        save_database(database, args.database)
    elif args.command == 'list-skill-categories':
        list_skill_categories(database)
    elif args.command == 'edit-skill-category':
        edit_skill_category(database, args.category_id)
        save_database(database, args.database)
    elif args.command == 'list-text-blocks':
        list_text_blocks(database)
    elif args.command == 'edit-text-block':
        edit_text_block(database, args.block_id)
        save_database(database, args.database)
    elif args.command == 'edit-contact':
        edit_contact_info(database)
        save_database(database, args.database)

if __name__ == "__main__":
    main()
