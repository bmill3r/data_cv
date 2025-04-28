#!/usr/bin/env Rscript

# This script builds both the HTML and PDF versions of your CV
# It supports command-line arguments for customization

# Load required packages
suppressPackageStartupMessages({
  if(!require("optparse")) install.packages("optparse", repos = "http://cran.us.r-project.org")
  library(optparse)
})

# Clear the environment
rm(list = ls())

# Create a function with parameters for customization
render_cv <- function(
  # Template file (default: my_cv.rmd)
  template = "my_cv.rmd",
  # Output filename without extension (default: BrendanMillerCV_YYYY-MM-DD)
  output_filename = paste0("BrendanMillerCV_", format(Sys.Date(), "%Y-%m-%d")),
  # Include HTML version? (default: FALSE - only generate PDF)
  html_too = FALSE,
  # Include plain text version for LinkedIn/job applications? (default: FALSE)
  plain_text_too = FALSE,
  # Custom image path (default: NULL - use network logo)
  custom_image_path = NULL
) {
  # Check if required packages are installed
  required_packages <- c("rmarkdown", "fs", "pagedown", "htmltools", "knitr")
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
  })
  
  # Source the CV printing functions
  source(file.path(getwd(), "cv_printing_functions.r"))
  
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
  
  # CV template
  cv_template <- template
  
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
        cat("Using custom image: ", custom_image_path, "\n")
      }
    }
  }
  
  # Create CV object with custom image if provided
  CV <- create_CV_object(
    data_location = file.path(repo_dir, "my_cv_data/"),
    pdf_mode = FALSE,
    custom_image_path = custom_image_path
  )
  
  cat(paste0("Rendering CV from template: ", cv_template, "\n"))
  
  # Knit the HTML version
  cat("Generating HTML version...\n")
  template_path <- file.path(root_dir, cv_template)
  
  if (!file.exists(template_path)) {
    stop("Template file not found: ", template_path, "\nPlease check the template name and path.")
  }
  
  cat("Using template at: ", template_path, "\n")
  
  # Save CV object to a temporary RDS file for use in the template
  cv_rds_path <- file.path(tempdir(), "cv_data.rds")
  saveRDS(CV, cv_rds_path)
  
  # Set environment variable for the template to use
  Sys.setenv(CV_DATA_PATH = cv_rds_path)
  
  # Render HTML version
  rmarkdown::render(template_path,
                    params = list(pdf_mode = FALSE),
                    output_file = html_output)
  
  if (html_too) {
    cat(paste0("HTML CV created: ", html_output, "\n"))
  }
  
  # Try to find Chrome on the system
  chrome_path <- NULL
  
  # Check common locations for Chrome on macOS
  possible_paths <- c(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chrome.app/Contents/MacOS/Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser"
  )
  
  for (path in possible_paths) {
    if (file.exists(path)) {
      chrome_path <- path
      cat("Found Chrome at: ", chrome_path, "\n")
      break
    }
  }
  
  # Generate PDF using Chrome
  cat("Generating PDF using Chrome...\n")
  
  if (!is.null(chrome_path)) {
    # Set Chrome path explicitly
    Sys.setenv(PAGEDOWN_CHROME = chrome_path)
  }
  
  # Set appropriate Chrome arguments for headless rendering
  options(pagedown.chrome.args = c("--headless", "--disable-gpu"))
  
  # Use pagedown for PDF generation
  pagedown::chrome_print(
    input = html_output, 
    output = pdf_output,
    browser = chrome_path
  )
  
  cat(paste0("PDF CV created: ", pdf_output, "\n"))
  
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
    cat("Generating plain text version for LinkedIn/job applications...\n")
    writeLines(plain_text_content, plain_text_output)
    cat(paste0("Plain text CV created: ", plain_text_output, "\n"))
    
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
                help="CV template file [default: %default]"),
    make_option(c("-o", "--output"), type="character", 
                default=paste0("BrendanMillerCV_", format(Sys.Date(), "%Y-%m-%d")),
                help="Output filename without extension [default: %default]"),
    make_option(c("--html"), action="store_true", default=FALSE,
                help="Generate HTML version in addition to PDF [default: %default]"),
    make_option(c("--plaintext"), action="store_true", default=FALSE,
                help="Generate plain text version for LinkedIn/job applications [default: %default]"),
    make_option(c("-i", "--image"), type="character", default=NULL,
                help="Path to custom image (PNG or JPEG) to use instead of network logo [default: none]")
  )
  
  # Parse command-line arguments
  opt_parser <- OptionParser(option_list=option_list)
  opts <- parse_args(opt_parser)
  
  # Run with provided arguments
  render_cv(
    template = opts$template,
    output_filename = opts$output,
    html_too = opts$html,
    plain_text_too = opts$plaintext,
    custom_image_path = opts$image
  )
} else {
  # If being sourced in an interactive session, don't automatically run
  cat("Function 'render_cv()' is available for use.\n")
  cat("Example usage:\n")
  cat("  render_cv(template = 'my_cv.rmd', output_filename = 'BrendanMiller_CompanyX', html_too = TRUE, plain_text_too = TRUE, custom_image_path = '/path/to/logo.png')\n\n")
}

