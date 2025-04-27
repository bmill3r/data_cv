#!/usr/bin/env python3
"""
AI-Powered CV/Resume Generator

This script takes a job posting as input, uses AI (OpenAI or Claude) to analyze the posting,
filters your CV/resume entries based on relevance, and generates a customized
CV/resume document.

Requirements:
    - pip install openai anthropic python-dotenv
    - AI API keys stored in .env file

Usage:
    python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" --type resume --ai-service openai
    python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" --type resume --ai-service claude
"""

import argparse
import json
import os
import sys
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union, Literal
from datetime import datetime
import platform
from pathlib import Path

# Third-party imports
try:
    from dotenv import load_dotenv
    from openai import OpenAI
    import anthropic
except ImportError:
    print("Missing required packages. Install with:")
    print("pip install openai anthropic python-dotenv")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

# Check if API keys are set
openai_key_present = "OPENAI_API_KEY" in os.environ
claude_key_present = "ANTHROPIC_API_KEY" in os.environ

if not openai_key_present and not claude_key_present:
    print("WARNING: Neither OPENAI_API_KEY nor ANTHROPIC_API_KEY environment variables are set.")
    print("Create a .env file in the same directory with your API keys:")
    print("OPENAI_API_KEY='your-openai-api-key'")
    print("ANTHROPIC_API_KEY='your-anthropic-api-key'")
    print("Continuing without API keys (you'll be prompted later)...")

def load_json_data(json_path: str) -> Dict:
    """Load and parse the JSON data from the specified file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        sys.exit(1)

def read_job_posting(file_path: str) -> str:
    """Read a job posting from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading job posting file: {e}")
        sys.exit(1)

def setup_ai_client(service: str = "openai") -> Tuple[Any, str]:
    """
    Set up and return an AI client (OpenAI or Claude).
    
    Args:
        service: Which AI service to use ("openai" or "claude")
        
    Returns:
        Tuple of (ai_client, service_name)
    """
    if service.lower() == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        
        # If no API key is set in the environment, prompt the user
        if not api_key:
            api_key = input("Enter your OpenAI API key: ").strip()
            if not api_key:
                print("No API key provided. Exiting.")
                sys.exit(1)
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        return client, "openai"
        
    elif service.lower() == "claude":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        # If no API key is set in the environment, prompt the user
        if not api_key:
            api_key = input("Enter your Anthropic API key: ").strip()
            if not api_key:
                print("No API key provided. Exiting.")
                sys.exit(1)
        
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=api_key)
        return client, "claude"
        
    else:
        print(f"Unsupported AI service: {service}")
        print("Supported services: openai, claude")
        sys.exit(1)

def analyze_job_posting(ai_client: Any, job_posting: str, service: str = "openai") -> Dict:
    """
    Use AI to analyze the job posting and extract key skills, 
    requirements, and other relevant information.
    
    Args:
        ai_client: AI client (OpenAI or Claude)
        job_posting: Text of the job posting
        service: Which AI service is being used
        
    Returns:
        Dictionary with analyzed job information
    """
    system_prompt = """
    You are an expert career counselor and resume specialist. Analyze the job posting and extract the following:
    1. Required skills and technologies
    2. Desired experience areas
    3. Key responsibilities
    4. Industry and domain-specific knowledge required
    5. Soft skills emphasized
    
    Format your response as a JSON object with these categories.
    """
    
    try:
        if service == "openai":
            response = ai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this job posting and extract the key information:\n\n{job_posting}"}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON from the response
            analysis = json.loads(response.choices[0].message.content)
            return analysis
            
        elif service == "claude":
            prompt = f"{system_prompt}\n\nAnalyze this job posting and extract the key information:\n\n{job_posting}"
            
            response = ai_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.0,
                system="You are an expert career counselor and resume specialist.",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON from the response
            analysis = json.loads(response.content[0].text)
            return analysis
    
    except Exception as e:
        print(f"Error analyzing job posting: {e}")
        sys.exit(1)

def score_entry_relevance(ai_client: Any, entry: Dict, job_analysis: Dict, service: str = "openai") -> Tuple[float, str, List[str]]:
    """
    Use AI to score the relevance of a CV/resume entry based on the job analysis.
    Returns a tuple of (score, reasoning, improved_descriptions) where score is between 0 and 10.
    
    Args:
        ai_client: AI client (OpenAI or Claude)
        entry: CV/resume entry to score
        job_analysis: Analysis of the job posting
        service: Which AI service is being used
        
    Returns:
        Tuple of (score, reasoning, improved_descriptions)
    """
    # Create a condensed version of the entry
    entry_text = f"""
    Title: {entry.get('title', '')}
    Section: {entry.get('section', '')}
    Institution: {entry.get('institution', '')}
    Descriptions:
    - {' '.join(entry.get('descriptions', []))}
    Tags: {', '.join(entry.get('tags', []))}
    """
    
    # Create a condensed version of the job analysis
    job_text = f"""
    Required Skills: {', '.join(job_analysis.get('Required skills and technologies', []))}
    Desired Experience: {', '.join(job_analysis.get('Desired experience areas', []))}
    Key Responsibilities: {', '.join(job_analysis.get('Key responsibilities', []))}
    Industry Knowledge: {', '.join(job_analysis.get('Industry and domain-specific knowledge required', []))}
    Soft Skills: {', '.join(job_analysis.get('Soft skills emphasized', []))}
    """
    
    system_prompt = """
    You are an expert career counselor and resume specialist. Score the relevance of this CV/resume entry 
    for the job described. Return a JSON object with:
    {
        "score": <score between 0 and 10, where 10 is extremely relevant>,
        "reasoning": "<brief explanation for the score>",
        "improved_descriptions": [
            "<suggestion for improved description 1>",
            "<suggestion for improved description 2>",
            ...
        ]
    }
    
    Focus on relevance, not just quality. An impressive entry that's irrelevant should score low.
    """
    
    try:
        if service == "openai":
            response = ai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Resume Entry:\n{entry_text}\n\nJob Details:\n{job_text}"}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON from the response
            result = json.loads(response.choices[0].message.content)
            return (result.get("score", 0), result.get("reasoning", ""), result.get("improved_descriptions", []))
            
        elif service == "claude":
            prompt = f"Resume Entry:\n{entry_text}\n\nJob Details:\n{job_text}"
            
            response = ai_client.messages.create(
                model="claude-3-haiku-20240307",  # Using a faster, cheaper model for individual entry scoring
                max_tokens=1000,
                temperature=0.0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON from the response
            result = json.loads(response.content[0].text)
            return (result.get("score", 0), result.get("reasoning", ""), result.get("improved_descriptions", []))
    
    except Exception as e:
        print(f"Error scoring entry relevance: {e}")
        return (0, f"Error: {str(e)}", [])

def create_tailored_json(
    cv_data: Dict, 
    job_analysis: Dict, 
    ai_client: Any,
    output_path: str,
    max_entries_per_section: Dict[str, int] = None,
    improve_descriptions: bool = True,
    service: str = "openai"
) -> None:
    """
    Create a tailored version of the CV/resume JSON file with entries
    scored and filtered based on relevance to the job posting.
    
    Args:
        cv_data: The original CV/resume JSON data
        job_analysis: Analysis of the job posting
        openai_client: OpenAI client
        output_path: Path to save the tailored JSON
        max_entries_per_section: Dictionary mapping sections to max number of entries to include
        improve_descriptions: Whether to improve descriptions with AI suggestions
    """
    # Create a deep copy of the CV data
    tailored_data = {
        "meta": cv_data.get("meta", {}),
        "contact_info": cv_data.get("contact_info", {}),
        "skills": cv_data.get("skills", []),
        "text_blocks": cv_data.get("text_blocks", [])
    }
    
    # Update meta information
    tailored_data["meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    tailored_data["meta"]["generated_for"] = "Job Application"
    tailored_data["meta"]["original_file"] = "cv_data.json"
    
    # Default max entries per section if not provided
    if max_entries_per_section is None:
        max_entries_per_section = {
            "current_position": 2,
            "education": 2,
            "research_positions": 3,
            "awards_and_honors": 3,
            "teaching_positions": 2,
            "academic_articles": 3,
            "software": 3,
            "invited_speaker": 2,
            "mentorship": 2
        }
    
    # Process and score each entry
    scored_entries = []
    print("\nScoring CV/resume entries for relevance...")
    for idx, entry in enumerate(cv_data.get("entries", [])):
        print(f"Processing entry {idx+1}/{len(cv_data.get('entries', []))}: {entry.get('title', '')}")
        score, reasoning, improved_descriptions = score_entry_relevance(ai_client, entry, job_analysis, service)
        
        # Create a copy of the entry with score information
        scored_entry = entry.copy()
        scored_entry["relevance_score"] = score
        scored_entry["relevance_reasoning"] = reasoning
        
        # Update descriptions if improvement is enabled and suggestions are available
        if improve_descriptions and improved_descriptions:
            print(f"  - Improving descriptions for: {entry.get('title', '')}")
            scored_entry["original_descriptions"] = entry.get("descriptions", []).copy()
            scored_entry["descriptions"] = improved_descriptions
        
        scored_entries.append(scored_entry)
        print(f"  - Score: {score}/10 - {reasoning[:50]}...")
    
    # Group entries by section
    section_entries = {}
    for entry in scored_entries:
        section = entry.get("section", "other")
        if section not in section_entries:
            section_entries[section] = []
        section_entries[section].append(entry)
    
    # Sort entries by relevance score and select top entries for each section
    tailored_entries = []
    for section, entries in section_entries.items():
        # Sort by relevance score (highest first)
        entries.sort(key=lambda e: e.get("relevance_score", 0), reverse=True)
        
        # Get the maximum number of entries for this section
        max_entries = max_entries_per_section.get(section, 2)
        
        # Take top entries but ensure we don't take very low-scoring entries
        selected_entries = [e for e in entries[:max_entries] if e.get("relevance_score", 0) >= 3]
        
        # Add to our tailored entries list
        tailored_entries.extend(selected_entries)
    
    # Add the tailored entries to our output data
    tailored_data["entries"] = tailored_entries
    
    # Save the tailored JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tailored_data, f, indent=2)
    
    print(f"\nTailored JSON file created: {output_path}")
    print(f"Selected {len(tailored_entries)} entries out of {len(cv_data.get('entries', []))} original entries")

def create_tailored_cv_with_prompt(
    ai_client: Any, 
    cv_data: Dict, 
    job_posting: str, 
    output_path: str,
    service: str = "openai"
) -> None:
    """
    Create a tailored version of the CV directly using a structured prompt.
    
    Args:
        ai_client: AI client (OpenAI or Claude)
        cv_data: The original CV/resume JSON data
        job_posting: The text of the job posting
        output_path: Path to save the tailored JSON
        service: Which AI service is being used
    """
    # Convert CV data to a string representation
    cv_json_str = json.dumps(cv_data, indent=2)
    
    system_prompt = """
    You are an expert CV/resume tailoring assistant. Your task is to analyze a job posting and a CV/resume database,
    then create a tailored version of the CV/resume that highlights the most relevant skills and experience for the job.
    
    Your output must be a valid JSON object following the same structure as the input CV data, but with:
    1. Only the most relevant entries included (max 2-3 per section)
    2. Descriptions rewritten to highlight relevant skills and experience
    3. A tailored professional summary
    
    The output must be valid JSON that can be parsed with json.loads().
    """
    
    user_prompt = f"""
    # Job Posting
    
    {job_posting}
    
    # CV Database (JSON)
    
    ```json
    {cv_json_str}
    ```
    
    Analyze the job posting and CV database, then create a tailored version of the CV that highlights the most relevant skills and experience for this job.
    
    Your response must be only the valid JSON object for the tailored CV, following the same structure as the input.
    """
    
    try:
        print("Generating tailored CV using AI prompt...")
        
        if service == "openai":
            response = ai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            tailored_cv_json = response.choices[0].message.content
            
        elif service == "claude":
            response = ai_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            tailored_cv_json = response.content[0].text
        
        # Parse the JSON to ensure it's valid
        tailored_cv = json.loads(tailored_cv_json)
        
        # Save the tailored CV
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tailored_cv, f, indent=2)
            
        print(f"Tailored CV saved to {output_path}")
        
    except Exception as e:
        print(f"Error creating tailored CV: {e}")
        print("Falling back to default tailoring method...")
        create_tailored_json(cv_data, analyze_job_posting(ai_client, job_posting, service), 
                            ai_client, output_path, service=service)

def main():
    """Main function to generate a tailored CV/resume."""
    parser = argparse.ArgumentParser(description="Generate a tailored CV/resume based on a job posting")
    parser.add_argument("--job-posting", required=True, help="Path to the job posting text file")
    parser.add_argument("--cv-data", default="cv_database.json", help="Path to the CV/resume JSON data file")
    parser.add_argument("--output-dir", default="output", help="Directory to save the output files")
    parser.add_argument("--output-name", help="Base name for output files (without extension)")
    parser.add_argument("--type", choices=["cv", "resume"], default="resume", help="Document type to generate")
    parser.add_argument("--improve-descriptions", action="store_true", help="Use AI to improve entry descriptions")
    parser.add_argument("--json-only", action="store_true", help="Only generate the JSON file, not the document")
    parser.add_argument("--use-prompt-only", action="store_true", help="Use direct prompt for CV tailoring instead of entry-by-entry analysis")
    parser.add_argument("--ai-service", choices=["openai", "claude"], default="openai", help="AI service to use (openai or claude)")
    parser.add_argument("--entries-per-section", help="JSON string mapping sections to max entries (e.g., '{\"education\": 2}')")
    
    args = parser.parse_args()
    
    # Prepare paths and directories
    output_dir = f"my_{args.type}_data"
    
    # Load the CV/resume data
    print("\nLoading CV/resume data...")
    cv_data = load_json_data(args.cv_data)
    print(f"Loaded {len(cv_data.get('entries', []))} entries from {args.cv_data}")
    
    # Read the job posting
    print("\nReading job posting...")
    job_posting = read_job_posting(args.job_posting)
    print(f"Read {len(job_posting)} characters from {args.job_posting}")
    
    # Setup AI client (OpenAI or Claude)
    ai_client, service = setup_ai_client(args.ai_service)
    
    # Analyze the job posting
    job_analysis = analyze_job_posting(ai_client, job_posting, service)
    print("Job analysis complete. Extracted key requirements:")
    for category, items in job_analysis.items():
        print(f"  - {category}: {', '.join(items[:3])}...")
    
    # Create a tailored professional summary
    print("\nCreating job-specific professional summary...")
    updated_summary = create_job_specific_summary(ai_client, cv_data, job_analysis, service)
    
    # Update the professional summary in the CV data
    for block in cv_data.get("text_blocks", []):
        if block.get("id") == "professional_summary":
            print(f"Original summary: {block.get('content', '')[:50]}...")
            block["content"] = updated_summary
            print(f"Updated summary: {updated_summary[:50]}...")
            break
    
    # Create a tailored JSON file with only the most relevant entries
    if args.use_prompt_only:
        # Use the direct prompt approach for tailoring
        create_tailored_cv_with_prompt(
            ai_client,
            cv_data,
            job_posting,
            f"{args.output_dir}/{args.output_name}.json",
            service=service
        )
    else:
        # Use the detailed entry-by-entry analysis
        create_tailored_json(
            cv_data, 
            job_analysis, 
            ai_client, 
            f"{args.output_dir}/{args.output_name}.json", 
            max_entries_per_section=json.loads(args.entries_per_section) if args.entries_per_section else None,
            improve_descriptions=args.improve_descriptions,
            service=service
        )
    
    # Run the converter script
    print("\nConverting tailored JSON to CSV...")
    if not run_converter_script(f"{args.output_dir}/{args.output_name}.json", output_dir, args.type):
        print("Error: Failed to convert JSON to CSV. Exiting.")
        sys.exit(1)
    
    # 8. Run the render script
    print("\nRendering final document...")
    if not run_render_script(template_name, args.output_name, args.html):
        print("Error: Failed to render document. Exiting.")
        sys.exit(1)
    
    print(f"\nSuccess! Tailored {args.type.upper()} created: output/{args.output_name}.pdf")
    if args.html:
        print(f"HTML version also available: output/{args.output_name}.html")
    
    print("\nAI-assisted improvements:")
    print("1. Created a job-specific professional summary")
    print("2. Selected the most relevant entries based on job requirements")
    if args.improve_descriptions:
        print("3. Improved entry descriptions to better match job requirements")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
