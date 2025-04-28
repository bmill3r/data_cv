# Suppress warnings about package versions
options(warn = -1)

# Suppress package startup messages
suppressPackageStartupMessages({
  if (file.exists(".RData")) {
    # Avoid loading workspace data
    rm(list = ls())
  }
})

# Create a function to suppress all output
quiet <- function(x) { 
  suppressWarnings(suppressMessages(invisible(x)))
}

# Make sure this file is only used for this project
.First <- function() {
  cat("R startup profile loaded with warning suppression enabled\n")
}
