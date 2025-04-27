# data_cv
Generate custom CV using R and CSS based on `datadrivencv`

## Overview

This repository allows you to create beautifully formatted, data-driven CVs and resumes using R, CSS, and a collection of CSV files. The system is built on top of the `datadrivencv` framework with custom modifications.

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

The `cv_data.json` file uses this structure:

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

### Converting JSON to CSV

To generate the CSV files needed by render.r:

```bash
# For CV
python json_to_csv_converter.py --json cv_data.json --output-dir my_cv_data --type cv

# For Resume
python json_to_csv_converter.py --json cv_data.json --output-dir my_resume_data --type resume

# For Resume targeting a specific company
python json_to_csv_converter.py --json cv_data.json --output-dir my_resume_data --type resume --filter-company biotech

# For CV filtering by a specific tag
python json_to_csv_converter.py --json cv_data.json --output-dir my_cv_data --type cv --filter-tag machine_learning
```

## AI-Powered CV/Resume Generation

The `ai_cv_generator.py` script uses OpenAI's API to analyze job postings and generate tailored CVs/resumes that highlight your most relevant experience.

### Prerequisites

1. Install the OpenAI Python package:
```bash
pip install openai
```

2. Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY='your-api-key'
```

### Usage

```bash
# Basic usage
python ai_cv_generator.py --job-posting job_posting.txt --output-name "Company_Resume" --type resume

# With AI-enhanced descriptions
python ai_cv_generator.py --job-posting job_posting.txt --output-name "Company_Resume" --type resume --improve-descriptions

# Generate only HTML (no PDF)
python ai_cv_generator.py --job-posting job_posting.txt --output-name "Company_Resume" --type resume --html-only
```

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
