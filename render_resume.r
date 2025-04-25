#!/usr/bin/env Rscript

# This script builds both the HTML and PDF versions of your resume
# It requires the following packages: rmarkdown, webshot, fs, optparse

# Load required packages
suppressPackageStartupMessages({
  if(!require("optparse")) install.packages("optparse", repos = "http://cran.us.r-project.org")
  library(optparse)
})

# Clear the environment
rm(list = ls())

# Create a function with parameters for customization
render_resume <- function(
  # Template file (default: my_resume.rmd)
  template = "my_resume.rmd",
  # Output filename without extension (default: BrendanMillerResume_YYYY-MM-DD)
  output_filename = paste0("BrendanMillerResume_", format(Sys.Date(), "%Y-%m-%d")),
  # Include HTML version? (default: FALSE - only generate PDF)
  html_too = FALSE,
  # Include plain text version for LinkedIn/job applications? (default: FALSE)
  plain_text_too = FALSE
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
  
  # Resume template
  resume_template <- template
  
  # Full paths for output files
  pdf_output <- file.path(root_dir, paste0(output_filename, ".pdf"))
  html_output <- file.path(root_dir, paste0(output_filename, ".html"))
  
  cat(paste0("Rendering resume from template: ", resume_template, "\n"))
  
  # Knit the HTML version
  cat("Generating HTML version...\n")
  template_path <- file.path(root_dir, resume_template)
  
  if (!file.exists(template_path)) {
    stop("Template file not found: ", template_path, "\nPlease check the template name and path.")
  }
  
  cat("Using template at: ", template_path, "\n")
  rmarkdown::render(template_path,
                    params = list(pdf_mode = FALSE),
                    output_file = html_output)
  
  if (html_too) {
    cat(paste0("HTML resume created: ", html_output, "\n"))
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
  
  cat(paste0("PDF resume created: ", pdf_output, "\n"))
  
  # Clean up temporary HTML file if not requested
  if (!html_too) {
    file.remove(html_output)
  }
  
  # Generate plain text version if requested
  if (plain_text_too) {
    # Source the CV printing functions to get access to generate_plain_text_cv
    source(file.path(repo_dir, "cv_printing_functions.r"))
    
    # Create a CV object
    CV <- create_CV_object(
      data_location = file.path(repo_dir, "my_resume_data/"),
      pdf_mode = FALSE
    )
    
    # Generate plain text content
    plain_text_content <- generate_plain_text_cv(CV)
    
    # Define the output file path
    plain_text_output <- file.path(root_dir, paste0(output_filename, ".txt"))
    
    # Write the plain text content to a file
    cat("Generating plain text version for LinkedIn/job applications...\n")
    writeLines(plain_text_content, plain_text_output)
    cat(paste0("Plain text resume created: ", plain_text_output, "\n"))
    
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
    make_option(c("-t", "--template"), type="character", default="my_resume.rmd",
                help="Resume template file [default: %default]"),
    make_option(c("-o", "--output"), type="character", 
                default=paste0("BrendanMillerResume_", format(Sys.Date(), "%Y-%m-%d")),
                help="Output filename without extension [default: %default]"),
    make_option(c("--html"), action="store_true", default=FALSE,
                help="Generate HTML version in addition to PDF [default: %default]"),
    make_option(c("--plaintext"), action="store_true", default=FALSE,
                help="Generate plain text version for LinkedIn/job applications [default: %default]")
  )
  
  # Parse command-line arguments
  opt_parser <- OptionParser(option_list=option_list)
  opts <- parse_args(opt_parser)
  
  # Run with provided arguments
  render_resume(
    template = opts$template,
    output_filename = opts$output,
    html_too = opts$html,
    plain_text_too = opts$plaintext
  )
} else {
  # If being sourced in an interactive session, don't automatically run
  cat("Function 'render_resume()' is available for use.\n")
  cat("Example usage:\n")
  cat("  render_resume(template = 'my_resume.rmd', output_filename = 'BrendanMiller_CompanyX', html_too = TRUE, plain_text_too = TRUE)\n\n")
}
