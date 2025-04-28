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

import re
import os
import sys
import json
import argparse
import logging
import traceback
import platform
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union, Literal
from datetime import datetime
from pathlib import Path

# Third-party imports

# Import rich for colorful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.logging import RichHandler
    # Create a console instance
    console = Console()
    # Rich is available
    RICH_AVAILABLE = True
except ImportError:
    # Fallback for when rich is not available
    RICH_AVAILABLE = False
    console = None
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

# Configure logging
def setup_logging(verbose=False):
    """Configure logging based on verbosity level"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create a timestamp for the log filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Set up two separate logs
    log_filename = f'logs/cv_generator_{timestamp}.log'
    api_log_filename = f'logs/api_interactions_{timestamp}.log'
    
    # Configure main logger
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Configure file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Set up API logger (always at DEBUG level for complete recording)
    api_logger = logging.getLogger('api')
    api_logger.setLevel(logging.DEBUG)
    api_logger.propagate = False  # Don't send messages to root logger
    
    # Detailed format for API logs
    api_format = '%(asctime)s - %(message)s'
    api_file_handler = logging.FileHandler(api_log_filename)
    api_file_handler.setFormatter(logging.Formatter(api_format))
    api_logger.addHandler(api_file_handler)
    
    # Also add console handler for API logs if verbose
    if verbose:
        api_console_handler = logging.StreamHandler()
        api_console_handler.setFormatter(logging.Formatter(api_format))
        api_console_handler.setLevel(logging.DEBUG)
        api_logger.addHandler(api_console_handler)
    
    print(f"Main log file: {log_filename}")
    print(f"API interactions log file: {api_log_filename}")
    
    return logger

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

def analyze_job_posting(ai_client: Any, job_posting: str, service: str = "openai", openai_model: str = "gpt-4o", claude_model: str = "claude-3-7-sonnet-20250219", temperature: float = 0.0, verbose: bool = False) -> Dict:
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
    
    # Log the prompt and model being used
    if verbose:
        logging.debug(f"\n===== ANALYZE JOB POSTING =====\nService: {service}\nModel: {openai_model if service == 'openai' else claude_model}")
        logging.debug(f"System prompt:\n{system_prompt}")
        logging.debug(f"User prompt:\nAnalyze this job posting and extract the key information:\n\n{job_posting[:500]}...")
    
    try:
        if service == "openai":
            user_prompt = f"Analyze this job posting and extract the key information:\n\n{job_posting}"
            logging.info(f"Sending job analysis request to OpenAI using {openai_model}")
            response = ai_client.chat.completions.create(
                model=openai_model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON from the response
            response_content = response.choices[0].message.content
            analysis = json.loads(response_content)
            
            # Log the complete API interaction
            log_api_interaction(
                service="openai", 
                model=openai_model, 
                prompt_type="Job Analysis", 
                system_prompt=system_prompt,
                user_prompt=user_prompt, 
                response_text=response_content
            )
            
            if verbose:
                logging.debug(f"OpenAI Response:\n{json.dumps(analysis, indent=2)}")
                
            return analysis
            
        elif service == "claude":
            # Add more explicit JSON formatting instructions to the prompt
            prompt = f"{system_prompt}\n\nAnalyze this job posting and extract the key information:\n\n{job_posting}\n\nYou MUST respond with valid JSON only. Your entire response must be valid JSON with no other text. Do not include markdown code blocks or any other formatting."
            
            logging.info(f"Sending job analysis request to Claude using {claude_model}")
            response = ai_client.messages.create(
                model=claude_model,
                max_tokens=4000,
                temperature=0.0,
                system="You are an expert career counselor and resume specialist. Your response must be only valid JSON with no text before or after. DO NOT include markdown code blocks, explanations, or any other non-JSON text in your response.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Get the raw response text
            raw_response = response.content[0].text
            
            if verbose:
                logging.debug(f"Claude Raw Response:\n{raw_response}")
            
            # Try to parse the JSON, with better error handling
            try:
                # Remove any potential markdown code block markers that Claude might add
                cleaned_response = raw_response
                if "```json" in cleaned_response:
                    # Extract content from code blocks if present
                    import re
                    json_blocks = re.findall(r'```(?:json)?\n(.+?)\n```', cleaned_response, re.DOTALL)
                    if json_blocks:
                        cleaned_response = json_blocks[0]
                
                # Try to parse as JSON
                analysis = json.loads(cleaned_response)
                
                if verbose:
                    logging.debug(f"Claude Parsed Response:\n{json.dumps(analysis, indent=2)}")
                    
                return analysis
            except json.JSONDecodeError as e:
                # If we get here, the response wasn't valid JSON
                print(f"Error parsing Claude response as JSON: {e}")
                print("Raw response first 100 chars: " + raw_response[:100] + "...")
                
                # Fallback: Try to extract structured data manually
                # This is a more aggressive approach to extract information
                print("Attempting to extract structured data from non-JSON response...")
                
                # Define a minimal structure for job analysis with default values
                manual_analysis = {
                    "Required skills and technologies": ["Python programming", "R programming", "Data analysis"],
                    "Desired experience areas": ["Data science", "Machine learning", "Statistical modeling"],
                    "Key responsibilities": ["Analyzing data", "Building models", "Reporting results"],
                    "Industry and domain-specific knowledge required": ["Domain expertise", "Industry knowledge"],
                    "Soft skills emphasized": ["Communication", "Collaboration", "Problem-solving"]
                }
                
                # Try to extract sections from the raw response text
                sections = {
                    "Required skills and technologies": ["Required skills", "technologies", "proficiency", "technical skills"],
                    "Desired experience areas": ["Desired experience", "preferred experience", "areas of expertise"],
                    "Key responsibilities": ["Key responsibilities", "responsibilities", "key duties", "You will"],
                    "Industry and domain-specific knowledge required": ["knowledge", "domain", "industry", "field"],
                    "Soft skills emphasized": ["Soft skills", "interpersonal", "communication", "teamwork"]
                }
                # Apply more aggressive parsing for each section type
                for section_key, section_terms in sections.items():
                    for term in section_terms:
                        # Try different approaches to find relevant content
                        # 1. Look for sections with the term in a header
                        section_pattern = rf"(?i){re.escape(term)}[^\n]*\n+((?:-[^\n]+\n)+)"
                        section_matches = re.findall(section_pattern, raw_response)
                        for match in section_matches:
                            bullet_items = re.findall(r"- ([^\n]+)", match)
                            if bullet_items:
                                manual_analysis[section_key].extend([item.strip() for item in bullet_items if item.strip()])
                                
                        # 2. Try to extract bullet lists even without clear headers
                        if term.lower() in raw_response.lower():
                            nearby_pattern = rf"(?i)(?:\n|.)*{re.escape(term)}[^\n]*(?:\n|.)*?(((?:-|\*|\d+\.)\s+[^\n]+\n)+)"
                            nearby_matches = re.findall(nearby_pattern, raw_response)
                            for match in nearby_matches:
                                items = re.findall(r"(?:-|\*|\d+\.)\s+([^\n]+)", match[0])
                                if items:
                                    manual_analysis[section_key].extend([item.strip() for item in items if item.strip()])
                
                # Extract from the job posting directly if we need more data
                if not any(len(items) > 0 for section_key, items in manual_analysis.items() if "required" in section_key.lower()) and len(job_posting) > 0:
                    # Look for requirements/skills sections
                    req_pattern = r"(?i)(?:requirements|qualifications|skills|experience)[:\s]*((?:(?:\n|.)*?(?:-|\*|\d+\.)\s+[^\n]+\n)+)"
                    req_matches = re.findall(req_pattern, job_posting)
                    for match in req_matches:
                        items = re.findall(r"(?:-|\*|\d+\.)\s+([^\n]+)", match)
                        if items:
                            key = "Required skills and technologies"
                            manual_analysis[key].extend([item.strip() for item in items if len(item.strip()) > 3][:5])
                            
                    # Look for responsibilities section
                    resp_pattern = r"(?i)(?:responsibilities|duties|role)[:\s]*((?:(?:\n|.)*?(?:-|\*|\d+\.)\s+[^\n]+\n)+)"
                    resp_matches = re.findall(resp_pattern, job_posting)
                    for match in resp_matches:
                        items = re.findall(r"(?:-|\*|\d+\.)\s+([^\n]+)", match)
                        if items:
                            key = "Key responsibilities"
                            manual_analysis[key].extend([item.strip() for item in items if len(item.strip()) > 3][:5])
                            
                # Make sure we have at least some content
                if not any(len(items) > 3 for items in manual_analysis.values()):
                    # Extract words that might be skills from the job posting
                    skill_keywords = ["python", "R", "analysis", "development", "programming", "research", 
                                      "communication", "teamwork", "leadership", "data", "science", "biology"]
                    found_skills = []
                    for skill in skill_keywords:
                        if skill.lower() in job_posting.lower():
                            found_skills.append(skill.capitalize())
                    if found_skills:
                        manual_analysis["Required skills and technologies"] = found_skills[:5]

                # Remove duplicates and limit size of each category
                for key in manual_analysis:
                    manual_analysis[key] = list(dict.fromkeys([item for item in manual_analysis[key] if item]))
                    manual_analysis[key] = manual_analysis[key][:5]  # Limit to 5 items per category
                    
                # Log the manually extracted analysis
                log_api_interaction(
                    service="claude", 
                    model=claude_model, 
                    prompt_type="Job Analysis (Manual Extraction)", 
                    system_prompt=system_prompt,
                    user_prompt=prompt, 
                    response_text=f"MANUAL EXTRACTION\n\nOriginal Response:\n{raw_response}\n\nExtracted Data:\n{json.dumps(manual_analysis, indent=2)}"
                )
                
                return manual_analysis
    
    except Exception as e:
        print(f"Error analyzing job posting: {e}")
        sys.exit(1)

def run_converter_script(json_path: str, output_dir: str, doc_type: str) -> bool:
    """
    Run the JSON to CSV converter script.
    
    Args:
        json_path: Path to the JSON file
        output_dir: Directory to output CSV files (will be created if it doesn't exist)
        doc_type: Type of document (cv or resume)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if converter script exists
        converter_script = "json_to_csv_converter.py"
        if not os.path.exists(converter_script):
            print(f"Error: Converter script '{converter_script}' not found in the current directory.")
            return False
            
        # Construct the command
        cmd = [
            sys.executable,
            converter_script,
            "--json", json_path,
            "--output-dir", output_dir,
            "--type", doc_type
        ]
        
        # Run the command
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if successful
        if result.returncode != 0:
            print(f"Error running converter script: {result.stderr}")
            return False
            
        print(f"Successfully converted JSON to CSV files in {output_dir}")
        return True
        
    except Exception as e:
        print(f"Error running converter script: {e}")
        return False

def run_render_script(template_path: str, output_name: str, html_too: bool = False, data_dir: str = None) -> bool:
    """
    Run the R render script to generate the final document.
    
    Args:
        template_path: Template file to use (e.g., my_cv.rmd)
        output_name: Base name for output files (without extension)
        html_too: Whether to generate HTML output as well
        data_dir: Directory containing the CSV data files (defaults to output_name_data)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if render script exists
        render_script = "render.r"
        if not os.path.exists(render_script):
            print(f"Error: Render script '{render_script}' not found in the current directory.")
            return False
            
        # Construct the command
        cmd = ["Rscript", render_script, "--template", template_path, "--output", output_name]
        
        # Add data directory if specified
        if data_dir:
            cmd.extend(["--data-dir", data_dir])
        
        # Add HTML flag if requested
        if html_too:
            cmd.append("--html")
            
        # Run the command
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check if successful
        if result.returncode != 0:
            print(f"Error running render script: {result.stderr}")
            return False
            
        print(f"Successfully rendered document as {output_name}")
        return True
        
    except Exception as e:
        print(f"Error running render script: {e}")
        return False

def create_job_specific_summary(ai_client: Any, cv_data: Dict, job_analysis: Dict, service: str = "openai", openai_model: str = "gpt-4o", claude_model: str = "claude-3-7-sonnet-20250219", temperature: float = 0.7, verbose: bool = False) -> str:
    """Create a tailored professional summary for the CV/resume based on job posting analysis."""
    # Extract existing text blocks
    text_blocks = cv_data.get("text_blocks", [])
    original_summary = ""
    
    # First try to find a professional_summary block
    for block in text_blocks:
        if block.get("id") == "professional_summary":
            original_summary = block.get("content", "")
            break
    
    # If no professional_summary found, try to use intro block as fallback
    if not original_summary:
        for block in text_blocks:
            if block.get("id") == "intro":
                original_summary = block.get("content", "")
                print("Using intro block as professional summary")
                break
                
    # Log the original summary to help with debugging
    print(f"Original summary: {original_summary[:100]}..." if len(original_summary) > 100 else original_summary)
    
    # Debug job analysis data
    print("\nJob Analysis Keys:", list(job_analysis.keys()))
    for key in job_analysis.keys():
        print(f"  - {key}: {len(job_analysis[key])} items")
    
    # Prepare prompt with guaranteed fallback values for missing keys
    system_prompt = """You are an expert resume writer who crafts compelling professional summaries. 
    Create a concise, tailored professional summary (150-200 words) that highlights the candidate's most relevant 
    skills and experience for the specific job. The summary should be written in first person and should 
    specifically address the job requirements."""
    
    # Define mappings between different potential key formats
    key_mappings = {
        "required_skills": ["Required skills and technologies", "required_skills_and_technologies", "Required skills", "Skills", "Technical skills", "Technologies", "skills", "technologies", "tech_skills", "technical_skills"],
        "desired_experience": ["Desired experience areas", "desired_experience_areas", "Experience", "Desired experience", "Preferred experience", "experience", "areas_of_experience"],
        "key_responsibilities": ["Key responsibilities", "key_responsibilities", "Responsibilities", "Duties", "Job duties", "responsibilities", "job_duties", "duties"],
        "industry_knowledge": ["Industry and domain-specific knowledge required", "industry_and_domain_specific_knowledge", "Domain knowledge", "Industry knowledge", "Knowledge", "domain_knowledge", "industry_knowledge", "specific_knowledge", "industry_and_domain_specific_knowledge_required"],
        "soft_skills": ["Soft skills emphasized", "soft_skills_emphasized", "Soft skills", "Interpersonal skills", "Communication skills", "soft_skills", "interpersonal_skills", "communication_skills"]
    }
    
    # Print the entire job_analysis for debugging
    print("\nComplete job analysis content:")
    for key, value in job_analysis.items():
        print(f"  {key}: {value}")
    
    # Helper function to find values using various key formats
    def get_values_by_key_patterns(data, key_patterns):
        for pattern in key_patterns:
            if pattern in data and data[pattern]:
                print(f"Found matching key: '{pattern}' with {len(data[pattern])} items")
                return data[pattern]
        return []
    
    # Extract values using the key mappings
    required_skills = get_values_by_key_patterns(job_analysis, key_mappings["required_skills"])
    desired_experience = get_values_by_key_patterns(job_analysis, key_mappings["desired_experience"])
    key_responsibilities = get_values_by_key_patterns(job_analysis, key_mappings["key_responsibilities"])
    industry_knowledge = get_values_by_key_patterns(job_analysis, key_mappings["industry_knowledge"])
    soft_skills = get_values_by_key_patterns(job_analysis, key_mappings["soft_skills"])
    
    # Special check for snake_case key patterns that Claude often returns
    if not any([required_skills, desired_experience, key_responsibilities, industry_knowledge, soft_skills]):
        print("No matching keys found, checking for snake_case variants directly")
        if "required_skills_and_technologies" in job_analysis:
            required_skills = job_analysis["required_skills_and_technologies"]
            print(f"Using direct key 'required_skills_and_technologies' with {len(required_skills)} items")
        if "desired_experience_areas" in job_analysis:
            desired_experience = job_analysis["desired_experience_areas"]
            print(f"Using direct key 'desired_experience_areas' with {len(desired_experience)} items")
        if "key_responsibilities" in job_analysis:
            key_responsibilities = job_analysis["key_responsibilities"]
            print(f"Using direct key 'key_responsibilities' with {len(key_responsibilities)} items")
        if "industry_and_domain_specific_knowledge" in job_analysis:
            industry_knowledge = job_analysis["industry_and_domain_specific_knowledge"]
            print(f"Using direct key 'industry_and_domain_specific_knowledge' with {len(industry_knowledge)} items")
        if "soft_skills_emphasized" in job_analysis:
            soft_skills = job_analysis["soft_skills_emphasized"]
            print(f"Using direct key 'soft_skills_emphasized' with {len(soft_skills)} items")

    # Use fallback values if still empty
    if not required_skills:
        required_skills = ["Python programming", "R programming", "Data analysis"]
        print("Using fallback values for required_skills")
    if not desired_experience:
        desired_experience = ["Data science", "Bioinformatics", "Statistical analysis"]
        print("Using fallback values for desired_experience")
    if not key_responsibilities:
        key_responsibilities = ["Data analysis", "Building models", "Reporting results"]
        print("Using fallback values for key_responsibilities")
    if not industry_knowledge:
        industry_knowledge = ["Genomics", "Bioinformatics", "Research methods"]
        print("Using fallback values for industry_knowledge")
    if not soft_skills:
        soft_skills = ["Communication", "Collaboration", "Problem-solving"]
        print("Using fallback values for soft_skills")
        
    # Format data for the prompt
    skills_text = ', '.join(required_skills[:5])
    experience_text = ', '.join(desired_experience[:5])
    responsibilities_text = ', '.join(key_responsibilities[:5])
    knowledge_text = ', '.join(industry_knowledge[:5])
    soft_skills_text = ', '.join(soft_skills[:5])
    
    print(f"\nSending to AI:\n- Skills: {skills_text}\n- Experience: {experience_text}")

    user_prompt = f"""Original professional summary: {original_summary}
    
    Job requirements:
    - Required skills: {skills_text}
    - Desired experience: {experience_text}
    - Key responsibilities: {responsibilities_text}
    - Industry knowledge: {knowledge_text}
    - Soft skills: {soft_skills_text}
    
    Create a tailored professional summary that emphasizes the most relevant aspects of my background 
    for this specific job opportunity. Keep it concise (150-200 words) and impactful.
    
    IMPORTANT: Do not include a title or heading in your response. Just provide the summary text itself.
    DO NOT start with "# Professional Summary" or any other heading."""
    
    
    if verbose:
        logging.debug(f"\n===== CREATE JOB-SPECIFIC SUMMARY =====\nService: {service}\nModel: {openai_model if service == 'openai' else claude_model}")
        logging.debug(f"System prompt:\n{system_prompt}")
        logging.debug(f"User prompt:\n{user_prompt}")
    
    try:
        if service == "openai":
            logging.info(f"Creating job-specific summary with OpenAI using {openai_model}")
            response = ai_client.chat.completions.create(
                model=openai_model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            summary = response.choices[0].message.content.strip()
            
            # Log the complete API interaction
            log_api_interaction(
                service="openai", 
                model=openai_model, 
                prompt_type="Job-Specific Summary", 
                system_prompt=system_prompt,
                user_prompt=user_prompt, 
                response_text=summary
            )
            
            if verbose:
                logging.debug(f"OpenAI response:\n{summary}")
            
            # Remove any markdown heading if present
            if summary.startswith("# ") and "\n" in summary:
                summary = summary.split("\n", 1)[1].strip()
            
            # Print a sample of the summary
            print(f"Generated job-specific summary: {summary[:100]}...")
            logging.info(f"Generated job-specific summary: {summary[:500]}...")
            
            return summary
            
        elif service == "claude":
            logging.info(f"Creating job-specific summary with Claude using {claude_model}")
            response = ai_client.messages.create(
                model=claude_model,
                max_tokens=1000,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            summary = response.content[0].text.strip()
            
            # Log the complete API interaction
            log_api_interaction(
                service="claude", 
                model=claude_model, 
                prompt_type="Job-Specific Summary", 
                system_prompt=system_prompt,
                user_prompt=user_prompt, 
                response_text=summary
            )
            
            # Check if the response is wrapped in code blocks and unwrap if needed
            if summary.startswith("```") and summary.endswith("```"):
                # Extract content from code blocks
                summary = "\n".join(summary.split("\n")[1:-1])
            
            if verbose:
                logging.debug(f"Claude response:\n{summary}")
                
            return summary
            
        else:
            print(f"Unsupported service: {service}")
            return original_summary
            
    except Exception as e:
        print(f"Error creating job-specific summary: {e}")
        return original_summary


def score_entry_relevance(ai_client: Any, entry: Dict, job_analysis: Dict, service: str = "openai", openai_model: str = "gpt-4o", claude_model: str = "claude-3-7-sonnet-20250219", temperature: float = 0.0, verbose: bool = False) -> Tuple[float, str, List[str]]:
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
    
    # Log the entry being scored
    if verbose:
        logging.debug(f"\n===== SCORING ENTRY =====\nTitle: {entry.get('title', '')}\nSection: {entry.get('section', '')}")
        logging.debug(f"Service: {service}\nModel: {openai_model if service == 'openai' else claude_model}")
        logging.debug(f"System prompt:\n{system_prompt}")
        logging.debug(f"Entry text:\n{entry_text}")
        logging.debug(f"Job text:\n{job_text}")
    
    try:
        if service == "openai":
            user_prompt = f"Resume Entry:\n{entry_text}\n\nJob Details:\n{job_text}"
            logging.info(f"Scoring entry '{entry.get('title', '')}' with OpenAI using {openai_model}")
            response = ai_client.chat.completions.create(
                model=openai_model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON from the response
            response_content = response.choices[0].message.content
            response_data = json.loads(response_content)
            
            # Log the complete API interaction
            log_api_interaction(
                service="openai", 
                model=openai_model, 
                prompt_type="Entry Scoring", 
                system_prompt=system_prompt,
                user_prompt=user_prompt, 
                response_text=response_content
            )
            
            if verbose:
                logging.debug(f"OpenAI Response:\n{json.dumps(response_data, indent=2)}")
            
            # Return the extracted data
            return float(response_data.get("score", 0)), response_data.get("reasoning", ""), response_data.get("improved_descriptions", [])
            
        elif service == "claude":
            prompt = f"Resume Entry:\n{entry_text}\n\nJob Details:\n{job_text}"
            
            logging.info(f"Scoring entry '{entry.get('title', '')}' with Claude using {claude_model}")
            # Use the main Claude model for consistency, with explicit JSON instructions
            response = ai_client.messages.create(
                model=claude_model,
                max_tokens=1000,
                temperature=0.0,
                system=system_prompt + "\nYour entire response must be valid JSON only. Do not include markdown code blocks or explanations. Respond with just the raw JSON object.",
                messages=[
                    {"role": "user", "content": prompt + "\n\nYou MUST respond with valid JSON only. Your entire response must be valid JSON with no other text."}
                ]
            )
            
            # Get the raw response text
            raw_response = response.content[0].text
            
            if verbose:
                logging.debug(f"Claude Raw Response:\n{raw_response}")
            
            # Try to parse the JSON, with better error handling
            try:
                # Remove any potential markdown code block markers that Claude might add
                cleaned_response = raw_response
                if "```json" in cleaned_response:
                    # Extract content from code blocks if present
                    import re
                    json_blocks = re.findall(r'```(?:json)?\n(.+?)\n```', cleaned_response, re.DOTALL)
                    if json_blocks:
                        cleaned_response = json_blocks[0]
                
                # Try to parse as JSON
                response_data = json.loads(cleaned_response)
                
                if verbose:
                    logging.debug(f"Claude Parsed Response:\n{json.dumps(response_data, indent=2)}")
                
                # Return the extracted data
                return float(response_data.get("score", 0)), response_data.get("reasoning", ""), response_data.get("improved_descriptions", [])
            except json.JSONDecodeError as e:
                # If we get here, the response wasn't valid JSON
                print(f"Error parsing Claude response as JSON: {e}")
                print("Raw response first 100 chars: " + raw_response[:100] + "...")
                
                # Return fallback values
                score = 5.0  # Neutral score
                reasoning = "Unable to parse Claude response as JSON. Using default score."
                return score, reasoning, []
    
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
    service: str = "openai",
    openai_model: str = "gpt-4o",
    claude_model: str = "claude-3-7-sonnet-20250219",
    temperature: float = 0.0,
    verbose: bool = False
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
    tailored_data["meta"] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "generated_by": "ai_cv_generator.py",
        "generated_for": "Job Application",
        "original_file": args.cv_data if 'args' in locals() else "cv_data.json"
    }
    
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
        score, reasoning, improved_descriptions = score_entry_relevance(ai_client, entry, job_analysis, service, openai_model, claude_model, verbose)
        
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
    service: str = "openai",
    openai_model: str = "gpt-4o",
    claude_model: str = "claude-3-7-sonnet-20250219",
    temperature: float = 0.7,
    verbose: bool = False
):
    """
    Create a tailored version of the CV directly using a structured prompt.
    This uses a single comprehensive API call instead of evaluating entries individually.
    
    Note: cv_data should already contain the updated professional summary if it was generated separately.
    
    Args:
        ai_client: AI client (OpenAI or Claude)
        cv_data: The original CV/resume JSON data
        job_posting: The text of the job posting
        output_path: Path to save the tailored JSON
        service: Which AI service is being used
        openai_model: The OpenAI model to use
        claude_model: The Claude model to use
        verbose: Whether to enable verbose logging
    """
    # Convert CV data to a string representation
    cv_json_str = json.dumps(cv_data, indent=2)
    
    # Update meta information in the CV data for correct attribution
    if 'meta' not in cv_data:
        cv_data['meta'] = {}
    
    cv_data['meta'] = {
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "generated_by": "ai_cv_generator.py",
        "tailoring_method": "prompt-only"
    }
    
    # Create a system prompt instructing the AI how to tailor the CV with comprehensive editing guidance
    system_prompt = """You are an expert CV/resume tailoring assistant. Your task is to create a tailored version of the CV/resume for a specific job posting.
    
    Follow these steps:
    1. Analyze the job posting to identify key requirements, skills, and qualifications
    2. Review the CV/resume to find relevant experience and accomplishments
    3. Create a comprehensive tailored version that emphasizes fit for the specific position
    
    Your output must be a valid JSON object following the same structure as the input CV data, but with:
    
    1. COMPREHENSIVE TAILORING across ALL sections, including:
       - A completely rewritten professional summary/intro that highlights qualifications
       - Every selected entry's title, descriptions, and content rewritten to emphasize relevance
       - Skills section reorganized to prioritize the most relevant skills
       - Any text_blocks updated to reflect job-specific messaging
    
    2. STRATEGIC ENTRY SELECTION:
       - Include only the most relevant entries (generally 2-3 per section)
       - Ensure all critical qualifications from the job posting are addressed
       - For each entry, add notes explaining relevance when appropriate
    
    3. DESCRIPTION ENHANCEMENT:
       - Rewrite ALL descriptions using active language and quantifiable achievements
       - Incorporate keywords from the job posting naturally into descriptions
       - Highlight transferable skills when direct experience is limited
       - Add specific technical details when they match job requirements
    
    4. FORMATTING CONSIDERATION: 
       - Maintain proper JSON structure with all field names preserved
       - Ensure there's no unnecessary repetition across sections
       - Keep descriptions concise but impactful
    
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
    
    # Log the prompts being used
    if verbose:
        logging.debug(f"\n===== CREATE TAILORED CV WITH PROMPT =====")
        logging.debug(f"Service: {service}\nModel: {openai_model if service == 'openai' else claude_model}")
        logging.debug(f"System prompt:\n{system_prompt}")
        logging.debug(f"User prompt (first 500 chars):\n{user_prompt[:500]}...")
    
    try:
        # Compress CV data by limiting entry descriptions to conserve tokens
        def compress_cv_data(cv_data):
            """Reduce size of CV by limiting entry descriptions to save tokens"""
            compressed = cv_data.copy()
            
            # If entries exist, truncate long descriptions
            if "entries" in compressed:
                for entry in compressed["entries"]:
                    # Truncate descriptions longer than 300 characters
                    if "description" in entry and isinstance(entry["description"], str):
                        if len(entry["description"]) > 300:
                            entry["description"] = entry["description"][:300] + "..."
                            
            return compressed
        
        # Reduce size of CV by limiting descriptions
        compressed_cv = compress_cv_data(cv_data)
        cv_json_str = json.dumps(compressed_cv)
        
        if service == "openai":
            logging.info(f"Creating tailored CV with OpenAI using {openai_model}")
            response = ai_client.chat.completions.create(
                model=openai_model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            tailored_cv_json = response.choices[0].message.content
            
            # Log the complete API interaction
            log_api_interaction(
                service="openai", 
                model=openai_model, 
                prompt_type="CV Tailoring (Prompt-Only)", 
                system_prompt=system_prompt,
                user_prompt=user_prompt, 
                response_text=tailored_cv_json
            )
            
            if verbose:
                logging.debug(f"OpenAI response (first 500 chars):\n{tailored_cv_json[:500]}...")
            
        elif service == "claude":
            logging.info(f"Creating tailored CV with Claude using {claude_model}")
            response = ai_client.messages.create(
                model=claude_model,
                max_tokens=4000,
                temperature=temperature,
                system=system_prompt + "\nYour entire response must be valid JSON only. Do not include markdown code blocks or explanations. Respond with just the raw JSON object.",
                messages=[
                    {"role": "user", "content": user_prompt + "\n\nYou MUST respond with valid JSON only. Your entire response must be valid JSON with no other text."}
                ]
            )
            # Get the raw response text
            raw_response = response.content[0].text
            
            # Log the complete API interaction
            log_api_interaction(
                service="claude", 
                model=claude_model, 
                prompt_type="CV Tailoring (Prompt-Only)", 
                system_prompt=system_prompt + "\nYour entire response must be valid JSON only. Do not include markdown code blocks or explanations. Respond with just the raw JSON object.",
                user_prompt=user_prompt + "\n\nYou MUST respond with valid JSON only. Your entire response must be valid JSON with no other text.", 
                response_text=raw_response
            )
            
            if verbose:
                logging.debug(f"Claude Raw Response (first 500 chars):\n{raw_response[:500]}...")
            
            # Add more comprehensive JSON extraction and validation
            import re
            cleaned_response = raw_response
            
            # First check for code blocks and extract content if present
            if "```json" in cleaned_response or "```" in cleaned_response:
                # Extract content from code blocks 
                json_blocks = re.findall(r'```(?:json)?\n(.+?)\n```', cleaned_response, re.DOTALL)
                if json_blocks:
                    cleaned_response = json_blocks[0]
                    logging.debug(f"Extracted JSON from code block, length: {len(cleaned_response)}")
            
            # Look for JSON object patterns as a fallback
            if not cleaned_response.strip().startswith('{'):
                potential_json = re.search(r'(\{.+\})', cleaned_response, re.DOTALL)
                if potential_json:
                    cleaned_response = potential_json.group(1)
                    logging.debug(f"Extracted JSON object using regex, length: {len(cleaned_response)}")
            
            # Clean up common issues that break JSON parsing
            def fix_json_string(json_str):
                # Handle trailing commas in arrays/objects which are invalid in JSON
                json_str = re.sub(r',\s*([\}\]])', r'\1', json_str)
                
                # Fix mismatched quotes, ensuring strings are properly quoted
                # This is a simple fix and won't catch all issues
                json_str = re.sub(r'([\{,:]\s*)(\w+):\s*', r'\1"\2":', json_str)
                
                # Replace single quotes with double quotes for JSON compliance
                # This is tricky and can break content with apostrophes, so we're careful
                in_string = False
                in_single_quote = False
                fixed_str = []
                i = 0
                
                while i < len(json_str):
                    char = json_str[i]
                    
                    # Handle escaped characters
                    if char == '\\' and i + 1 < len(json_str):
                        fixed_str.append(char)
                        fixed_str.append(json_str[i+1])
                        i += 2
                        continue
                        
                    # Track string state with double quotes
                    if char == '"' and not in_single_quote:
                        in_string = not in_string
                    
                    # Replace single quotes only when not inside a double-quoted string
                    if char == "'" and not in_string:
                        fixed_str.append('"')
                    else:
                        fixed_str.append(char)
                    
                    i += 1
                
                return ''.join(fixed_str)
            
            # Apply JSON fixes
            tailored_cv_json = fix_json_string(cleaned_response)
            logging.debug(f"Attempting to parse JSON of length {len(tailored_cv_json)}")
            
            # For debugging - log a snippet of the JSON
            json_preview = tailored_cv_json[:500] + '...' if len(tailored_cv_json) > 500 else tailored_cv_json
            logging.debug(f"JSON preview: {json_preview}")
        
        # Parse with better error reporting
        try:
            tailored_cv = json.loads(tailored_cv_json)
        except json.JSONDecodeError as e:
            # Show detailed debugging info
            error_context = tailored_cv_json[max(0, e.pos-50):min(len(tailored_cv_json), e.pos+50)]
            logging.error(f"JSON Error at position {e.pos}: {e.msg}")
            logging.error(f"Error context: ...{error_context}...")
            
            # Try fixing with a more permissive parser if available
            try:
                import ast
                logging.info("Attempting to repair JSON with ast.literal_eval")
                # Use ast to evaluate as Python literal - works for some malformed JSON
                tailored_cv = ast.literal_eval(tailored_cv_json)
                logging.info("Successfully repaired JSON!")
            except:
                # Last resort: try a very permissive JSON parser
                try:
                    import demjson3
                    logging.info("Attempting to repair JSON with demjson3")
                    tailored_cv = demjson3.decode(tailored_cv_json)
                    logging.info("Successfully repaired JSON with demjson3!")
                except ImportError:
                    logging.info("demjson3 not available for JSON repair")
                    raise e  # Re-raise the original error
                except Exception as demjson_error:
                    logging.error(f"Failed to repair JSON: {demjson_error}")
                    raise e  # Re-raise the original error
        
        # Save the tailored CV
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tailored_cv, f, indent=2)
            
        print(f"\nCreated tailored CV JSON: {output_path}")
        print("Used comprehensive prompt approach - no individual entry scoring performed")
        
    except Exception as e:
        print(f"Error creating tailored CV with comprehensive prompt approach: {e}")
        traceback.print_exc()
        print("Error in prompt-only approach. Consider trying again without --use-prompt-only flag.")
        print("To maintain separation between approaches, NOT falling back to entry-by-entry processing.")
        # Create a minimal valid JSON file so the process can continue
        minimal_cv = {
            "meta": cv_data.get("meta", {}),
            "contact_info": cv_data.get("contact_info", {}),
            "text_blocks": cv_data.get("text_blocks", []),
            "entries": cv_data.get("entries", [])[:3],  # Include a few entries to avoid empty output
            "skills": cv_data.get("skills", [])
        }
        # Add note about the error
        minimal_cv["meta"]["note"] = f"Error in prompt-only CV generation: {str(e)}"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(minimal_cv, f, indent=2)

def log_api_interaction(service, model, prompt_type, system_prompt, user_prompt, response_text):
    """Log the complete API interaction to the API log file"""
    api_logger = logging.getLogger('api')
    
    separator = "="*80
    api_logger.debug(f"\n{separator}\nAPI INTERACTION: {prompt_type}\n{separator}")
    api_logger.debug(f"Service: {service}")
    api_logger.debug(f"Model: {model}")
    api_logger.debug(f"\n--- SYSTEM PROMPT ---\n{system_prompt}")
    api_logger.debug(f"\n--- USER PROMPT ---\n{user_prompt}")
    api_logger.debug(f"\n--- RESPONSE ---\n{response_text}")
    api_logger.debug(f"\n{separator}\nEND OF INTERACTION\n{separator}\n")

def create_directories():
    """Create necessary directories for output files
    
    Uses relative paths to avoid permission issues with absolute paths
    """
    # Always use relative paths to avoid permission issues
    os.makedirs("./output", exist_ok=True)
    os.makedirs("./tailored_json", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    
    return {
        "output": "./output",
        "tailored_json": "./tailored_json",
        "logs": "./logs"
    }

def main():
    """Main function to generate a tailored CV/resume."""
    parser = argparse.ArgumentParser(description="Generate a tailored CV/resume based on a job posting")
    parser.add_argument("--job-posting", required=True, help="Path to the job posting text file")
    parser.add_argument("--cv-data", default="cv_database.json", help="Path to the CV/resume JSON data file")
    parser.add_argument("--output-name", help="Base name for output files (without extension)")
    parser.add_argument("--type", choices=["cv", "resume"], default="resume", help="Document type to generate")
    parser.add_argument("--improve-descriptions", action="store_true", help="Use AI to improve entry descriptions")
    parser.add_argument("--json-only", action="store_true", help="Only generate the JSON file, not the document")
    parser.add_argument("--html-too", action="store_true", help="Generate HTML version in addition to PDF")
    parser.add_argument("--use-prompt-only", action="store_true", help="Use direct prompt for CV tailoring instead of entry-by-entry analysis")
    parser.add_argument("--ai-service", choices=["openai", "claude"], default="openai", help="AI service to use (openai or claude)")
    parser.add_argument("--openai-model", default="gpt-4o", help="OpenAI model to use (default: gpt-4o)")
    parser.add_argument("--claude-model", default="claude-3-7-sonnet-20250219", help="Claude model to use (default: claude-3-7-sonnet-20250219)")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature setting for AI models (0.0-1.0). Lower values are more deterministic, higher values more creative (default: 0.7)")
    parser.add_argument("--entries-per-section", help="JSON string mapping sections to max entries (e.g., '{\"education\": 2}')")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging of prompts and API interactions")
    
    args = parser.parse_args()
    
    # Setup logging
    if RICH_AVAILABLE:
        # If rich is available, set up pretty logging
        log_level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(message)s",
            handlers=[RichHandler(rich_tracebacks=True)]
        )
    else:
        # Standard logging if rich is not available
        if not args.verbose:
            logging.getLogger().setLevel(logging.INFO)
        else:
            logging.getLogger().setLevel(logging.DEBUG)
    
    # Display colorful header if rich is available
    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold cyan]AI CV Generator[/bold cyan]\n[green]Create tailored resumes with AI[/green]", 
            border_style="blue"
        ))
    
    # Create necessary directories
    if RICH_AVAILABLE:
        console.print("[bold]Setting up directories...[/bold]")
    else:
        print("Setting up directories...")
    directories = create_directories()
    
    # Include date in YYYY-MM-DD format (for filenames only, not directories)
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    # Base name should NOT include the date for directory names
    if args.output_name is None:
        # For auto-generated names without date
        timestamp = datetime.now().strftime("%H%M%S")
        base_name = f"{args.type}_{timestamp}"
    else:
        # Use the user-provided name as is for the base name
        base_name = args.output_name
    
    # Create data directory name without date
    csv_output_dir = f"{base_name}_data"
    
    # Full output name WITH date (for JSON, HTML, PDF files)
    if today_date not in base_name:
        args.output_name = f"{base_name}_{today_date}"
    else:
        args.output_name = base_name
    
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
    
    # Store model information for later use
    openai_model = args.openai_model
    claude_model = args.claude_model
    
    # Analyze the job posting
    job_analysis = analyze_job_posting(ai_client, job_posting, service, openai_model=openai_model, claude_model=claude_model, temperature=args.temperature, verbose=args.verbose)
    print("Job analysis complete. Extracted key requirements:")
    for category, items in job_analysis.items():
        print(f"  - {category}: {', '.join(items[:3])}...")
    
    # Create a tailored professional summary
    print("\nCreating job-specific professional summary...")
    updated_summary = create_job_specific_summary(ai_client, cv_data, job_analysis, service, openai_model=openai_model, claude_model=claude_model, temperature=args.temperature, verbose=args.verbose)
    
    # Update the professional summary in the CV data
    summary_updated = False
    for block in cv_data.get("text_blocks", []):
        if block.get("id") == "professional_summary":
            print(f"Original summary: {block.get('content', '')[:50]}...")
            block["content"] = updated_summary
            print(f"Updated summary: {updated_summary[:50]}...")
            summary_updated = True
            break
            
    # If no professional_summary found, try to update intro block
    if not summary_updated and cv_data.get("text_blocks"):
        for block in cv_data.get("text_blocks", []):
            if block.get("id") == "intro":
                print(f"No professional_summary found, updating intro: {block.get('content', '')[:50]}...")
                block["content"] = updated_summary
                print(f"Updated intro: {updated_summary[:50]}...")
                break
    
    # Define the JSON output file path in the tailored_json directory
    tailored_json_path = f"{directories['tailored_json']}/{args.output_name}.json"
    
    # Create a tailored JSON file with only the most relevant entries
    tailoring_method = "prompt-only" if args.use_prompt_only else "entry-by-entry"
    if RICH_AVAILABLE:
        console.print(f"\n[bold blue]Using {tailoring_method} approach for CV tailoring...[/bold blue]")
    else:
        print(f"\nUsing {tailoring_method} approach for CV tailoring...")
    
    if args.use_prompt_only:
        # Use the direct prompt approach for tailoring (comprehensive single API call)
        if RICH_AVAILABLE:
            console.print("[yellow]Sending entire CV and job posting to AI in a single request...[/yellow]")
        else:
            print("Sending entire CV and job posting to AI in a single request...")
        create_tailored_cv_with_prompt(
            ai_client,
            cv_data,
            job_posting,
            tailored_json_path,
            service=service,
            openai_model=openai_model,
            claude_model=claude_model,
            temperature=args.temperature,
            verbose=args.verbose
        )
        # Skip all other processing steps that would trigger entry-by-entry evaluation
        if RICH_AVAILABLE:
            console.print("\n[italic yellow]Skipping individual entry evaluation as --use-prompt-only was specified[/italic yellow]")
        else:
            print("\nSkipping individual entry evaluation as --use-prompt-only was specified")
    else:
        # Use the detailed entry-by-entry analysis
        if RICH_AVAILABLE:
            console.print("[bold yellow]Evaluating each CV entry individually...[/bold yellow]")
        else:
            print("Evaluating each CV entry individually...")
        create_tailored_json(
            cv_data, 
            job_analysis, 
            ai_client,
            tailored_json_path,
            max_entries_per_section=json.loads(args.entries_per_section) if args.entries_per_section else None,
            improve_descriptions=args.improve_descriptions,
            service=service,
            openai_model=openai_model,
            claude_model=claude_model,
            temperature=args.temperature,
            verbose=args.verbose
        )
    
    # Run the converter script to create CSV files in a dedicated directory
    print("\nConverting tailored JSON to CSV...")
    if not run_converter_script(tailored_json_path, csv_output_dir, args.type):
        print("Error: Failed to convert JSON to CSV. Exiting.")
        sys.exit(1)
    
    # Set template name based on type
    template_name = f"my_{args.type}.rmd"
    
    # 8. Run the render script
    print("\nRendering final document...")
    # Always use relative paths to avoid permission issues
    if not run_render_script(template_name, args.output_name, args.html_too, data_dir=csv_output_dir):
        print("Error: Failed to render document. Exiting.")
        sys.exit(1)
    
    print(f"\nSuccess! Files created:")
    print(f"- JSON: {tailored_json_path}")
    print(f"- CSV files: {csv_output_dir}/*.csv")
    print(f"- PDF: ./output/{args.output_name}.pdf")
    if args.html_too:
        print(f"- HTML: ./output/{args.output_name}.html")
    
    print("\nAI-assisted improvements:")
    print("1. Created a job-specific professional summary")
    print("2. Selected the most relevant entries based on job requirements")
    if args.improve_descriptions:
        print("3. Improved entry descriptions to better match job requirements")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
