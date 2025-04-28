#!/usr/bin/env Rscript

# This script builds both the HTML and PDF versions of your CV or resume
# It supports command-line arguments for customization
# Usage: Rscript render.r --template my_cv.rmd --output MyCV --html --plaintext --image logo.png --data-dir my_cv_data

# Load required packages
suppressPackageStartupMessages({
  if(!require("optparse")) install.packages("optparse", repos = "http://cran.us.r-project.org")
  if(!require("crayon")) install.packages("crayon", repos = "http://cran.us.r-project.org")
  library(optparse)
  library(crayon)
})

# Clear the environment
rm(list = ls())

# Set up colorful output functions
header <- function(text) cat(bold(blue(paste0("\n=== ", text, " ===\n"))))
success <- function(text) cat(green(paste0("✓ ", text, "\n")))
info <- function(text) cat(cyan(paste0("ℹ ", text, "\n")))
warning_msg <- function(text) cat(yellow(paste0("⚠ ", text, "\n")))
error_msg <- function(text) cat(red(bold(paste0("✗ ", text, "\n"))))

# Create a function with parameters for customization
render_document <- function(
  # Template file (default: my_cv.rmd)
  template = "my_cv.rmd",
  # Output filename without extension
  output_filename = NULL,
  # Include HTML version? (default: FALSE - only generate PDF)
  html_too = FALSE,
  # Skip PDF generation? (default: FALSE - generate PDF)
  skip_pdf = FALSE,
  # Include plain text version for LinkedIn/job applications? (default: FALSE)
  plain_text_too = FALSE,
  # Custom image path (default: NULL - use network logo)
  custom_image_path = NULL,
  # Data directory (default: determined by template name)
  data_dir = NULL
) {
  # Check if required packages are installed
  required_packages <- c("rmarkdown", "fs", "pagedown", "htmltools", "knitr", "magrittr", "tidyr", "dplyr")
  for (pkg in required_packages) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
      cat(paste0("Installing package: ", pkg, "\n"))
      install.packages(pkg, repos = "http://cran.us.r-project.org")
    }
  }
  
  # Load the required packages
  suppressPackageStartupMessages({
    library(rmarkdown)
    library(fs)
    library(pagedown)
    library(htmltools)
    library(knitr)
    library(magrittr)
    library(tidyr)
    library(dplyr)
  })
  
  # Set global options to suppress warnings and messages
  options(warn = -1)  # Suppress warnings globally
  options(knitr.table.format = "html")
  
  # Create a function to specifically suppress the libxml warning
  withoutLibXmlWarning <- function(expr) {
    withCallingHandlers(
      expr,
      warning = function(w) {
        if (grepl("libxml", w$message)) {
          invokeRestart("muffleWarning")
        }
      }
    )
  }
  
  # Configure knitr to suppress warnings and messages in all chunks
  knitr::opts_chunk$set(
    warning = FALSE,
    message = FALSE,
    echo = FALSE,
    results = "asis"
  )
  
  # Source the CV printing functions
  # This file contains important functions: 
  # - create_CV_object: Creates a CV object from CSV data files
  # - generate_plain_text_cv: Creates a plain text version of the CV
  source(file.path(getwd(), "cv_printing_functions.r"))
  
  # The linter doesn't see these imported functions, so explicitly check they exist
  
  # Check if necessary functions are available after sourcing
  if (!exists("create_CV_object")) {
    error_msg("Function 'create_CV_object' not found in cv_printing_functions.r")
    stop("Missing required function 'create_CV_object'")
  }
  
  if (!exists("generate_plain_text_cv")) {
    error_msg("Function 'generate_plain_text_cv' not found in cv_printing_functions.r")
    stop("Missing required function 'generate_plain_text_cv'")
  }
  
  # Suppress readr messages about column specifications
  options(readr.show_col_types = FALSE)
  
  # Get absolute paths
  repo_dir <- getwd()
  root_dir <- file.path(repo_dir, "output")
  
  # Create output directory if it doesn't exist
  if (!dir.exists(root_dir)) {
    cat("Creating output directory at: ", root_dir, "\n")
    dir.create(root_dir, recursive = TRUE)
  }
  
  # Add trailing slash for file path construction
  root_dir <- paste0(root_dir, "/")
  
  # Determine document type based on template name
  is_cv <- grepl("cv", tolower(template))
  is_resume <- grepl("resume", tolower(template))
  doc_type <- if (is_cv) "CV" else if (is_resume) "resume" else "document"
  
  # Set default output filename if not provided
  if (is.null(output_filename)) {
    date_suffix <- format(Sys.Date(), "%Y-%m-%d")
    output_filename <- if (is_cv) {
      paste0("BrendanMiller_CV_", date_suffix)
    } else if (is_resume) {
      paste0("BrendanMiller_resume_", date_suffix)
    } else {
      paste0("BrendanMiller_document_", date_suffix)
    }
  } else {
    # If output_filename was provided (from Python), preserve it including its date
    # But ensure it has today's date if not already present
    today_date <- format(Sys.Date(), "%Y-%m-%d")
    if (!grepl(today_date, output_filename)) {
      output_filename <- paste0(output_filename, "_", today_date)
    }
    cat("Using provided output filename: ", output_filename, "\n")
  }
  
  # Determine data directory based on template if not provided
  if (is.null(data_dir)) {
    data_dir <- if (is_cv) {
      "my_cv_data"
    } else if (is_resume) {
      "my_resume_data"
    } else {
      # Default to CV data if unclear
      "my_cv_data"
    }
  }
  
  # Full paths for output files
  pdf_output <- file.path(root_dir, paste0(output_filename, ".pdf"))
  html_output <- file.path(root_dir, paste0(output_filename, ".html"))
  
  # Check if custom image path is valid
  if (!is.null(custom_image_path)) {
    if (!file.exists(custom_image_path)) {
      warning("Custom image file not found: ", custom_image_path)
      warning("Falling back to network logo")
      custom_image_path <- NULL
    } else {
      # Get file extension
      file_ext <- tolower(tools::file_ext(custom_image_path))
      if (!(file_ext %in% c("png", "jpg", "jpeg"))) {
        warning("Unsupported image format: ", file_ext)
        warning("Please use PNG or JPEG. Falling back to network logo")
        custom_image_path <- NULL
      } else {
        # Convert to absolute path if it's not already
        is_absolute_path <- function(path) {
          grepl("^/", path) # For Unix/Mac
        }
        
        if (!is_absolute_path(custom_image_path)) {
          custom_image_path <- normalizePath(custom_image_path)
        }
        cat("Custom image: ", custom_image_path, "\n")
      }
    }
  }
  
  # Handle path for data location
  # Check if data_dir is an absolute path or a relative path
  if (dir.exists(data_dir)) {
    # If the directory exists as provided, use it directly
    data_location <- normalizePath(file.path(data_dir, "/"))
  } else if (dir.exists(file.path(repo_dir, data_dir))) {
    # Try prepending the repo directory
    data_location <- normalizePath(file.path(repo_dir, data_dir, "/"))
  } else {
    # Log the issue and fall back to a default
    cat("WARNING: Data directory not found at", data_dir, "or", file.path(repo_dir, data_dir), "\n")
    cat("Current working directory:", getwd(), "\n")
    cat("Falling back to checking various possible paths...\n")
    
    # Try several possible path combinations
    possible_paths <- c(
      data_dir,
      file.path(repo_dir, data_dir),
      file.path(getwd(), data_dir),
      # Extra variants with and without trailing slash
      paste0(data_dir, "/"),
      file.path(repo_dir, paste0(data_dir, "/")),
      file.path(getwd(), paste0(data_dir, "/"))
    )
    
    # Check each path
    found_path <- FALSE
    for (path in possible_paths) {
      info(paste0("Checking path: ", path, "..."))  # Using cyan for checking paths
      if (dir.exists(path)) {
        data_location <- normalizePath(path)
        success(" FOUND!")  # Success in green bold
        found_path <- TRUE
        break
      }
      warning_msg(" not found")  # Not found in yellow
    }
    
    if (!found_path) {
      # As a last resort, use default path
      warning_msg("Could not find data directory, using default path")  # Warning in yellow
      data_location <- file.path(repo_dir, data_dir, "/")
    }
  }
  
  info(paste0("Using data location: ", data_location))
  
  # Create CV object with custom image if provided
  CV <- create_CV_object(
    data_location = data_location,
    pdf_mode = FALSE,
    custom_image_path = custom_image_path
  )
  
  header(paste0("Rendering ", doc_type, " from template: ", template))
  
  # Knit the HTML version
  info("Generating HTML version...")
  
  # Use the modified template in the templates directory if it exists
  template_name <- basename(template)
  modified_template_path <- file.path(repo_dir, "templates", template_name)
  
  if (file.exists(modified_template_path)) {
    template_path <- modified_template_path
    info(paste0("Using modified template at: ", template_path))
  } else {
    template_path <- file.path(root_dir, template)
    
    if (!file.exists(template_path)) {
      error_msg(paste0("Template file not found: ", template_path, "\nPlease check the template name and path."))
      stop()
    }
    
    info(paste0("Using template at: ", template_path))
  }
  
  # Save CV object to a temporary RDS file for use in the template
  cv_rds_path <- file.path(tempdir(), "cv_data.rds")
  saveRDS(CV, cv_rds_path)
  
  # Set environment variable for the template to use
  Sys.setenv(CV_DATA_PATH = cv_rds_path)
  
  # Set global option to suppress warnings
  oldw <- getOption("warn")
  options(warn = -1)
  
  # Render the HTML version of resume or CV
  if (html_too || skip_pdf) {
    info("Generating HTML version...")
    
    # Check for custom template in templates directory
    template_path <- file.path(repo_dir, "templates", template)
    if (file.exists(template_path)) {
      info(paste0("Using modified template at: ", template_path))
      template <- template_path
    } else {
      info(paste0("Using default template: ", template))
    }
    
    # We need to tell the template where to find data
    info(paste0("Passing data directory to template: ", data_location))
    
    # Render HTML version
    rmarkdown::render(
      input = template,
      params = list(
        pdf_mode = FALSE,
        data_dir = data_location,
        custom_image_path = custom_image_path
      ),
      output_file = html_output,
      quiet = TRUE
    )
  }
  
  # Restore original warning level
  options(warn = oldw)
  
  if (html_too) {
    success(paste0("HTML ", doc_type, " created: ", html_output))
  }
  
  # Try to find Chrome on the system
  chrome_path <- NULL
  
  # Check common locations for Chrome on different operating systems
  possible_paths <- c(
    # macOS paths
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chrome.app/Contents/MacOS/Chrome",
    # Linux paths
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    # Windows paths when running in WSL
    "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
    "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
  )
  
  for (path in possible_paths) {
    if (file.exists(path)) {
      chrome_path <- path
      success(paste0("Found Chrome at: ", chrome_path))
      break
    }
  }
  
  # Generate PDF using Chrome (unless skip_pdf is TRUE)
  if (!skip_pdf) {
    info("Generating PDF using Chrome...")
    
    if (!is.null(chrome_path)) {
      # Set Chrome path explicitly
      Sys.setenv(PAGEDOWN_CHROME = chrome_path)
    } else {
      # If Chrome wasn't found in any of the predefined paths
      warning_msg("Chrome not found in predefined paths. Checking PAGEDOWN_CHROME environment variable...")
      
      # Check if PAGEDOWN_CHROME environment variable is set
      env_chrome <- Sys.getenv("PAGEDOWN_CHROME")
      if (env_chrome != "") {
        chrome_path <- env_chrome
        info(paste0("Using Chrome from PAGEDOWN_CHROME environment variable: ", chrome_path))
      } else {
        # Try to find Chrome using system commands
        info("Attempting to locate Chrome using system commands...")
        
        # Try to find Chrome in Windows using WSL
        wsl_chrome_cmd <- tryCatch({
          system("wslpath -u 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'", intern = TRUE)
        }, error = function(e) NULL)
        
        if (!is.null(wsl_chrome_cmd) && length(wsl_chrome_cmd) > 0) {
          chrome_path <- wsl_chrome_cmd[1]
          info(paste0("Found Chrome using WSL path conversion: ", chrome_path))
        } else {
          warning_msg("Warning: Chrome not found. PDF generation may fail.")
          warning_msg("Consider setting the PAGEDOWN_CHROME environment variable to the path of your Chrome executable.")
        }
      }
    }
    
    # Set appropriate Chrome arguments for headless rendering
    # Use more robust arguments for WSL environment
    options(pagedown.chrome.args = c(
      "--headless=new",
      "--disable-gpu",
      "--no-sandbox",
      "--disable-dev-shm-usage"
    ))
    
    # Use pagedown for PDF generation
    tryCatch({
      pagedown::chrome_print(
        input = html_output, 
        output = pdf_output,
        browser = chrome_path
      )
      success(paste0("PDF ", doc_type, " created: ", pdf_output))
    }, error = function(e) {
      error_msg(paste0("Error generating PDF: ", e$message))
      info(paste0("HTML version is still available at: ", html_output))
      # Force HTML to be kept even if html_too is FALSE
      html_too <<- TRUE
    })
  } else {
    info("Skipping PDF generation as requested")
    # Force HTML to be kept since we're skipping PDF
    html_too <- TRUE
  }
  
  # Clean up temporary HTML file if not requested
  if (!html_too) {
    file.remove(html_output)
  }
  
  # Generate plain text version if requested
  if (plain_text_too) {
    # Generate plain text content
    plain_text_content <- generate_plain_text_cv(CV)
    
    # Define the output file path
    plain_text_output <- file.path(root_dir, paste0(output_filename, ".txt"))
    
    # Write the plain text content to a file
    info("Generating plain text version...")
    writeLines(plain_text_content, plain_text_output)
    success(paste0("Plain text ", doc_type, " created: ", plain_text_output))
    
    # Return paths to all generated files
    return(list(
      pdf = pdf_output, 
      html = if(html_too) html_output else NULL,
      plain_text = plain_text_output
    ))
  } else {
    # Return the paths to the generated files without plain text
    return(list(pdf = pdf_output, html = if(html_too) html_output else NULL))
  }
}

# CLI execution support
if (!interactive()) {
  # Define command-line arguments
  option_list <- list(
    make_option(c("-t", "--template"), type="character", default="my_cv.rmd",
                help="Template file (e.g., my_cv.rmd or my_resume.rmd) [default: %default]"),
    make_option(c("-o", "--output"), type="character", default=NULL,
                help="Output filename without extension [default: BrendanMiller<DocType>_YYYY-MM-DD]"),
    make_option(c("--html"), action="store_true", default=FALSE,
                help="Generate HTML version in addition to PDF [default: %default]"),
    make_option(c("--skip-pdf"), action="store_true", default=FALSE,
                help="Skip PDF generation and only create HTML [default: %default]"),
    make_option(c("--plaintext"), action="store_true", default=FALSE,
                help="Generate plain text version for LinkedIn/job applications [default: %default]"),
    make_option(c("-i", "--image"), type="character", default=NULL,
                help="Path to custom image (PNG or JPEG) to use instead of network logo [default: none]"),
    make_option(c("-d", "--data-dir"), type="character", default=NULL,
                help="Data directory to use (e.g., my_cv_data or my_resume_data) [default: determined by template]")
  )
  
  # Parse command-line arguments
  opt_parser <- OptionParser(option_list=option_list)
  opts <- parse_args(opt_parser)
  
  # Run with provided arguments
  render_document(
    template = opts$template,
    output_filename = opts$output,
    html_too = opts$html,
    skip_pdf = opts$`skip-pdf`,
    plain_text_too = opts$plaintext,
    custom_image_path = opts$image,
    data_dir = opts$`data-dir`
  )
} else {
  # If being sourced in an interactive session, don't automatically run
  cat("Function 'render_document()' is available for use.\n")
  cat("Example usage:\n")
  cat("  # Generate CV\n")
  cat("  render_document(template = 'my_cv.rmd', output_filename = 'BrendanMiller_CompanyX', html_too = TRUE)\n\n")
  cat("  # Generate resume\n")
  cat("  render_document(template = 'my_resume.rmd', output_filename = 'BrendanMiller_CompanyX', html_too = TRUE)\n\n")
  cat("  # Generate CV with custom image\n")
  cat("  render_document(template = 'my_cv.rmd', custom_image_path = '/path/to/logo.png')\n\n")
}
