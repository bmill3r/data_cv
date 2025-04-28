# data_cv
Generate custom CV using R and CSS based on `datadrivencv`

## Quick Start Guide

This system provides a flexible, data-driven approach to creating tailored CVs and resumes. Here's how it works:

1. **Central Database**: Everything starts with `cv_database.json`, your master database containing all CV/resume entries with tags.

2. **Filtering Process**: You can subset entries from this database in two ways:
   - **Manual**: Use `json_to_csv_converter.py` with tag/company filters to select entries
   - **AI-Powered**: Let `ai_cv_generator.py` analyze a job posting and select the best entries for you

3. **CSV Generation**: Selected entries are converted into CSV files in a subdirectory (e.g., `my_resume_data/`)

4. **Document Rendering**: The `render.r` script combines these CSV files with a template RMD file to create beautiful HTML and PDF outputs

5. **Customization**: Create different CSV subdirectories and customized RMD templates for various job applications

With this workflow, you can maintain a single source of truth (your database) while generating tailored documents for different purposes. The system can be fully automated (AI selects entries and renders documents in one step) or manually controlled for precise customization.

### Updating Your Database

To efficiently maintain your CV database without manually editing JSON files:

```bash
# Add a new entry interactively
python cv_database_editor.py add-entry --database cv_database.json

# List all entries with their IDs
python cv_database_editor.py list-entries --database cv_database.json

# Edit an existing entry by ID
python cv_database_editor.py edit-entry --database cv_database.json --entry-id 5

# Add a new skill category
python cv_database_editor.py add-skill-category --database cv_database.json

# List all skill categories
python cv_database_editor.py list-skill-categories --database cv_database.json

# Edit a skill category
python cv_database_editor.py edit-skill-category --database cv_database.json --category-id 0

# List all text blocks (summaries, introductions, etc.)
python cv_database_editor.py list-text-blocks --database cv_database.json

# Edit an existing text block
python cv_database_editor.py edit-text-block --database cv_database.json --block-id 0

# Update contact information
python cv_database_editor.py edit-contact --database cv_database.json
```

**Note**: For editing text blocks, you need to use the numeric ID shown by the list-text-blocks command, not the text block name.

The database editor provides interactive prompts for all fields, making it easy to maintain your CV data without dealing with JSON syntax directly.

## Table of Contents

- [Overview](#overview)
- [AI-Powered CV Generation Workflow](#ai-powered-cv-generation-workflow)
  - [Step-by-Step Workflow for Beginners](#step-by-step-workflow-for-beginners)
- [Tool Documentation](#tool-documentation)
  - [AI CV Generator](#ai-cv-generator-ai_cv_generatorpy)
    - [Arguments](#arguments)
    - [Usage Examples](#usage-examples)
  - [JSON to CSV Converter](#json-to-csv-converter-json_to_csv_converterpy)
    - [Arguments](#arguments-1)
    - [Usage Examples](#usage-examples-1)
  - [CSV to JSON Converter](#csv-to-json-converter-csv_to_json_converterpy)
    - [Arguments](#arguments-2)
    - [Usage Examples](#usage-examples-2)
  - [CV Database Editor](#cv-database-editor-cv_database_editorpy)
    - [Commands](#commands)
  - [Render Script](#render-script-renderr)
- [Tagging System and Data Flow](#tagging-system-and-data-flow)
- [CV Data Structure](#cv-data-structure)
- [Citation Metrics](#citation-metrics)
- [Page Customization](#page-customization)
- [JSON Format Examples](#json-format-examples)
- [Entry Selection and AI Processing](#entry-selection-and-ai-processing)
  - [Entry Selection Guide](./entry_selection_guide.md)
- [AI CV Generator Details](#ai-cv-generator-details)

## Overview

This repository allows you to create beautifully formatted, data-driven CVs and resumes using R, CSS, and a collection of CSV files. The system is built on top of the `datadrivencv` framework with custom modifications.

## CV Generation Workflows

This system supports two primary workflows for generating tailored CVs and resumes:

1. **AI-Powered Workflow** - Uses AI to automatically analyze job postings and select the most relevant entries
2. **Manual Filtering Workflow** - Manually filter your CV database using tags and company filtering

### AI-Powered CV Generation Workflow

The repository includes an AI-powered workflow for automatically tailoring your CV/resume to specific job postings using OpenAI GPT-4 or Anthropic Claude APIs. **This approach automates the entire process** - from analyzing the job posting to generating the final PDF/HTML document in a single command:

```
+------------------------+     +-------------------------+
|   Master CV Database   |     |      Job Posting        |
|                        |     |                         |
+----------+-------------+     +-----------+-------------+
           |                               |
           | INPUT: /cv_database.json      | INPUT: /sample_job_posting.txt
           v                               v
+------------------------------------------------+
|              AI CV Generator                    |
|             ai_cv_generator.py                  |
+------------------------------------------------+
                         |
                         | STEP 1: ALWAYS PERFORMED
                         v
+------------------------------------------------+
|                Tailored CV Data                 |
|              tailored_[NAME].json               |
+------------------------------------------------+
                         |
                         | STEP 2: SKIPPED IF --json-only FLAG IS USED
                         v
+------------------------------------------------+
|                   CSV Files                     |
|            [NAME]_data directory                |
+------------------------------------------------+
                         |
                         | STEP 3: SKIPPED IF --json-only FLAG IS USED
                         v
+------------------------------------------------+
|              Final CV/Resume Output             |
|                                                 |
|          - /output/[NAME].pdf                   |
|          - /output/[NAME].html (if --html-too)  |
+------------------------------------------------+
```

### Manual Filtering Workflow

Alternatively, you can manually filter your CV database using tags or company filters without AI assistance:

```
+------------------------+
|   Master CV Database   |
|                        |
+----------+-------------+
           |
           | INPUT: /cv_database.json
           v
+------------------------------------------------+
|             JSON to CSV Converter               |
|           json_to_csv_converter.py              |
|       with --filter-tag or --filter-company     |
+------------------------+-------------------------+
                         |
                         | OUTPUT: /my_[TYPE]_data/*.csv
                         v
+------------------------------------------------+
|                   CSV Files                     |
|    /my_resume_data/ or /my_cv_data/ directory   |
|      - entries.csv                              |
|      - contact_info.csv                         |
|      - text_blocks.csv                          |
|      - aside_sections.csv                       |
|      - aside_entries.csv                        |
+------------------------+-------------------------+
                         |
           +-------------+------------+
           |                          |
           | INPUT: /templates/       | INPUT: /my_[TYPE]_data/*.csv
           | my_[TYPE].rmd            |
           v                          v
+----------------------+   +----------------------------+
|    RMD Template      |   |      R Render Script      |
|    my_cv.rmd or      |-->|        render.r           |
|    my_resume.rmd     |   |                           |
+----------------------+   +-------------+-------------+
                                         |
                                         | OUTPUT: /output/[NAME].*
                                         v
                           +------------------------------+
                           |      Final CV/Resume        |
                           |  - /output/[NAME].pdf       |
                           |  - /output/[NAME].html      |
                           |  - /output/[NAME].txt       |
                           +------------------------------+
```

In this workflow:

1. You directly filter your CV database using one or more of these filters:
   - Document type (--type): Filter by `cv` or `resume` tags (required)
   - Tag filter (--filter-tag): Filter by skill areas like `bioinformatics`, `machine_learning`, etc.
   - Company filter (--filter-company): Filter by company categories like `academic`, `biotech`, etc.

2. Examples of filtering commands:
   ```bash
   # Basic filtering by document type
   python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume
   
   # Filter by tag (only entries with both "resume" and "bioinformatics" tags)
   python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume --filter-tag bioinformatics
   
   # Filter by company (only entries in the "biotech" company category)
   python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume --filter-company biotech
   ```

3. After filtering, render the CV/resume as usual:
   ```bash
   Rscript render.r --template my_resume.rmd --output CompanyX_Resume --html --data-dir my_resume_data
   ```

### Step-by-Step Workflow for Beginners

1. **Prepare Your Master CV Database**
   - Create or update `cv_database.json` with all your experience, education, skills, etc.
   - This is your complete "source of truth" for all CV entries.

2. **Save the Job Posting**
   - Save the job posting you're applying for as a text file (e.g., `sample_job_posting.txt`).

3. **Run the AI CV Generator**
   - This analyzes the job posting and filters your master CV data to create a tailored JSON file.
   ```bash
   python ai_cv_generator.py --job-posting sample_job_posting.txt --output-name "CompanyX_Resume" --cv-data cv_database.json
   ```
   - The generator will create a tailored JSON file in the `tailored_json` directory (e.g., `tailored_json/CompanyX_Resume.json`).
   - **By default, the generator automatically runs all steps**:
     - Analyzes the job posting with AI
     - Creates a tailored JSON file
     - Converts the JSON to CSV files
     - Renders the final PDF document
   - Key arguments that control the workflow:
     - `--json-only`: Stop after generating the tailored JSON (don't create CSV files or render the document)
     - `--html-too`: Generate HTML version in addition to PDF
     - `--improve-descriptions`: Use AI to improve entry descriptions (enabled by default)

4. **Convert JSON to CSV** (automated by the generator)
   - This step is automatically performed by the AI CV Generator, but you can run it manually if needed:
   ```bash
   python json_to_csv_converter.py --json tailored_json/CompanyX_Resume.json --output-dir CompanyX_Resume_data --type resume
   ```
   - CSV files will be created in a directory named after your output name: `CompanyX_Resume_data/`

5. **Render the Final CV/Resume** (automated by the generator)
   - This step is also automatically performed by the AI CV Generator unless you use the `--json-only` flag.
   - If you want to re-render manually, use:
   ```bash
   Rscript render.r --template my_resume.rmd --output CompanyX_Resume --html
   ```

6. **Review and Submit**
   - Your tailored CV/resume is now ready to review and submit!
   - The output files will be organized in these directories:
     - Final PDF/HTML: `output/CompanyX_Resume.pdf`, `output/CompanyX_Resume.html`
     - Tailored JSON: `tailored_json/CompanyX_Resume.json`
     - CSV files: `CompanyX_Resume_data/*.csv`
     - API interaction logs: `logs/api_interactions_TIMESTAMP.log`
     - Main process logs: `logs/cv_generator_TIMESTAMP.log`

## Tool Documentation

### AI CV Generator (`ai_cv_generator.py`)

Automatically analyzes job postings with OpenAI's GPT models and filters your CV data to create tailored applications.

#### Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|--------|
| `--job-posting` | Path to the job posting text file | Yes | None |
| `--output-name` | Name for the output files (without extension) | Yes | None |
| `--cv-data` | Path to the CV/resume JSON data file | No | `cv_database.json` |
| `--output-dir` | Directory to save the output files | No | `output` |
| `--type` | Type of document to generate (`cv` or `resume`) | No | `resume` |
| `--ai-service` | AI service to use (`openai` or `claude`) | No | `openai` |
| `--openai-model` | OpenAI model to use | No | `gpt-4o` |
| `--claude-model` | Claude model to use | No | `claude-3-7-sonnet-20250219` |
| `--temperature` | Temperature setting for AI models (0.0-1.0). Lower values are more deterministic, higher values more creative | No | 0.7 |
| `--use-prompt-only` | Use direct prompt for CV tailoring instead of entry-by-entry analysis | No | False |
| `--improve-descriptions` | Use AI to improve entry descriptions to better match job requirements | No | **True** |
| `--json-only` | Only generate the JSON file, not the document | No | False |
| `--html-too` | Generate HTML version in addition to PDF | No | False |
| `--verbose` | Enable detailed logging of AI interactions | No | False |
| `--entries-per-section` | JSON string defining maximum entries per section | No | See below |

#### Entry Selection Process

The AI CV Generator automatically selects the most relevant entries from your CV database through a smart scoring and filtering process:

1. **Scoring**: Each entry is scored from 0-10 based on relevance to the job posting
2. **Grouping**: Entries are grouped by section (education, experience, etc.)
3. **Sorting**: Within each section, entries are sorted by relevance score (highest first)
4. **Selection**: Top-scoring entries are selected based on the maximum allowed per section
5. **Minimum Quality**: Only entries with a score ≥ 3 are included, regardless of maximum entries

**Default Maximum Entries Per Section:**

```json
{
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
```

**Customizing Maximum Entries per Section:**

Use the `--entries-per-section` parameter with a JSON string:

```bash
# Allow more education entries but fewer research positions
python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" \
  --entries-per-section '{"education": 3, "research_positions": 1}'
```

#### Detailed Entry Scoring Example

Here's how entry scoring and selection works in practice:

1. **Job Analysis**: The AI first analyzes the job posting to extract key requirements:
   - Required skills and technologies
   - Desired experience areas
   - Key responsibilities
   - Industry knowledge requirements
   - Soft skills emphasized

2. **Entry Scoring**: Each CV entry is scored with reasoning:

   ```
   Entry: "Senior Data Scientist at TechCorp"
   Score: 8/10
   Reasoning: "Highly relevant - demonstrates experience with machine learning models 
              and large dataset analysis mentioned in job requirements."
   ```

3. **Section-Based Selection**: Entries are filtered by relevance with a practical example:

   Example for "experience" section with max_entries=2:
   ```
   1. Data Scientist at AI Company (Score: 9/10) ✓ SELECTED
   2. ML Engineer at Tech Startup (Score: 7/10) ✓ SELECTED
   3. Software Developer at Web Company (Score: 5/10) ✗ NOT SELECTED
   4. IT Support at University (Score: 2/10) ✗ NOT SELECTED (below threshold)
   ```

#### Path Handling and Output Directories

**IMPORTANT**: Always use relative paths rather than absolute paths to avoid permission issues:

- ✓ Use: `./output` or `output` (relative to current directory)
- ✗ Avoid: `/output` (absolute path from root)

The script creates these directories relative to your current working directory:

```
./output/         - For final PDF/HTML documents
./tailored_json/  - For tailored JSON files
./logs/           - For logging files
./{output-name}_data/ - For CSV files
```

If files seem to be missing after running the script, verify that you're not using absolute paths that might be writing to locations requiring elevated permissions.

#### Usage Examples

```bash
# Generate a tailored resume named "CompanyX_Resume" from a job posting using OpenAI
# Uses the default cv_database.json file
python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" --type resume

# Specify a custom CV database file
python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" --cv-data my_custom_cv.json

# Disable AI-improved descriptions (enabled by default)
python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" --type resume --improve-descriptions=False

# Generate a tailored CV using Claude with custom section entry limits
python ai_cv_generator.py --job-posting academic_position.txt --output-name "University_CV" --type cv \
  --ai-service claude --entries-per-section '{"education": 2, "academic_articles": 5}'

# Generate a tailored CV using the prompt-only approach with Claude and generate HTML too
python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" \
  --type resume --ai-service claude --use-prompt-only --html-too

# Use a lower temperature for more deterministic/focused output
python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" --temperature 0.2

# Use a higher temperature for more creative output
python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" --temperature 0.9
```

### JSON to CSV Converter (`json_to_csv_converter.py`)

Converts a structured JSON file containing resume/CV data into the CSV format expected by the render.r script.

#### Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|--------|
| `--json` | Path to the JSON file | Yes | None |
| `--output-dir` | Directory to write CSV files | Yes | None |
| `--type` | Type of document (`cv` or `resume`) | Yes | None |
| `--filter-company` | Filter entries by company. Use comma-separated values for multiple companies | No | None |
| `--filter-tag` | Filter entries by tag. Use comma-separated values for multiple tags | No | None |
| `--filter-logic` | Logic to apply for filtering (`and` or `or`). With `and`, entries must match all filters; with `or`, entries must match any filter | No | `and` |

#### Usage Examples

```bash
# Convert JSON to CSV files for a resume
python json_to_csv_converter.py --json cv_data.json --output-dir my_resume_data --type resume

# Convert JSON to CSV files for a CV with company filter
python json_to_csv_converter.py --json cv_data.json --output-dir my_cv_data --type cv --filter-company biotech

# Convert JSON to CV and filter by tag
python json_to_csv_converter.py --json tailored_CompanyX.json --output-dir my_cv_data --type cv --filter-tag machine_learning

# Filter with multiple tags using OR logic
python json_to_csv_converter.py --json cv_data.json --output-dir my_resume_data --type resume --filter-tag bioinformatics,machine_learning --filter-logic or

# Filter with multiple companies using AND logic
python json_to_csv_converter.py --json cv_data.json --output-dir my_cv_data --type cv --filter-company biotech,academic --filter-logic and

# Combine tag and company filters
python json_to_csv_converter.py --json cv_data.json --output-dir my_resume_data --type resume --filter-tag bioinformatics --filter-company biotech
```

### CSV to JSON Converter (`csv_to_json_converter.py`)

Converts CSV files in the format expected by the render.r script into a structured JSON file that can be used as a master database.

#### Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|--------|
| `--input-dir` | Directory containing CSV files | Yes | None |
| `--output-file` | Path to save the JSON file | No | `cv_database.json` |

#### Usage Examples

```bash
# Convert CSV files to a JSON database
python csv_to_json_converter.py --input-dir my_resume_data --output-file cv_database.json

# Use a different input directory
python csv_to_json_converter.py --input-dir my_cv_data --output-file full_cv_database.json
```

### CV Database Editor (`cv_database_editor.py`)

Provides a simple way to add new entries to your cv_database.json file or edit existing ones without manually editing the JSON.

#### Commands

| Command | Description |
|---------|-------------|
| `add-entry` | Add a new entry to the database |
| `edit-entry` | Edit an existing entry by ID |
| `list-entries` | List all entries with their IDs |
| `add-skill-category` | Add a new skill category |
| `edit-contact` | Edit contact information |

#### Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|--------|
| `--database` | Path to the database file | No | `cv_database.json` |
| `--entry-id` | ID of the entry to edit (only for `edit-entry`) | Yes (for `edit-entry`) | None |

#### Usage Examples

```bash
# List all entries with their IDs
python cv_database_editor.py list-entries --database cv_database.json

# Add a new entry interactively
python cv_database_editor.py add-entry --database cv_database.json

# Edit an existing entry
python cv_database_editor.py edit-entry --database cv_database.json --entry-id 5

# Add a skill category
python cv_database_editor.py add-skill-category --database cv_database.json

# Edit contact information
python cv_database_editor.py edit-contact --database cv_database.json
```

### Render Script (`render.r`)

Unified R script for rendering the HTML and PDF versions of both CV and resume documents from CSV data files.

#### Function Parameters

| Parameter | Description | Default |
|-----------|-------------|--------|
| `template` | Template file to use | `"my_cv.rmd"` |
| `output_filename` | Output filename without extension | Based on template type and date |
| `html_too` | Generate HTML version in addition to PDF | `FALSE` |
| `skip_pdf` | Skip PDF generation and only generate HTML | `FALSE` |
| `plain_text_too` | Generate plain text version for job applications | `FALSE` |
| `custom_image_path` | Path to custom image to use instead of network logo | `NULL` |
| `data_dir` | Data directory to use | Determined by template type |

#### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|--------|
| `-t, --template` | Template file | `"my_cv.rmd"` |
| `-o, --output` | Output filename without extension | Based on template type and date |
| `--html` | Generate HTML version in addition to PDF | `FALSE` |
| `--skip-pdf` | Skip PDF generation and only create HTML | `FALSE` |
| `--plaintext` | Generate plain text version for job applications | `FALSE` |
| `-i, --image` | Path to custom image to use instead of network logo | None |
| `-d, --data-dir` | Data directory to use | Determined by template type |

#### Usage Examples

##### From R Console

```r
# Basic usage with default settings
source("render.r")
render_document(template = "my_cv.rmd")

# Generate resume with HTML version too
render_document(
  template = "my_resume.rmd",
  output_filename = "BrendanMiller_CompanyX",
  html_too = TRUE
)

# Generate CV with custom image and plain text version
render_document(
  template = "my_cv.rmd",
  output_filename = "BrendanMiller_CompanyX",
  html_too = TRUE,
  plain_text_too = TRUE,
  custom_image_path = "/path/to/logo.png",
  data_dir = "my_cv_data"
)
```

##### From Command Line

```bash
# Basic usage with default settings
Rscript render.r --template my_cv.rmd

# Generate resume with custom output name and HTML format
Rscript render.r --template my_resume.rmd --output BrendanMiller_CompanyX --html

# Generate CV with custom image
Rscript render.r --template my_cv.rmd --image /path/to/logo.png --html

# Generate plain text version for job applications
Rscript render.r --template my_resume.rmd --plaintext

# Skip PDF generation and only create HTML
Rscript render.r --template my_resume.rmd --skip-pdf --html

# Specify custom data directory
Rscript render.r --template my_cv.rmd --data-dir my_custom_data
```

#### Output Files

The script generates the following output files in the `output/` directory:

- **PDF**: `output/[output_filename].pdf` (Primary output format)
- **HTML**: `output/[output_filename].html` (If `html_too` or `--html` is used)
- **Plain Text**: `output/[output_filename].txt` (If `plain_text_too` or `--plaintext` is used)

Additionally, the script will copy the template file to the output directory as: `output/[template_name]`

## Important Files

- `setup.Rmd` - Run the first code chunk to install the necessary R packages. The chunks below that instantiate the original CV templates used in the `datadrivencv` library. I have edited these myself and moved my edited versions of `render_cv.r` and `cv_printing_function.r` to the root directory of this repo.

- `cv_printing_functions.r` - Contains the printing functions used to convert the `*.csv` files into HTML/Markdown code in the `cv.rmd` template. This file has been customized to include additional formatting options.

- `render.r` - Unified script used to render the HTML and PDF versions of both the full CV and the concise resume. This replaces the separate `render_cv.r` and `render_resume.r` scripts.

- `/output/my_cv.rmd` - Custom version of the CV markdown template. The rendered PDF and HTML versions will be placed in this folder.

- `/output/my_resume.rmd` - Custom version of the resume markdown template, a more concise version of the CV.

- `css/styles.css` - Contains the CSS code used when rendering the RMD files into PDF and HTML versions.

- `my_cv_data/*.csv` - Where the full CV entries are stored.

- `my_resume_data/*.csv` - Where the resume entries are stored, including:
  - `entries.csv` - Main content entries for the resume
  - `aside_sections.csv` - Defines categories for the skills/expertise in the ASIDE section
  - `aside_entries.csv` - Individual skills/expertise items for each category

## Google Scholar Integration

The CV/resume now supports displaying a bar chart of your Google Scholar citations for the last 5 years in the aside section.

### Adding Citations Chart to Your CV/Resume

1. Find your Google Scholar ID from your profile URL: `https://scholar.google.com/citations?user=YOUR_ID`

2. In your template file (e.g., `templates/my_resume.rmd`), the following code is already included in the Aside section:

   ```r
   # Replace 'YOUR_SCHOLAR_ID' with your actual Google Scholar ID
   CV %>% print_scholar_citations(scholar_id = "YOUR_SCHOLAR_ID", bar_color = "#4292c6")
   ```

3. Replace `"YOUR_SCHOLAR_ID"` with your actual Google Scholar ID.

### Customizing the Citations Chart

You can customize the appearance of the chart with these parameters:

- `bar_color` - The color of the citation bars (default: "#969696")
- `text_color` - The color of the text labels (default: "#777777")
- `base_size` - Base font size for the chart (default: 14)

Example with custom colors:

```r
CV %>% print_scholar_citations(
  scholar_id = "YOUR_SCHOLAR_ID",
  bar_color = "#41ab5d",  # Green bars
  text_color = "#333333"  # Darker text
)
```

To disable the citations chart, simply comment out or remove the code block from your template.

## Usage Instructions

### From R Console

The CV and resume generation is done through the unified `render_document()` function:

```r
# Generate CV with default settings
source("render.r")
render_document(template = "my_cv.rmd")

# Generate CV with custom image instead of network logo
render_document(
  template = "my_cv.rmd",                            # Use CV template
  custom_image_path = "/path/to/your/logo.png",       # Custom image to use in the aside section
  output_filename = "BrendanMiller_CompanyX",         # Custom output filename
  html_too = TRUE                                     # Generate HTML version too
)

# Generate resume with default settings
render_document(template = "my_resume.rmd")

# For more control, call the function with parameters
render_document(
  template = "my_resume.rmd",                         # Choose resume template
  output_filename = "BrendanMiller_CompanyX",         # Custom output filename
  html_too = TRUE,                                    # Generate HTML version too
  plain_text_too = TRUE,                              # Generate plain text version for job applications
  data_dir = "my_resume_data"                         # Explicitly specify data directory
)
```

### From Command Line

Both the CV and resume can be generated directly from the command line using the unified script:

```bash
# Generate CV with default settings
Rscript render.r --template my_cv.rmd

# Generate CV with custom image instead of network logo
Rscript render.r --template my_cv.rmd --image /path/to/your/logo.png

# Generate CV with custom image and other options
Rscript render.r --template my_cv.rmd --image /path/to/your/logo.png --output BrendanMiller_CompanyX --html

# Generate resume with default settings
Rscript render.r --template my_resume.rmd

# Generate resume with custom settings
Rscript render.r --template my_resume.rmd --output BrendanMiller_CompanyX --html

# Generate a plain text version for LinkedIn/job applications
Rscript render.r --template my_resume.rmd --output BrendanMiller_LinkedIn --plaintext

# Explicitly specify data directory
Rscript render.r --template my_cv.rmd --data-dir my_custom_data

# See all available options
Rscript render.r --help
```

Command line options for `render.r`:
- `-t, --template` - Template file (default: "my_cv.rmd")
- `-o, --output` - Output filename without extension (default: determined by template type)
- `--html` - Flag to generate HTML version in addition to PDF
- `--plaintext` - Flag to generate a plain text version for job applications
- `-i, --image` - Path to custom image (PNG or JPEG) to use instead of network logo in the aside section
- `-d, --data-dir` - Data directory to use (default: determined by template name)

## Customizing Image Size and Positioning

You can customize the size and positioning of both custom images and the network logo in your CV or resume. This can be done by modifying specific parameters in the template file:

### For Custom Images

When using a custom image via the `--image` parameter, you can adjust how it appears by modifying the markdown image parameters in `templates/my_resume.rmd` (or `templates/my_cv.rmd`):

```r
# Change these values in the cat() function to adjust the image size
cat(paste0("![](", params$custom_image_path, "){width=100% height=200px}"))
```

- `width=100%` - Controls the width of the image (percentage of container)
- `height=200px` - Controls the height of the image (in pixels)

### For Network Logo

If you're using the default network logo, you can adjust its parameters in the `build_network_logo_custom` function call:

```r
build_network_logo_custom(CV$entries_data, 
                        margin_top = "-10px", 
                        margin_bottom = "0px", 
                        width = "100%", 
                        height = "200px")
```

- `margin_top` - Controls the vertical positioning (negative values move it up)
- `margin_bottom` - Controls the space below the image
- `width` - Controls the width (percentage or pixels)
- `height` - Controls the height (pixels)

### Overall Positioning

You can also adjust the overall positioning of the aside section using CSS. This is particularly useful for aligning the image with other elements on the page:

```html
<style>
.pagedjs_page:first-of-type .aside {
  margin-top: -50px; /* Move content higher */
}
</style>
```

This CSS block can be found at the top of the template file and adjusted as needed.

## Output Formats

### PDF (Default)

The default output is a PDF file optimized for print and sharing. This format will:
- Automatically be generated for every render
- Include properly formatted links as footnotes
- Use professional formatting with optimized typography

### HTML (Optional)

Adding the `--html` flag or setting `html_too = TRUE` will generate an HTML version that:
- Contains active hyperlinks
- Can be hosted on a website or shared digitally
- Looks identical to the PDF version but with interactive elements

### Plain Text (Optional)

Adding the `--plaintext` flag or setting `plain_text_too = TRUE` will generate a plain text version of your resume (.txt file). This format is optimized for:
- Copy-pasting into LinkedIn Easy Apply forms
- Online job application systems
- ATS (Applicant Tracking Systems)

## JSON-Based CV/Resume Management

The new JSON-based system offers a more flexible and maintainable way to manage your professional information.

### JSON Structure

The `cv_database.json` file uses this structure:

```json
{
  "meta": { "version": "1.0", "last_updated": "2025-04-27" },
  "contact_info": { ... },
  "entries": [
    {
      "id": "unique_entry_id",
      "section": "current_position",
      "title": "Post-doctoral Research Fellow",
      "descriptions": [ ... ],
      "tags": ["resume", "cv", "bioinformatics", ...],
      "importance": 10,
      "companies": ["academic", "biotech"]
    },
    ...
  ],
  "skills": [ ... ],
  "text_blocks": [ ... ]
}
```

### Benefits of the JSON System

- **Unified Storage**: All data in one file instead of multiple CSVs
- **Tagging System**: Each entry has tags to identify which documents it belongs to (cv, resume) and skills
- **Company Targeting**: Entries can be associated with specific companies or industries
- **Importance Ranking**: Entries have an importance score to prioritize them
- **Structured Skills**: Skills are organized by category with proficiency levels

### Tag System Between JSON and CSV Files

The tagging system is a critical component that controls how entries in the master JSON database are filtered and included in the CSV files used for rendering documents. Here's how it works:

#### How Tags Are Used in the JSON Database

1. **Document Type Tags**: Each entry in `cv_database.json` has a `tags` array that includes values like:
   - `"resume"` - Indicates the entry should appear in resume documents
   - `"cv"` - Indicates the entry should appear in CV documents
   - Some entries may have both tags if they should appear in both document types

2. **Company-Specific Tags**: For tailored applications, entries can include company-specific tags:
   - `"company_merck"`, `"company_dropletbiosciences"`, etc.
   - These tags are used to include specialized versions of entries for specific companies

3. **Category Tags**: Entries often include category tags:
   - `"education"`, `"research"`, `"bioinformatics"`, etc.
   - These can be used for focused filtering based on job requirements

#### How Text Blocks Use Tags

Text blocks (like introductions or summaries) also use the tag system:

```json
{
  "id": "intro",
  "content": "Post-doctoral research fellow developing computational tools...",
  "tags": ["cv", "resume"]
},
{
  "id": "company_dropletbiosciences",
  "content": "Post-doctoral research fellow with expertise in circulating cell-free DNA...",
  "tags": ["cv", "resume"]
}
```

This allows for customized text blocks that target specific companies or document types.

#### Tag-Based Filtering in JSON to CSV Conversion

When you run the JSON to CSV converter:

```bash
python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume
```

The following happens:

1. The `--type resume` parameter acts as a filter
2. Only entries with the `"resume"` tag are included in the output CSV files
3. If using `--type cv` instead, only entries with the `"cv"` tag would be included

#### Enhanced Filtering with Multiple Tags and Companies

The system supports filtering by multiple tags and companies with flexible logic:

1. **Multiple Tags**: You can filter by multiple tags using comma-separated values:
   ```bash
   python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume --filter-tag bioinformatics,machine_learning
   ```

2. **Multiple Companies**: You can filter by multiple companies using comma-separated values:
   ```bash
   python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume --filter-company biotech,academic
   ```

3. **AND/OR Logic**: You can specify whether entries must match ALL filters (AND logic) or ANY filter (OR logic):
   ```bash
   # AND logic (default): Entry must have ALL specified tags
   python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume --filter-tag bioinformatics,machine_learning --filter-logic and
   
   # OR logic: Entry must have ANY of the specified tags
   python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume --filter-tag bioinformatics,machine_learning --filter-logic or
   ```

4. **Combining Tags and Companies**: You can combine tag and company filters:
   ```bash
   # Default AND logic: Entry must have the "resume" tag AND the "bioinformatics" tag AND be in the "biotech" company category
   python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume --filter-tag bioinformatics --filter-company biotech
   
   # OR logic: Entry must have the "resume" tag AND either the "bioinformatics" tag OR be in the "biotech" company category
   python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume --filter-tag bioinformatics --filter-company biotech --filter-logic or
   ```

The filtering logic works as follows:

- **Base Filter**: The document type (--type) is ALWAYS required. All entries must have this tag regardless of other filters.
- **Multiple Tags**: When specifying multiple tags with AND logic, entries must have ALL specified tags. With OR logic, entries must have AT LEAST ONE of the specified tags.
- **Multiple Companies**: When specifying multiple companies with AND logic, entries must be associated with ALL specified companies. With OR logic, entries must be associated with AT LEAST ONE of the specified companies.
- **Combining Filters**: The same logic (AND/OR) applies across both tag and company filters when both are specified.

#### Tags in Tailored JSON Files

When the AI CV Generator creates a tailored JSON file for a specific job application:

1. It preserves the original tags from selected entries
2. It may add additional job-specific tags based on the analysis
3. When this tailored JSON is converted to CSV, the same tag-based filtering applies

This system ensures that your CSV files (and resulting documents) contain only the entries that are relevant to the specific document type and job application.

## CV Database Editor

The `cv_database_editor.py` script provides a convenient way to maintain your CV/resume data without directly editing JSON files. The editor allows you to add, edit, and manage entries, skill categories, text blocks, and contact information.

### Features

- Interactive command-line interface for managing CV/resume data
- Add and edit entries with comprehensive prompts
- Manage skill categories and individual skills
- Edit text blocks for summary and other content sections
- Update contact information
- User-friendly section selection with numbered lists

### Usage

```bash
python cv_database_editor.py [command] --database cv_database.json [options]
```

### Available Commands

| Command | Description | Options |
|---------|-------------|---------|
| `add-entry` | Add a new entry to your CV/resume | `--database` |
| `edit-entry` | Edit an existing entry | `--database`, `--entry-id` |
| `list-entries` | List all entries with their IDs | `--database` |
| `add-skill-category` | Add a new skill category | `--database` |
| `list-skill-categories` | List all skill categories | `--database` |
| `edit-skill-category` | Edit an existing skill category | `--database`, `--category-id` |
| `list-text-blocks` | List all text blocks | `--database` |
| `edit-text-block` | Edit an existing text block | `--database`, `--block-id` |
| `edit-contact` | Edit contact information | `--database` |

### Examples

#### Adding a New Entry

```bash
python cv_database_editor.py add-entry --database cv_database.json
```

You'll see interactive prompts like:

```
Available sections:
  1. education
  2. work_experience
  3. publications
  4. teaching_positions

Choose a section:
  [number] - Use an existing section (enter the number)
  [name] - Create a new section (enter a new name)
  [n] - Create a new section (you'll be prompted for the name)

Section choice: n
Enter new section name: volunteer_work
Created new section: 'volunteer_work'

Title: Community Organizer
Institution/Company: Local Environmental Group
Location: Boston, MA
Start date (e.g., 2020): 2022
End date (e.g., 2022, or 'Current'): Current
Description (leave empty to finish): Led bi-weekly cleanup efforts in local parks
Description (leave empty to finish): Organized educational workshops on sustainability
Description (leave empty to finish): 
Company tag (leave empty to finish): environmental
Company tag (leave empty to finish): nonprofit
Company tag (leave empty to finish): 
Include in CV? (y/n): y
Include in resume? (y/n): y
Additional tag (leave empty to finish): environmental
Additional tag (leave empty to finish): 
Importance (0-10, higher values are more important): 8

Entry added successfully!
```

This creates the following entry in the JSON file:

```json
{
  "section": "volunteer_work",
  "title": "Community Organizer",
  "institution": "Local Environmental Group",
  "loc": "Boston, MA",
  "start": "2022",
  "end": "Current",
  "descriptions": [
    "Led bi-weekly cleanup efforts in local parks",
    "Organized educational workshops on sustainability"
  ],
  "companies": [
    "environmental",
    "nonprofit"
  ],
  "tags": [
    "cv",
    "resume",
    "environmental"
  ],
  "importance": 8
}
```

After running the JSON to CSV converter:

```bash
python json_to_csv_converter.py --json cv_database.json --output-dir my_cv_data --type cv
```

This entry would appear in `my_cv_data/entries.csv` as:

```csv
section,title,loc,institution,start,end,description_1,description_2,in_cv,in_resume,importance
volunteer_work,Community Organizer,Boston MA,Local Environmental Group,2022,Current,"Led bi-weekly cleanup efforts in local parks","Organized educational workshops on sustainability",TRUE,TRUE,8
```

And if you used the `--type resume` option, it would appear in `my_resume_data/entries.csv` with the same format.

#### Editing a Skill Category

First, list the skill categories:

```bash
python cv_database_editor.py list-skill-categories --database cv_database.json
```

Output:
```
Skill Categories:
ID: 0 - Programming - Tags: cv, resume
  Entries: 5 skills
ID: 1 - Biology - Tags: cv, resume
  Entries: 4 skills
```

Then edit a specific category:

```bash
python cv_database_editor.py edit-skill-category --database cv_database.json --category-id 0
```

You'll interact with prompts like:

```
Editing skill category 0:
Current category: {"category": "Programming", "entries": [{"name": "Python", "level": "Expert"}, {"name": "R", "level": "Proficient"}, ...]}

Category name [Programming]: 

Current skills:
  0: Python - Expert
  1: R - Proficient

Edit skills? (y/n): y

Options:
1. Add a new skill
2. Edit an existing skill
3. Remove a skill
4. Done editing skills
Choose an option (1-4): 1
Skill name: JavaScript
Skill level (e.g., Proficient, 5/5): Intermediate
Skill added.

Options:
1. Add a new skill
2. Edit an existing skill
3. Remove a skill
4. Done editing skills
Choose an option (1-4): 2
Skill ID to edit (0-2): 0
Skill name [Python]: 
Skill level [Expert]: Expert (5+ years)
Skill updated.

Options:
1. Add a new skill
2. Edit an existing skill
3. Remove a skill
4. Done editing skills
Choose an option (1-4): 4

Current tags: cv, resume
Edit tags? (y/n): n

Skill category updated successfully!
```

The updated skill category in the JSON file will look like:

```json
{
  "category": "Programming",
  "entries": [
    {
      "name": "Python",
      "level": "Expert (5+ years)"
    },
    {
      "name": "R",
      "level": "Proficient"
    },
    {
      "name": "JavaScript",
      "level": "Intermediate"
    }
  ],
  "tags": [
    "cv",
    "resume"
  ]
}
```

#### Editing a Text Block

List text blocks first:

```bash
python cv_database_editor.py list-text-blocks --database cv_database.json
```

Output:
```
Text Blocks:
ID: 0 - intro - Tags: cv, resume
  Content: Post-doctoral research fellow developing computational...
ID: 1 - references1 - Tags: cv, resume
  Content: Dr. Jean Fan, Johns Hopkins University, Department of ...
```

Then edit a specific text block:

```bash
python cv_database_editor.py edit-text-block --database cv_database.json --block-id 0
```

Interactive prompts will look like:

```
Editing text block 0:
Current text block ID: intro
Current content: Post-doctoral research fellow developing computational tools for analysis of single-cell and spatial transcriptomics data. Molecular biologist with strong background in clinical diagnostics and cancer biology.
Current tags: cv, resume

Block ID [intro]: 

Edit content? (y/n): y
Enter new content (press Enter then Ctrl+D or Ctrl+Z on empty line to finish):
Research scientist with expertise in computational biology and bioinformatics. Specialized in developing tools for single-cell and spatial transcriptomics analysis with a background in cancer genomics and clinical applications.

Current tags: cv, resume
Edit tags? (y/n): n

Text block updated successfully!
```

The updated text block in the JSON file will look like:

```json
{
  "id": "intro",
  "content": "Research scientist with expertise in computational biology and bioinformatics. Specialized in developing tools for single-cell and spatial transcriptomics analysis with a background in cancer genomics and clinical applications.",
  "tags": [
    "cv",
    "resume"
  ]
}
```

After running the JSON to CSV converter, this text block would appear in `my_cv_data/text_blocks.csv` and `my_resume_data/text_blocks.csv` as:

```csv
id,text,in_cv,in_resume
intro,"Research scientist with expertise in computational biology and bioinformatics. Specialized in developing tools for single-cell and spatial transcriptomics analysis with a background in cancer genomics and clinical applications.",TRUE,TRUE
```

### JSON to CSV Conversion Examples

Here's how each type of JSON entry is converted to CSV format when using the json_to_csv_converter:

#### Regular Entries (from JSON to entries.csv)

JSON in `cv_database.json`:
```json
{
  "section": "volunteer_work",
  "title": "Community Organizer",
  "institution": "Local Environmental Group",
  "loc": "Boston, MA",
  "start": "2022",
  "end": "Current",
  "descriptions": [
    "Led bi-weekly cleanup efforts in local parks",
    "Organized educational workshops on sustainability"
  ],
  "tags": ["cv", "resume", "environmental"],
  "importance": 8
}
```

Conversion to `entries.csv`:
```csv
section,title,loc,institution,start,end,description_1,description_2,in_cv,in_resume,importance
volunteer_work,Community Organizer,Boston MA,Local Environmental Group,2022,Current,"Led bi-weekly cleanup efforts in local parks","Organized educational workshops on sustainability",TRUE,TRUE,8
```

#### Skill Categories (from JSON to aside_sections.csv and aside_entries.csv)

JSON in `cv_database.json`:
```json
{
  "category": "Programming",
  "entries": [
    {
      "name": "Python",
      "level": "Expert (5+ years)"
    },
    {
      "name": "R",
      "level": "Proficient"
    },
    {
      "name": "JavaScript",
      "level": "Intermediate"
    }
  ],
  "tags": ["cv", "resume"]
}
```

Conversion to `aside_sections.csv`:
```csv
section_id,section_name,in_cv,in_resume
Programming,Programming,TRUE,TRUE
```

Conversion to `aside_entries.csv`:
```csv
section_id,skill_name,level,in_cv,in_resume
Programming,Python,Expert (5+ years),TRUE,TRUE
Programming,R,Proficient,TRUE,TRUE
Programming,JavaScript,Intermediate,TRUE,TRUE
```

#### Text Blocks (from JSON to text_blocks.csv)

JSON in `cv_database.json`:
```json
{
  "id": "intro",
  "content": "Research scientist with expertise in computational biology and bioinformatics. Specialized in developing tools for single-cell and spatial transcriptomics analysis with a background in cancer genomics and clinical applications.",
  "tags": ["cv", "resume"]
}
```

Conversion to `text_blocks.csv`:
```csv
id,text,in_cv,in_resume
intro,"Research scientist with expertise in computational biology and bioinformatics. Specialized in developing tools for single-cell and spatial transcriptomics analysis with a background in cancer genomics and clinical applications.",TRUE,TRUE
```

### Converting JSON to CSV

After editing your database, convert the JSON to CSV files needed by render.r:

```bash
# For CV
python json_to_csv_converter.py --json cv_database.json --output-dir my_cv_data --type cv

# For Resume
python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume

# For Resume targeting a specific company
python json_to_csv_converter.py --json cv_database.json --output-dir my_resume_data --type resume --filter-company biotech

# For CV filtering by a specific tag
python json_to_csv_converter.py --json cv_database.json --output-dir my_cv_data --type cv --filter-tag machine_learning
```

## AI-Powered CV/Resume Generation

The `ai_cv_generator.py` script uses OpenAI's API and Claude API to analyze job postings and generate tailored CVs/resumes that highlight your most relevant experience.

### Setup and Requirements

1. Install required packages:
   ```bash
   pip install openai anthropic python-dotenv
   ```

2. Create a `.env` file in the project directory with your API keys:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   ```
   
   Note: You only need the API key for the service you plan to use. If you're only using Claude, you can omit the OpenAI key, and vice versa.

2. Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY='your-api-key'
```

### Usage

```bash
# Using OpenAI (default)
python ai_cv_generator.py --job-posting sample_job_posting.txt --output-name "CompanyX_Resume" --type resume

# Using Claude API
python ai_cv_generator.py --job-posting sample_job_posting.txt --output-name "CompanyX_Resume" --type resume --ai-service claude

# Using Claude API with comprehensive prompt approach
python ai_cv_generator.py --job-posting sample_job_posting.txt --output-name "CompanyX_Resume" --type resume --ai-service claude --use-prompt-only

# Control AI creativity with temperature parameter (0.0-1.0)
python ai_cv_generator.py --job-posting sample_job_posting.txt --output-name "CompanyX_Resume" --temperature 0.4
```

### About the `--use-prompt-only` Flag

The AI CV Generator offers two distinct approaches for tailoring your CV/resume:

#### Default Approach (Without `--use-prompt-only`)

Without this flag, the script processes your CV using a detailed entry-by-entry analysis:

- **Methodical Processing**: Each entry in your CV database is individually scored for relevance to the job posting
- **Transparency**: Provides detailed reasoning for why each entry was included/excluded
- **Fine-Grained Control**: Allows setting maximum entries per section with precise control
- **Multiple API Calls**: Makes an API call for each entry, resulting in longer processing time but detailed analysis
- **Improved Descriptions**: When `--improve-descriptions` is used, each entry's description is refined individually

#### Comprehensive Approach (With `--use-prompt-only`)

With the `--use-prompt-only` flag, the script uses a single comprehensive prompt:

- **One-Shot Processing**: Sends the entire CV database and job posting to the AI in a single request
- **Efficiency**: Significantly faster, using only 1-2 API calls instead of dozens
- **Holistic View**: AI considers the entire CV as a cohesive document, potentially resulting in better overall narrative
- **Less Detailed Feedback**: Doesn't provide individual scoring or reasoning for each entry
- **Model Capabilities**: Leverages the AI model's ability to understand and process large contexts
- **Ideal for Large CVs**: Particularly useful when you have a large CV database with many entries

**When to use `--use-prompt-only`:**
- When processing speed is a priority
- When you have a very large CV database
- When using Claude API (which handles long contexts particularly well)
- When you want a more cohesive, narrative-driven tailoring of your CV

**When to use the default approach:**
- When you want detailed reasoning about entry selections
- When you want precise control over which sections get more emphasis
- When you need transparency about how the AI is tailoring your CV
- When fine-tuning the CV is more important than processing speed

### Understanding API Requests and Responses

Depending on which mode you choose, the AI CV Generator makes different types of API requests to OpenAI or Claude. Here are examples of what these requests look like:

#### Entry-by-Entry Mode API Requests (Default)

In the default mode, the generator makes multiple API calls:

1. **Job Analysis Request:** Analyzes the job posting (1 API call)
   ```
   System: "You are an expert career counselor and resume specialist. Analyze the job posting and extract the following:
   1. Required skills and technologies
   2. Desired experience areas
   3. Key responsibilities
   4. Industry and domain-specific knowledge required
   5. Soft skills emphasized
   
   Format your response as a JSON object with these categories."

   User: "Analyze this job posting and extract the key information: [JOB POSTING TEXT]"
   ```

2. **Entry Scoring Requests:** Scores each entry in your CV (1 API call per entry)
   ```
   System: "You are an expert career counselor and resume specialist. Score the relevance of this CV/resume entry
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
   
   Focus on relevance, not just quality. An impressive entry that's irrelevant should score low."

   User: "Resume Entry:
   Title: [ENTRY TITLE]
   Section: [SECTION]
   Institution: [INSTITUTION]
   Descriptions:
   - [DESCRIPTIONS]
   Tags: [TAGS]

   Job Details:
   Required Skills: [SKILLS]
   Desired Experience: [EXPERIENCE]
   Key Responsibilities: [RESPONSIBILITIES]
   Industry Knowledge: [KNOWLEDGE]
   Soft Skills: [SOFT SKILLS]"
   ```

3. **Summary Creation Request:** Creates a tailored professional summary (1 API call)
   ```
   System: "You are an expert resume writer specializing in tailoring professional summaries for specific job applications.
   Create a compelling, concise professional summary (2-3 sentences) that highlights the candidate's most relevant
   skills and experience for this specific job opportunity."

   User: "Current professional summary:
   "[CURRENT SUMMARY]"
   
   Skills:
   [SKILLS LIST]
   
   Job requirements:
   [JOB REQUIREMENTS]
   
   Please create a new tailored professional summary for this job opportunity."
   ```

#### Comprehensive Mode API Request (With `--use-prompt-only`)

With `--use-prompt-only`, the generator makes just one API call that includes everything:

```
System: "You are an expert CV/resume tailoring assistant. Your task is to analyze a job posting and a CV/resume database,
then create a tailored version of the CV/resume that highlights the most relevant skills and experience for the job.

Your output must be a valid JSON object following the same structure as the input CV data, but with:
1. Only the most relevant entries included (max 2-3 per section)
2. Descriptions rewritten to highlight relevant skills and experience
3. A tailored professional summary

The output must be valid JSON that can be parsed with json.loads()."

User: "# Job Posting

[FULL JOB POSTING TEXT]

# CV Database (JSON)

```json
[FULL CV DATABASE JSON]
```

Analyze the job posting and CV database, then create a tailored version of the CV that highlights the most relevant skills and experience for this job.

Your response must be only the valid JSON object for the tailored CV, following the same structure as the input."
```

### Effect of the `--improve-descriptions` Flag

The `--improve-descriptions` flag works differently depending on which mode you're using:

#### In Entry-by-Entry Mode

When used in the default mode, the `--improve-descriptions` flag:

1. Asks the AI to suggest improved descriptions for each relevant entry
2. Stores the original descriptions in an `original_descriptions` field
3. Replaces the descriptions with the AI-enhanced versions

**Example Original Description:**
```
"Developed computational pipelines for analyzing single-cell RNA-seq data"
```

**Example Improved Description:**
```
"Engineered high-performance computational pipelines for analyzing complex single-cell RNA-seq datasets, implementing machine learning algorithms that improved cell type classification accuracy by 35% while reducing processing time"
```

#### In Comprehensive Mode

When used with `--use-prompt-only`, the improvement happens as part of the comprehensive CV generation. The AI is instructed to rewrite descriptions to be more relevant and impactful as part of its overall task.

In this mode, you don't see explicit before/after comparisons, but the resulting descriptions are similarly optimized for the specific job posting.

### How It Works

1. **Analyzes the job posting** with OpenAI to extract key skills and requirements
2. **Scores your CV/resume entries** based on relevance to the job (0-10)
3. **Creates a tailored professional summary** highlighting relevant skills
4. **Selects the most relevant entries** for each section
5. **Optionally improves descriptions** to better match the job requirements
6. **Generates the final document** by running the converter and render scripts

### Sample Flow

1. Save a job posting as a text file (e.g., `job_posting.txt`)
2. Run the AI generator:
   ```bash
   python ai_cv_generator.py --job-posting job_posting.txt --output-name "CompanyX_Resume" --type resume
   ```
3. The script will:
   - Analyze the job posting
   - Select your most relevant entries
   - Generate a tailored resume in both PDF and HTML formats
   - Store the output in the `output` directory

## Docker/Podman Container Support

This project includes Docker containerization support for consistent execution across environments.

### Building the Container

```bash
# Using Docker
docker build -t data-cv .

# Using Podman
podman build -t data-cv .
```

### Running with the Container

```bash
# Using Docker
docker run -v $(pwd):/data_cv data-cv Rscript render.r --template my_resume.rmd --html

# Using Podman
podman run -v $(pwd):/data_cv:Z data-cv Rscript render.r --template my_resume.rmd --html
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
