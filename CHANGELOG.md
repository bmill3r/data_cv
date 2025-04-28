# Changelog

All notable changes to the data_cv project will be documented in this file.

## [2025-04-28] - Updated

### Added
- Enhanced filtering capabilities in JSON to CSV converter:
  - Added support for multiple tags with comma-separated values: `--filter-tag bioinformatics,machine_learning`
  - Added support for multiple companies with comma-separated values: `--filter-company biotech,academic`
  - Added `--filter-logic` parameter to choose between AND/OR operations
  - With `and` logic (default), entries must match ALL specified filters
  - With `or` logic, entries must match ANY specified filter
  - Updated documentation with comprehensive examples
- Added temperature parameter to AI CV Generator:
  - Control AI creativity with `--temperature` parameter (0.0-1.0)
  - Lower values (0.0-0.3) for more deterministic outputs
  - Higher values (0.8-1.0) for more creative outputs
  - Default value of 0.7 for balanced generation
- Added colorful terminal output:
  - Integrated `rich` library for Python scripts
  - Added `crayon` for colorful R script output
  - Created custom formatting functions for different message types
  - Added progress indicators and status messages

### Fixed
- Improved CSV reading in R scripts:
  - Smart detection for header/explanation rows in text_blocks.csv
  - Robust column name handling with fallbacks
  - Silent data loading with no debug output in terminal/HTML
- Enhanced JSON parsing with robust repair logic:
  - Added `demjson3` for permissive JSON parsing
  - Multiple repair strategies for malformed AI output
  - Better error context for troubleshooting
- Fixed relative path handling:
  - Ensured all scripts use relative paths consistently
  - Improved directory detection logic

## [2025-04-27] - Updated

### Added
- Added Claude API support to the AI CV Generator:
  - Support for both OpenAI and Anthropic Claude APIs
  - New `--ai-service` parameter to choose between `openai` and `claude`
  - Added `--use-prompt-only` option for efficient one-shot CV tailoring
  - Created comprehensive prompts for both APIs
  - Environment variable handling via .env file
  - Updated package requirements (openai, anthropic, python-dotenv)
  - Improved error handling and API fallback mechanisms

## [2025-04-25]

### Enhanced
- Improved CV database editor (cv_database_editor.py):
  - Added functions to edit skill categories and text blocks
  - Enhanced section display with numbered, user-friendly formatting
  - Added explicit options for creating new sections in both add and edit functions
  - Improved user interface with clear prompts and better error handling

### Added
- Enhanced contact information handling in CSV/JSON converters:
  - Improved parsing of contact_info.csv with multiple format support
  - Preserved icon information during round-trip conversions
  - Added support for duplicate location types (multiple websites)
  - Structured JSON storage of contact data with values and icons
  - Fixed missing entries in contact information

### Changed
- Tested multiple approaches for clean page breaks in the aside section:
  - Implemented CSS-based solutions with `page-break-inside: avoid` and `break-inside: avoid`
  - Tried JavaScript-based PagedJS handlers to control category pagination
  - Experimented with structural approaches including tables and explicit page containers
  - Adjusted spacing and formatting in the skill categories for better presentation
  - Added proper error handling to prevent crashes when sections are missing

### Added
- Google Scholar citations visualization:
  - New `print_scholar_citations()` function to display citation data as a bar chart
  - Integration with Google Scholar API to fetch citation counts for the last 5 years
  - Customizable styling options including bar color and text appearance
  - Error handling for network issues or invalid Scholar IDs
  - Automatic installation of required packages
- JSON-based CV/resume data management system:
  - New `cv_database.json` file that consolidates all CV/resume data in one file
  - Added tagging system for entries to identify document types and skills
  - Support for company/industry targeting of entries
  - Importance ranking for entries to prioritize the most significant ones
  - Structured skills organization by category with proficiency levels
- CSV to JSON converter:
  - New `csv_to_json_converter.py` script to convert CSV data to JSON format
  - Robust handling of multiple CSV encodings and explanation rows
  - Support for complex data structures including nested descriptions
  - Debug output for troubleshooting data conversion issues
  - Proper parsing of skills/aside data for structured JSON storage
- CV database editor:
  - New `cv_database_editor.py` script for interactive JSON editing
  - Support for adding, editing, and removing entries without manual JSON editing
  - Guided prompts for all required fields with validation
  - Skill category and entry management
  - JSON schema enforcement for data integrity
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