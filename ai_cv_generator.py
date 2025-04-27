#!/usr/bin/env python3
"""
AI-Powered CV/Resume Generator

This script takes a job posting as input, uses OpenAI's API to analyze the posting,
filters your CV/resume entries based on relevance, and generates a customized
CV/resume document.

Requirements:
    - pip install openai
    - An OpenAI API key stored in the OPENAI_API_KEY environment variable

Usage:
    python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" --type resume
"""

import argparse
import json
import os
import sys
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import openai

# Check if OpenAI API key is set
if "OPENAI_API_KEY" not in os.environ:
    print("WARNING: OPENAI_API_KEY environment variable not set.")
    print("Set it with: export OPENAI_API_KEY='your-api-key'")
    print("Continuing without API key (you'll be prompted later)...")

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

def setup_openai_client() -> Any:
    """Set up and return an OpenAI client."""
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # If no API key is set in the environment, prompt the user
    if not api_key:
        api_key = input("Enter your OpenAI API key: ").strip()
        if not api_key:
            print("No API key provided. Exiting.")
            sys.exit(1)
    
    # Set the API key for the openai module
    openai.api_key = api_key
    
    return openai

def analyze_job_posting(openai_client: Any, job_posting: str) -> Dict:
    """
    Use OpenAI to analyze the job posting and extract key skills, 
    requirements, and other relevant information.
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
        response = openai_client.chat.completions.create(
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
    
    except Exception as e:
        print(f"Error analyzing job posting: {e}")
        sys.exit(1)

def score_entry_relevance(openai_client: Any, entry: Dict, job_analysis: Dict) -> Tuple[float, str]:
    """
    Use OpenAI to score the relevance of a CV/resume entry based on the job analysis.
    Returns a tuple of (score, reasoning) where score is between 0 and 10.
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
        response = openai_client.chat.completions.create(
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
    
    except Exception as e:
        print(f"Error scoring entry relevance: {e}")
        return (0, f"Error: {str(e)}", [])

def create_tailored_json(
    cv_data: Dict, 
    job_analysis: Dict, 
    openai_client: Any,
    output_path: str,
    max_entries_per_section: Dict[str, int] = None,
    improve_descriptions: bool = True
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
        score, reasoning, improved_descriptions = score_entry_relevance(openai_client, entry, job_analysis)
        
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

def extract_job_skills(job_analysis: Dict) -> List[str]:
    """Extract and flatten all skills from the job analysis."""
    skills = []
    
    # Extract skills from all relevant sections of the job analysis
    for section in ["Required skills and technologies", "Desired experience areas", 
                  "Key responsibilities", "Industry and domain-specific knowledge required"]:
        if section in job_analysis:
            if isinstance(job_analysis[section], list):
                skills.extend(job_analysis[section])
            elif isinstance(job_analysis[section], str):
                skills.append(job_analysis[section])
    
    return skills

def create_job_specific_summary(openai_client: Any, cv_data: Dict, job_analysis: Dict) -> str:
    """Create a job-specific professional summary."""
    # Extract information from CV and job posting
    skills = extract_job_skills(job_analysis)
    
    # Get existing text blocks
    text_blocks = cv_data.get("text_blocks", [])
    current_summary = ""
    for block in text_blocks:
        if block.get("id") == "professional_summary":
            current_summary = block.get("content", "")
            break
    
    system_prompt = """
    You are an expert career counselor and resume specialist. Create a tailored professional 
    summary for a resume based on the candidate's existing summary and the job requirements.
    Focus on highlighting the most relevant skills and experiences that match the job posting.
    Keep the summary concise (maximum 3 sentences) and impactful.
    """
    
    user_content = f"""
    Current Professional Summary: {current_summary}
    
    Job Requirements:
    - Required Skills: {', '.join(job_analysis.get('Required skills and technologies', []))}
    - Desired Experience: {', '.join(job_analysis.get('Desired experience areas', []))}
    - Key Responsibilities: {', '.join(job_analysis.get('Key responsibilities', []))}
    - Industry Knowledge: {', '.join(job_analysis.get('Industry and domain-specific knowledge required', []))}
    
    Please create a tailored professional summary highlighting the candidate's most relevant skills and experience for this specific job.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        
        # Get the new summary from the response
        new_summary = response.choices[0].message.content.strip()
        return new_summary
    
    except Exception as e:
        print(f"Error creating job-specific summary: {e}")
        return current_summary

def run_converter_script(json_path: str, output_dir: str, doc_type: str) -> bool:
    """
    Run the JSON to CSV converter script.
    Returns True if successful, False otherwise.
    """
    try:
        cmd = [
            "python", "json_to_csv_converter.py",
            "--json", json_path,
            "--output-dir", output_dir,
            "--type", doc_type
        ]
        
        print(f"Running converter: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error running converter script: {e}")
        return False

def run_render_script(template: str, output_name: str, html: bool = True) -> bool:
    """
    Run the R render script to generate the CV/resume document.
    Returns True if successful, False otherwise.
    """
    try:
        cmd = [
            "Rscript", "render.r",
            "--template", template,
            "--output", output_name
        ]
        
        if html:
            cmd.append("--html")
        
        print(f"Running render script: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error running render script: {e}")
        return False

def main():
    """Main function to generate a tailored CV/resume."""
    parser = argparse.ArgumentParser(description='Generate a tailored CV/resume based on a job posting.')
    parser.add_argument('--job-posting', required=True, help='Path to the job posting text file')
    parser.add_argument('--cv-json', default='cv_data.json', help='Path to the CV/resume JSON file')
    parser.add_argument('--output-name', required=True, help='Output filename for the generated document (without extension)')
    parser.add_argument('--type', choices=['cv', 'resume'], default='resume', help='Type of document to generate')
    parser.add_argument('--improve-descriptions', action='store_true', help='Improve entry descriptions with AI suggestions')
    parser.add_argument('--html-only', action='store_true', help='Generate only HTML (no PDF)')
    
    args = parser.parse_args()
    
    # Prepare paths and directories
    output_dir = f"my_{args.type}_data"
    tailored_json_path = f"tailored_{args.output_name}.json"
    template_name = f"my_{args.type}.rmd"
    
    print("\n==== AI CV/Resume Generator ====")
    print(f"Job Posting: {args.job_posting}")
    print(f"Document Type: {args.type}")
    print(f"Output Name: {args.output_name}")
    
    # 1. Load the CV/resume data
    print("\nLoading CV/resume data...")
    cv_data = load_json_data(args.cv_json)
    print(f"Loaded {len(cv_data.get('entries', []))} entries from {args.cv_json}")
    
    # 2. Read the job posting
    print("\nReading job posting...")
    job_posting = read_job_posting(args.job_posting)
    print(f"Read {len(job_posting)} characters from {args.job_posting}")
    
    # 3. Set up OpenAI client
    print("\nSetting up OpenAI client...")
    openai_client = setup_openai_client()
    
    # 4. Analyze the job posting
    print("\nAnalyzing job posting with AI...")
    job_analysis = analyze_job_posting(openai_client, job_posting)
    print("Job analysis complete. Extracted key requirements:")
    for category, items in job_analysis.items():
        print(f"  - {category}: {', '.join(items[:3])}...")
    
    # 5. Create a tailored professional summary
    print("\nCreating job-specific professional summary...")
    new_summary = create_job_specific_summary(openai_client, cv_data, job_analysis)
    
    # Update the professional summary in the CV data
    for block in cv_data.get("text_blocks", []):
        if block.get("id") == "professional_summary":
            print(f"Original summary: {block.get('content', '')[:50]}...")
            block["content"] = new_summary
            print(f"Updated summary: {new_summary[:50]}...")
            break
    
    # 6. Create a tailored version of the CV/resume JSON
    create_tailored_json(
        cv_data,
        job_analysis,
        openai_client,
        tailored_json_path,
        improve_descriptions=args.improve_descriptions
    )
    
    # 7. Run the converter script
    print("\nConverting tailored JSON to CSV...")
    if not run_converter_script(tailored_json_path, output_dir, args.type):
        print("Error: Failed to convert JSON to CSV. Exiting.")
        sys.exit(1)
    
    # 8. Run the render script
    print("\nRendering final document...")
    if not run_render_script(template_name, args.output_name, not args.html_only):
        print("Error: Failed to render document. Exiting.")
        sys.exit(1)
    
    print(f"\nSuccess! Tailored {args.type.upper()} created: output/{args.output_name}.pdf")
    if not args.html_only:
        print(f"HTML version also available: output/{args.output_name}.html")
    
    print("\nAI-assisted improvements:")
    print("1. Created a job-specific professional summary")
    print("2. Selected the most relevant entries based on job requirements")
    if args.improve_descriptions:
        print("3. Improved entry descriptions to better match job requirements")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
