# Changelog

All notable changes to the data_cv project will be documented in this file.

## [2025-04-27]

### Added
- Google Scholar citations visualization:
  - New `print_scholar_citations()` function to display citation data as a bar chart
  - Integration with Google Scholar API to fetch citation counts for the last 5 years
  - Customizable styling options including bar color and text appearance
  - Error handling for network issues or invalid Scholar IDs
  - Automatic installation of required packages
- JSON-based CV/resume data management system:
  - New `cv_data.json` file that consolidates all CV/resume data in one file
  - Added tagging system for entries to identify document types and skills
  - Support for company/industry targeting of entries
  - Importance ranking for entries to prioritize the most significant ones
  - Structured skills organization by category with proficiency levels
- Python converter for JSON to CSV:
  - New `json_to_csv_converter.py` script to convert JSON data to CSV format
  - Support for filtering entries by document type, company, or tag
  - Automatic formatting of CSV files compatible with the render.r script
- AI-powered CV/resume generator:
  - New `ai_cv_generator.py` script using OpenAI API to analyze job postings
  - Automated scoring and selection of entries based on job relevance
  - Job-specific professional summary generation
  - Optional AI enhancement of entry descriptions
  - End-to-end pipeline from job posting to final document
- Sample job posting for testing the AI generator

## [2025-04-26]

### Added
- Custom image support for the ASIDE section:
  - New `--image` command-line flag to specify a custom image path
  - New `custom_image_path` parameter in `render_document()` function
  - Support for PNG and JPEG image formats
  - Configurable height and positioning for both custom images and network logo
  - CSS adjustments for optimal positioning of images relative to other content

## [2025-04-24]

### Added
- Plain text export option for LinkedIn Easy Apply and other job application systems
  - New `--plaintext` command-line flag
  - New `plain_text_too` parameter in `render_resume()` function
  - Generates a clean .txt file optimized for copying into web forms

## [2025-04-23]

### Added
- Command-line interface for `render_resume.r` with options for template, output filename, and HTML generation
- New CSV-based system for managing ASIDE section entries:
  - `aside_sections.csv` for defining expertise categories
  - [aside_entries.csv](cci:7://file:///Users/brendan/Projects/data_cv/my_resume_data/aside_entries.csv:0:0-0:0) for individual skills/expertise items
- CSS classes for skill indentation in the ASIDE section to replace `&nbsp;` entities
- Enhanced network logo visualization with customization options:
  - Configurable node size, colors, and force layout parameters
  - Interactive tooltips when hovering over nodes
  - Support for dragging nodes to reposition them
  - Better collision detection to prevent node overlap
- Dockerfile for containerized execution
  - Supports both podman and docker
  - Includes all required dependencies (R, Chrome, packages)
  - Facilitates consistent execution across different environments

### Changed
- Restructured `render_resume.r` as a flexible function with parameters
- Default resume output filename now includes the current date
- Updated README.md with comprehensive documentation
- Improved error handling and package dependency management

### Fixed
- Messy whitespace handling in ASIDE section by replacing `&nbsp;` with proper CSS