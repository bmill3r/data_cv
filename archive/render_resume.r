# This script builds both the HTML and PDF versions of your CV

# If you wanted to speed up rendering for googlesheets driven CVs you could use
# this script to cache a version of the CV_Printer class with data already
# loaded and load the cached version in the .Rmd instead of re-fetching it twice
# for the HTML and PDF rendering. This exercise is left to the reader.

## source in order to load the`"build_network_logo_custom()` I made
# source("cv_printing_functions.r")

## location of the `cv.rmd`
## set the working directory to this repo.
root_dir <- paste0(getwd(), "/output/")

resume_template <- "my_resume_20250117.rmd"

# Knit the HTML version
# rmarkdown::render(paste0(root_dir, resume_template),
#                   params = list(pdf_mode = FALSE),
#                   output_file = paste0(root_dir, "BrendanMillerResume.html"))

# Knit the PDF version to temporary html location
tmp_html_cv_loc <- fs::file_temp(ext = ".html")
rmarkdown::render(paste0(root_dir, resume_template),
                  params = list(pdf_mode = TRUE),
                  output_file = tmp_html_cv_loc)

# Convert to PDF using Pagedown
pagedown::chrome_print(input = tmp_html_cv_loc,
                       output = paste0(root_dir, "BrendanMillerResume_20250125.pdf"))




