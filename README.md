# data_cv
Generate custom CV using R and CSS based on `datadrivencv`

## Overview

This repository allows you to create beautifully formatted, data-driven CVs and resumes using R, CSS, and a collection of CSV files. The system is built on top of the `datadrivencv` framework with custom modifications.

## Important Files

- `setup.Rmd` - Run the first code chunk to install the necessary R packages. The chunks below that instantiate the original CV templates used in the `datadrivencv` library. I have edited these myself and moved my edited versions of `render_cv.r` and `cv_printing_function.r` to the root directory of this repo.

- `cv_printing_functions.r` - Contains the printing functions used to convert the `*.csv` files into HTML/Markdown code in the `cv.rmd` template. This file has been customized to include additional formatting options.

- `render_cv.r` - Used to render the HTML and PDF versions of the full CV. 

- `render_resume.r` - Used to render the HTML and PDF versions of the concise resume.

- `/output/my_cv.rmd` - Custom version of the CV markdown template. The rendered PDF and HTML versions will be placed in this folder.

- `/output/my_resume.rmd` - Custom version of the resume markdown template, a more concise version of the CV.

- `css/styles.css` - Contains the CSS code used when rendering the RMD files into PDF and HTML versions.

- `my_cv_data/*.csv` - Where the full CV entries are stored.

- `my_resume_data/*.csv` - Where the resume entries are stored, including:
  - `entries.csv` - Main content entries for the resume
  - `aside_sections.csv` - Defines categories for the skills/expertise in the ASIDE section
  - `aside_entries.csv` - Individual skills/expertise items for each category

## Usage Instructions

### From R Console

The CV and resume generation is done through two primary functions:

```r
# Generate CV
source("render_cv.r")

# Generate resume with default settings
source("render_resume.r")

# For more control, call the function with parameters
render_resume(
  template = "my_resume.rmd",                         # Choose a different template if needed
  output_filename = "BrendanMiller_CompanyX",         # Custom output filename
  html_too = TRUE,                                    # Generate HTML version too
  plain_text_too = TRUE                               # Generate plain text version for job applications
)
```

### From Command Line

Both the CV and resume can be generated directly from the command line:

```bash
# Generate CV with default settings
Rscript render_cv.r

# Generate resume with default settings
Rscript render_resume.r

# Generate resume with custom settings
Rscript render_resume.r --template my_resume.rmd --output BrendanMiller_CompanyX --html

# Generate a plain text version for LinkedIn/job applications
Rscript render_resume.r --output BrendanMiller_LinkedIn --plaintext

# See all available options
Rscript render_resume.r --help
```

Command line options for `render_resume.r`:
- `-t, --template` - Resume template file (default: "my_resume.rmd")
- `-o, --output` - Output filename without extension (default: "BrendanMillerResume_YYYY-MM-DD")
- `--html` - Flag to generate HTML version in addition to PDF
- `--plaintext` - Flag to generate a plain text version for LinkedIn Easy Apply and similar job applications

## Output Formats

### PDF (Default)
The default output is a professionally formatted PDF file suitable for printing or attaching to emails.

### HTML (Optional)
By adding the `--html` flag or setting `html_too = TRUE`, you can generate an HTML version with clickable links and interactive elements.

### Plain Text (Optional)
Adding the `--plaintext` flag or setting `plain_text_too = TRUE` will generate a plain text version of your resume (.txt file). This format is optimized for:
- Copy-pasting into LinkedIn Easy Apply forms
- Online job application systems
- ATS (Applicant Tracking Systems)

The plain text version preserves all content but removes complex formatting that might cause issues when pasting into web forms.

## Data Structure

### ASIDE Entries

The ASIDE section of the resume (which shows expertise and skills) can now be managed through CSV files:

1. `my_resume_data/aside_sections.csv` - Defines categories with fields:
   - `category`: Unique identifier
   - `display_name`: How it appears in the resume
   - `is_code`: Whether entries should be formatted as code (TRUE/FALSE)
   - `sort_order`: Controls display order

2. `my_resume_data/aside_entries.csv` - Contains individual entries with fields:
   - `category`: Links to a section defined above
   - `entry`: The text content
   - `sort_order`: Controls display order within a category

## To Run

If starting from scratch:

1. Have your CV entries in the `*.csv` files in the appropriate data directories.
2. Run all the chunks in `setup.Rmd`.
3. Use either `render_cv.r` or `render_resume.r` to generate your documents.

For quick updates to an existing setup:

1. Edit your data in the appropriate CSV files.
2. Run `render_cv.r` or `render_resume.r` as needed.

## Custom Templates

You can create different templates for different job applications by:

1. Creating a new RMD file based on `my_resume.rmd` or `my_cv.rmd`.
2. Customizing the content/style as needed.
3. Using the `template` parameter when running `render_resume.r` or `render_cv.r`.

## Docker/Podman Usage

The repository includes a Dockerfile that can be used to create a container with all necessary dependencies for generating CVs and resumes. This is particularly useful if you don't have R or the required packages installed on your system.

### Building the Image

```bash
podman build -t cv-generator .
# Or with Docker
docker build -t cv-generator .
```

### Running the Container

Generate a resume with default settings:
```bash
podman run -it --rm -v $(pwd):/cv cv-generator Rscript render_resume.r
```

Generate with custom output name:
```bash
podman run -it --rm -v $(pwd):/cv cv-generator Rscript render_resume.r --output Resume_test
```

Generate both PDF and HTML:
```bash
podman run -it --rm -v $(pwd):/cv cv-generator Rscript render_resume.r --output Resume_test --html

# Generate with plain text for job applications
podman run -it --rm -v $(pwd):/cv cv-generator Rscript render_resume.r --output Resume_JobApp --plaintext
```

Start an interactive R session:
```bash
podman run -it --rm -v $(pwd):/cv cv-generator
```

## Acknowledgements

A huge, huge thanks to [Nick Strayer](https://github.com/nstrayer) for this [amazing tool](http://nickstrayer.me/datadrivencv/). He also has a nice [blog post](https://livefreeordichotomize.com/2019/09/04/building_a_data_driven_cv_with_r/) breaking down how it was built, which is pretty useful to understand the inner workings of the code.
