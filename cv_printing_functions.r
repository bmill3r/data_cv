#' Create a CV_Printer object.
#'
#' @param data_location Path of the spreadsheets holding all your data. This can be
#'   either a URL to a google sheet with multiple sheets containing the four
#'   data types or a path to a folder containing four `.csv`s with the neccesary
#'   data.
#' @param source_location Where is the code to build your CV hosted?
#' @param pdf_mode Is the output being rendered into a pdf? Aka do links need
#'   to be stripped?
#' @param sheet_is_publicly_readable If you're using google sheets for data,
#'   is the sheet publicly available? (Makes authorization easier.)
#' @return A new `CV_Printer` object.
create_CV_object <-  function(data_location,
                              pdf_mode = FALSE,
                              sheet_is_publicly_readable = TRUE,
                              custom_image_path = NULL) {

  # Set custom image path in CV object

  cv <- list(
    pdf_mode = pdf_mode,
    links = c(),
    custom_image_path = custom_image_path
  )



  is_google_sheets_location <- stringr::str_detect(data_location, "docs\\.google\\.com")

  if(is_google_sheets_location){
    if(sheet_is_publicly_readable){
      # This tells google sheets to not try and authenticate. Note that this will only
      # work if your sheet has sharing set to "anyone with link can view"
      googlesheets4::sheets_deauth()
    } else {
      # My info is in a public sheet so there's no need to do authentication but if you want
      # to use a private sheet, then this is the way you need to do it.
      # designate project-specific cache so we can render Rmd without problems
      options(gargle_oauth_cache = ".secrets")
    }

    read_gsheet <- function(sheet_id){
      googlesheets4::read_sheet(data_location, sheet = sheet_id, skip = 1, col_types = "c")
    }
    cv$entries_data  <- read_gsheet(sheet_id = "entries")
    cv$skills        <- read_gsheet(sheet_id = "language_skills")
    cv$text_blocks   <- read_gsheet(sheet_id = "text_blocks")
    cv$contact_info  <- read_gsheet(sheet_id = "contact_info")
    
    # Try to read the new aside entries files if they exist
    tryCatch({
      cv$aside_sections <- read_gsheet(sheet_id = "aside_sections")
      cv$aside_entries <- read_gsheet(sheet_id = "aside_entries")
    }, error = function(e) {
      message("No aside entries found in Google Sheets. Using default ASIDE section.")
    })
    
  } else {
    # Want to go old-school with csvs?
    # Ensure path has proper trailing separator
    if (!endsWith(data_location, "/") && !endsWith(data_location, "\\")) {
      data_location <- paste0(data_location, "/")
    }
    
    # Log the data files being accessed
    cat("Reading data files from directory:\n  ", data_location, "\n")
    
    entries_path <- paste0(data_location, "entries.csv")
    skills_path <- paste0(data_location, "language_skills.csv")
    text_blocks_path <- paste0(data_location, "text_blocks.csv")
    contact_info_path <- paste0(data_location, "contact_info.csv")
    
    # Check if files exist and print diagnostics
    cat("Checking CSV files:\n")
    cat("  entries.csv:", if(file.exists(entries_path)) "Found" else "NOT FOUND!", "\n")
    cat("  language_skills.csv:", if(file.exists(skills_path)) "Found" else "NOT FOUND!", "\n")
    cat("  text_blocks.csv:", if(file.exists(text_blocks_path)) "Found" else "NOT FOUND!", "\n")
    cat("  contact_info.csv:", if(file.exists(contact_info_path)) "Found" else "NOT FOUND!", "\n")
    
    # Create an empty CV object as backup in case of errors
    empty_cv <- list(entries_data = data.frame(), skills = data.frame(), 
                     text_blocks = data.frame(loc = character(), text = character()), 
                     contact_info = data.frame())
    
    # Try reading CSV files with robust error handling
    # DO NOT SKIP HEADER ROW - the first row contains the column names
    csv_read_opts <- readr::read_csv_chunked
    
    cv$entries_data <- tryCatch({
      # Skip explanation row for entries.csv - it has an explanation row
      readr::read_csv(entries_path, skip = 1, col_types = readr::cols(), progress = FALSE, show_col_types = FALSE)
    }, error = function(e) {
      cat("WARNING: Error reading entries.csv:", e$message, "\n")
      empty_cv$entries_data
    })
    
    cv$skills <- tryCatch({
      # Skip explanation row for skills.csv - it has an explanation row
      readr::read_csv(skills_path, skip = 1, col_types = readr::cols(), progress = FALSE, show_col_types = FALSE)
    }, error = function(e) {
      cat("WARNING: Error reading language_skills.csv:", e$message, "\n")
      empty_cv$skills
    })
    
    # For text_blocks.csv, intelligently determine format without verbose output
    if (file.exists(text_blocks_path)) {
      # Read first line of the file to check header format
      tb_lines <- readLines(text_blocks_path, n=1)
      
      # Direct inspection to determine if the file has header in first row
      first_line_is_header <- FALSE
      if (length(tb_lines) > 0) {
        first_line_is_header <- grepl("^loc,text", tb_lines[1]) || grepl("^id,content", tb_lines[1])
      }
      
      # Read CSV based on detected format (quietly)
      cv$text_blocks <- tryCatch({
        if (first_line_is_header) {
          # First line is header - don't skip
          readr::read_csv(text_blocks_path, skip = 0, col_types = readr::cols(
            loc = readr::col_character(),
            text = readr::col_character()
          ), progress = FALSE, show_col_types = FALSE)
        } else {
          # First line is not header - skip it
          readr::read_csv(text_blocks_path, skip = 1, col_types = readr::cols(
            loc = readr::col_character(),
            text = readr::col_character()
          ), progress = FALSE, show_col_types = FALSE)
        }
      }, error = function(e) {
        # Return an empty dataframe with proper column names
        empty_cv$text_blocks
      })
    } else {
      cv$text_blocks <- empty_cv$text_blocks
    }
    
    cv$contact_info <- tryCatch({
      # Skip explanation row for contact_info.csv - it has an explanation row
      readr::read_csv(contact_info_path, skip = 1, col_types = readr::cols(), progress = FALSE, show_col_types = FALSE)
    }, error = function(e) {
      cat("WARNING: Error reading contact_info.csv:", e$message, "\n")
      empty_cv$contact_info
    })
    
    # Silently confirm that text_blocks data was read correctly
    
    # Try to read the new aside entries files if they exist
    aside_sections_path <- paste0(data_location, "aside_sections.csv")
    aside_entries_path <- paste0(data_location, "aside_entries.csv")
    
    if (file.exists(aside_sections_path) && file.exists(aside_entries_path)) {
      cv$aside_sections <- readr::read_csv(aside_sections_path)
      cv$aside_entries <- readr::read_csv(aside_entries_path)
    } else {
      message("One or both aside entries files not found. Using default ASIDE section.")
    }
  }

  extract_year <- function(dates){
    date_year <- stringr::str_extract(dates, "(20|19)[0-9]{2}")
    date_year[is.na(date_year)] <- lubridate::year(lubridate::ymd(Sys.Date())) + 10

    date_year
  }

  parse_dates <- function(dates){

    date_month <- stringr::str_extract(dates, "(\\w+|\\d+)(?=(\\s|\\/|-)(20|19)[0-9]{2})")
    date_month[is.na(date_month)] <- "1"

    paste("1", date_month, extract_year(dates), sep = "-") %>%
      lubridate::dmy()
  }

  # Clean up entries dataframe to format we need it for printing
  cv$entries_data %<>%
    tidyr::unite(
      tidyr::starts_with('description'),
      col = "description_bullets",
      sep = "\n- ",
      na.rm = TRUE
    ) %>%
    dplyr::mutate(
      description_bullets = ifelse(description_bullets != "", paste0("- ", description_bullets), ""),
      start = ifelse(start == "NULL", NA, start),
      end = ifelse(end == "NULL", NA, end),
      start_year = extract_year(start),
      end_year = extract_year(end),
      no_start = is.na(start),
      has_start = !no_start,
      no_end = is.na(end),
      has_end = !no_end,
      timeline = dplyr::case_when(
        no_start  & no_end  ~ "N/A",
        no_start  & has_end ~ as.character(end),
        has_start & no_end  ~ paste("Current", "-", start),
        TRUE                ~ paste(end, "-", start)
      )
    ) %>%
    dplyr::arrange(desc(parse_dates(end))) %>%
    dplyr::mutate_all(~ ifelse(is.na(.), 'N/A', .))

  cv
}


# Remove links from a text block and add to internal list
sanitize_links <- function(cv, text){
  if(cv$pdf_mode){
    link_titles <- stringr::str_extract_all(text, '(?<=\\[).+?(?=\\])')[[1]]
    link_destinations <- stringr::str_extract_all(text, '(?<=\\().+?(?=\\))')[[1]]

    n_links <- length(cv$links)
    n_new_links <- length(link_titles)

    if(n_new_links > 0){
      # add links to links array
      cv$links <- c(cv$links, link_destinations)

      # Build map of link destination to superscript
      link_superscript_mappings <- purrr::set_names(
        paste0("<sup>", (1:n_new_links) + n_links, "</sup>"),
        paste0("(", link_destinations, ")")
      )

      # Replace the link destination and remove square brackets for title
      # text <- text %>%
      #   stringr::str_replace_all(stringr::fixed(link_superscript_mappings)) %>%
      #   stringr::str_replace_all('\\[(.+?)\\]', "\\1")
    }
  }

  list(cv = cv, text = text)
}


#' @description Take a position data frame and the section id desired and prints the section to markdown.
#' @param section_id ID of the entries section to be printed as encoded by the `section` column of the `entries` table
print_section <- function(cv, section_id, glue_template = "default"){

  if(glue_template == "default"){
    glue_template <- "
### {title}

{loc}

{institution}

{timeline}

{description_bullets}
\n\n"
  }

  section_data <- dplyr::filter(cv$entries_data, section == section_id)

  # Take entire entries data frame and removes the links in descending order
  # so links for the same position are right next to each other in number.
  for(i in 1:nrow(section_data)){
    for(col in c('title', 'description_bullets')){
      strip_res <- sanitize_links(cv, section_data[i, col])
      section_data[i, col] <- strip_res$text
      cv <- strip_res$cv
    }
  }

  print(glue::glue_data(section_data, glue_template))

  invisible(strip_res$cv)
}



#' @description Prints out text block identified by a given label.
#' @param label ID of the text block to print as encoded in `label` column of `text_blocks` table.
# Original version simplified with error handling but no debug output
print_text_block <- function(cv, label){
  # First check if the text_blocks dataframe is valid
  if (is.null(cv$text_blocks) || nrow(cv$text_blocks) == 0) {
    return(invisible(cv))
  }
  
  # If the column names are as expected (loc, text)
  if ("loc" %in% names(cv$text_blocks) && "text" %in% names(cv$text_blocks)) {
    # Get the text block with the given label
    text_block_df <- cv$text_blocks[cv$text_blocks$loc == label, ]
    
    # If found, get the text and display it
    if (nrow(text_block_df) > 0) {
      text_content <- text_block_df$text[1]
      strip_res <- sanitize_links(cv, text_content)
      cat(strip_res$text)
      return(invisible(strip_res$cv))
    }
  }
  
  # If we're here, either the columns aren't as expected or the label wasn't found
  # Try using dplyr's filter as a fallback (original method)
  tryCatch({
    text_block <- dplyr::filter(cv$text_blocks, loc == label) %>%
      dplyr::pull(text)
    
    strip_res <- sanitize_links(cv, text_block)
    cat(strip_res$text)
    return(invisible(strip_res$cv))
  }, error = function(e) {
    # If there's an error, try one more approach as a last resort
    if (ncol(cv$text_blocks) >= 2) {
      # Assume first column is ID, second is content
      id_col <- names(cv$text_blocks)[1]
      content_col <- names(cv$text_blocks)[2]
      
      # Find row with matching label
      matching_rows <- which(cv$text_blocks[[id_col]] == label)
      
      if (length(matching_rows) > 0) {
        text_content <- cv$text_blocks[[content_col]][matching_rows[1]]
        strip_res <- sanitize_links(cv, text_content)
        cat(strip_res$text)
        return(invisible(strip_res$cv))
      }
    }
    
    # If all approaches fail, return silently
    return(invisible(cv))
  })
  
  # Should not reach here, but just in case
  invisible(cv)
}



#' @description Generate a plain text version of the CV for easy copying into job applications
#' @param cv CV object containing all the data
#' @return A character string containing the formatted plain text CV
generate_plain_text_cv <- function(cv) {
  # Initialize empty string to hold the plain text CV
  plain_text <- ""
  
  # Basic function to remove HTML tags but keep markdown brackets and URLs
  clean_text <- function(text) {
    # Skip empty text or N/A values
    if (is.na(text) || text == "" || text == "N/A") {
      return("")
    }
    
    # Replace <br /> with spaces
    text <- gsub("<br\\s*/>", " ", text)
    text <- gsub("<br>", " ", text)
    
    # Remove HTML tags but keep markdown brackets and parentheses
    text <- gsub("<[^>]+>", "", text)
    
    # Remove specific HTML elements that might have been missed
    text <- gsub("<span[^>]*>.*?</span>", "", text)
    text <- gsub("<i[^>]*>.*?</i>", "", text)
    text <- gsub("<a[^>]*>.*?</a>", "", text)
    text <- gsub("<u>.*?</u>", "", text)
    
    # Replace HTML entities with their plaintext equivalent
    text <- gsub("&nbsp;", " ", text)
    text <- gsub("&amp;", "&", text)
    text <- gsub("&lt;", "<", text)
    text <- gsub("&gt;", ">", text)
    text <- gsub("&quot;", "\"", text)
    text <- gsub("&apos;", "'", text)
    
    # Remove markdown formatting characters
    text <- gsub("\\*", "", text)       # Bold/Italic
    text <- gsub("_", "", text)         # Underline/Italic
    text <- gsub("`", "", text)         # Code
    text <- gsub("\\|", " ", text)       # Table separators
    
    # Clean up pipe separators that might be used for styling
    text <- gsub("\\s*\\|\\s*", " - ", text)
    
    # Clean up extra whitespace
    text <- gsub("\\s+", " ", text)     # Multiple spaces to single space
    text <- trimws(text)               # Trim whitespace at start/end
    
    # Remove any remaining HTML entities
    text <- gsub("&[^;]+;", "", text)
    
    return(text)
  }
  
  # CONTACT INFO SECTION
  plain_text <- paste0(plain_text, "CONTACT INFORMATION\n")
  plain_text <- paste0(plain_text, "====================\n\n")
  
  # Use column names from your actual CSV structure
  for (i in 1:nrow(cv$contact_info)) {
    contact_field <- cv$contact_info[[1]][i]  # "Id of contact section"
    contact_value <- clean_text(cv$contact_info[[3]][i])  # "The actual value written for the contact entry"
    plain_text <- paste0(
      plain_text,
      contact_field, ": ", 
      contact_value, "\n"
    )
  }
  plain_text <- paste0(plain_text, "\n\n")
  
  # INTRO TEXT BLOCK
  intro_text <- dplyr::filter(cv$text_blocks, loc == "intro") %>% dplyr::pull(text)
  plain_text <- paste0(plain_text, "PROFILE\n")
  plain_text <- paste0(plain_text, "=======\n\n")
  # Clean text of HTML and markdown formatting
  intro_text <- clean_text(intro_text)
  plain_text <- paste0(plain_text, intro_text, "\n\n")
  
  # CURRENT POSITION SECTION
  plain_text <- paste0(plain_text, "CURRENT POSITION\n")
  plain_text <- paste0(plain_text, "================\n\n")
  
  current_position <- dplyr::filter(cv$entries_data, section == "current_position_company_1")
  
  for (i in 1:nrow(current_position)) {
    plain_text <- paste0(plain_text, clean_text(current_position$title[i]), "\n")
    plain_text <- paste0(plain_text, clean_text(current_position$loc[i]), "\n")
    # Skip N/A values
    if (current_position$institution[i] != "N/A") {
      plain_text <- paste0(plain_text, clean_text(current_position$institution[i]), "\n")
    }
    plain_text <- paste0(plain_text, clean_text(current_position$timeline[i]), "\n\n")
    
    # Process description bullets
    if (current_position$description_bullets[i] != "") {
      # Remove the bullet point markers and format each point on its own line
      bullets <- gsub("^- ", "", strsplit(current_position$description_bullets[i], "\n- ")[[1]])
      for (bullet in bullets) {
        # Clean text of HTML and markdown formatting
        bullet <- clean_text(bullet)
        plain_text <- paste0(plain_text, "• ", bullet, "\n")
      }
      plain_text <- paste0(plain_text, "\n")
    }
  }
  
  # EDUCATION SECTION
  plain_text <- paste0(plain_text, "EDUCATION\n")
  plain_text <- paste0(plain_text, "=========\n\n")
  
  education <- dplyr::filter(cv$entries_data, section == "education")
  
  for (i in 1:nrow(education)) {
    plain_text <- paste0(plain_text, clean_text(education$title[i]), "\n")
    plain_text <- paste0(plain_text, clean_text(education$loc[i]), "\n")
    # Skip N/A values
    if (education$institution[i] != "N/A") {
      plain_text <- paste0(plain_text, clean_text(education$institution[i]), "\n")
    }
    plain_text <- paste0(plain_text, clean_text(education$timeline[i]), "\n\n")
    
    # Process description bullets
    if (education$description_bullets[i] != "") {
      # Remove the bullet point markers and format each point on its own line
      bullets <- gsub("^- ", "", strsplit(education$description_bullets[i], "\n- ")[[1]])
      for (bullet in bullets) {
        # Clean text of HTML and markdown formatting
        bullet <- clean_text(bullet)
        plain_text <- paste0(plain_text, "• ", bullet, "\n")
      }
      plain_text <- paste0(plain_text, "\n")
    }
  }
  
  # ADDITIONAL RESEARCH SECTION
  plain_text <- paste0(plain_text, "ADDITIONAL RESEARCH\n")
  plain_text <- paste0(plain_text, "===================\n\n")
  
  research <- dplyr::filter(cv$entries_data, section == "additional_research")
  
  for (i in 1:nrow(research)) {
    plain_text <- paste0(plain_text, clean_text(research$title[i]), "\n")
    plain_text <- paste0(plain_text, clean_text(research$loc[i]), "\n")
    # Skip N/A values
    if (research$institution[i] != "N/A") {
      plain_text <- paste0(plain_text, clean_text(research$institution[i]), "\n")
    }
    plain_text <- paste0(plain_text, clean_text(research$timeline[i]), "\n\n")
    
    # Process description bullets
    if (research$description_bullets[i] != "") {
      # Remove the bullet point markers and format each point on its own line
      bullets <- gsub("^- ", "", strsplit(research$description_bullets[i], "\n- ")[[1]])
      for (bullet in bullets) {
        # Clean text of HTML and markdown formatting
        bullet <- clean_text(bullet)
        plain_text <- paste0(plain_text, "• ", bullet, "\n")
      }
      plain_text <- paste0(plain_text, "\n")
    }
  }
  
  # SOFTWARE SECTION
  plain_text <- paste0(plain_text, "STATISTICAL SOFTWARE\n")
  plain_text <- paste0(plain_text, "====================\n\n")
  
  software <- dplyr::filter(cv$entries_data, section == "software")
  
  for (i in 1:nrow(software)) {
    plain_text <- paste0(plain_text, clean_text(software$title[i]), "\n")
    # Skip N/A values in institution
    if (software$institution[i] != "N/A") {
      plain_text <- paste0(plain_text, clean_text(software$institution[i]), "\n")
    }
    # Skip N/A values in location
    if (software$loc[i] != "N/A") {
      plain_text <- paste0(plain_text, clean_text(software$loc[i]), "\n")
    }
    plain_text <- paste0(plain_text, clean_text(software$timeline[i]), "\n\n")
    
    # Process description bullets
    if (software$description_bullets[i] != "") {
      # Remove the bullet point markers and format each point on its own line
      bullets <- gsub("^- ", "", strsplit(software$description_bullets[i], "\n- ")[[1]])
      for (bullet in bullets) {
        # Clean text of HTML and markdown formatting
        bullet <- clean_text(bullet)
        plain_text <- paste0(plain_text, "• ", bullet, "\n")
      }
      plain_text <- paste0(plain_text, "\n")
    }
  }
  
  # SKILLS SECTION
  plain_text <- paste0(plain_text, "EXPERTISE\n")
  plain_text <- paste0(plain_text, "=========\n\n")
  
  # Check if the CV object contains the aside entries data
  if (("aside_sections" %in% names(cv)) && ("aside_entries" %in% names(cv))) {
    # Sort sections by order
    aside_sections <- cv$aside_sections %>%
      dplyr::arrange(sort_order)
    
    # For each section, get and print entries
    for (i in 1:nrow(aside_sections)) {
      section_category <- aside_sections$category[i]
      section_name <- aside_sections$display_name[i]
      
      plain_text <- paste0(plain_text, section_name, ":\n")
      
      # Get entries for this section
      section_entries <- cv$aside_entries %>%
        dplyr::filter(category == !!section_category) %>%
        dplyr::arrange(sort_order)
      
      # Join entries with commas
      entry_list <- paste(section_entries$entry, collapse = ", ")
      plain_text <- paste0(plain_text, entry_list, "\n\n")
    }
  } else {
    # Add static skills content as fallback
    plain_text <- paste0(plain_text, 
      "Biology: Assay optimization, Cancer diagnostics, Cell-free DNA, droplet digital PCR, Liquid biopsy, DNA Methylation, Epigenetics and chromatin, Gene expression variability\n\n",
      "Data Analysis: Bisulfite sequencing, Differential Expression, Cell type deconvolution, Gene set enrichment analysis, Machine learning models, Single-cell multi-omics, Spatial transcriptomics\n\n",
      "Software/Coding: R/RStudio, Python, Bash scripting, Linux High-Performance Computing\n\n",
      "Data Visualization: ggplot2, jupyter notebook, markdown, matplotlib\n\n",
      "Package Development: Bioconductor, git/GitHub, PyPI\n\n",
      "Scientific Communication: High impact publications, Invited conference speaker\n\n"
    )
  }
  
  # FOOTER
  plain_text <- paste0(plain_text, "Last updated: ", format(Sys.Date(), "%B %d, %Y"), "\n")
  
  return(plain_text)
}

#' @description Construct a bar chart of skills
#' @param out_of The relative maximum for skills. Used to set what a fully filled in skill bar is.
print_skill_bars <- function(cv, out_of = 5, bar_color = "#969696", bar_background = "#d9d9d9", glue_template = "default"){

  if(glue_template == "default"){
    glue_template <- "
<div
  class = 'skill-bar'
  style = \"background:linear-gradient(to right,
                                      {bar_color} {width_percent}%,
                                      {bar_background} {width_percent}% 100%)\"
>{skill}</div>"
  }
  cv$skills %>%
    dplyr::mutate(width_percent = round(100*as.numeric(level)/out_of)) %>%
    glue::glue_data(glue_template) %>%
    print()

  invisible(cv)
}

#' @description Display a custom image in the aside section
#' @param cv The CV object
#' @param margin_top Top margin for the image
#' @param margin_bottom Bottom margin for the image
display_custom_image <- function(cv, margin_top = "-40px", margin_bottom = "0px", width = "100%", height = "250px") {
  # Function to display custom image instead of network logo
  
  # Check if the CV object has a custom image path
  if (is.null(cv$custom_image_path) || !file.exists(cv$custom_image_path)) {
    # If no custom image or file doesn't exist, return NULL
    return(NULL)
  }
  
  # Get the file extension to determine the image type
  file_ext <- tolower(tools::file_ext(cv$custom_image_path))
  
  # Only process supported image types
  if (!(file_ext %in% c("png", "jpg", "jpeg"))) {
    message("Unsupported image format. Please use PNG or JPEG.")
    return(NULL)
  }
  
  # Determine MIME type
  mime_type <- switch(file_ext,
                      "png" = "image/png",
                      "jpg" = "image/jpeg",
                      "jpeg" = "image/jpeg")
  
  # Read the image file and encode to base64
  img_data <- readBin(cv$custom_image_path, "raw", file.info(cv$custom_image_path)$size)
  base64_img <- base64enc::base64encode(img_data)
  
  # Create the data URI
  data_uri <- paste0("data:", mime_type, ";base64,", base64_img)
  
  # Return the HTML with the embedded image
  # Use the width and height parameters for consistent styling with network logo
  knitr::raw_html(paste0(
    '<div style="text-align: center; margin-top: ', margin_top, '; margin-bottom: ', margin_bottom, ';">',
    '<img src="', data_uri, '" style="width:', width, '; height:', height, ';" alt="Custom image">',
  '</div>'
  ))
  
  # Restore original warning level
  options(warn = oldw)
  
  return(result)
}

#' @description List of all links in document labeled by their superscript integer.
print_links <- function(cv) {
  n_links <- length(cv$links)
  if (n_links > 0) {
    cat("
Links {data-icon=link}
--------------------------------------------------------------------------------

<br>


")

    purrr::walk2(cv$links, 1:n_links, function(link, index) {
      print(glue::glue('{index}. {link}'))
    })
  }

  invisible(cv)
}

#' @description Contact information section with icons
print_contact_info <- function(cv){
  # Make sure we have contact info data
  if (is.null(cv$contact_info) || nrow(cv$contact_info) == 0) {
    cat("No contact information available.\n")
    return(invisible(cv))
  }
  
  ## Replace NAs with empty strings
  cv$contact_info[is.na(cv$contact_info)] <- ""
  
  # Manually add the email entry since it seems to be missing
  cat("- <i class='fa fa-envelope'></i> bmill3r@gmail.com\n")
  
  # Try both by column name and position for better robustness
  # For column position approach
  label_col <- 1 
  icon_col <- 2  
  content_col <- 3 
  
  # For column name approach
  loc_col <- which(names(cv$contact_info) == "loc")
  icon_col_name <- which(names(cv$contact_info) == "icon")
  contact_col <- which(names(cv$contact_info) == "contact")
  
  # Use column names if available, otherwise use positions
  if (length(loc_col) > 0) { label_col <- loc_col[1] }
  if (length(icon_col_name) > 0) { icon_col <- icon_col_name[1] }
  if (length(contact_col) > 0) { content_col <- contact_col[1] }
  
  # Make sure we have enough columns
  if (ncol(cv$contact_info) >= 3) {
    # Process each row of contact info
    for (i in seq_len(nrow(cv$contact_info))) {
      # Extract values
      label <- cv$contact_info[i, label_col]
      icon <- cv$contact_info[i, icon_col] 
      content <- cv$contact_info[i, content_col]
      
      # Skip if this is the email entry (we already showed it at the start)
      if (!is.na(label) && label == "email") next
      
      # Skip empty rows
      if (is.na(icon) || icon == "") next
      
      # Start with the icon
      output <- paste0("- <i class='fa fa-", icon, "'></i> ")
      
      # Special handling for email entries (should not reach here, but just in case)
      if (!is.na(label) && label == "email" && !is.na(content) && content != "") {
        # For email, just display the email address (no link)
        output <- paste0(output, content)
      }
      # Handle markdown links [text](url)
      else if (!is.na(content) && grepl("\\[(.+?)\\]\\((.+?)\\)", content)) {
        # Extract the parts of the markdown link
        link_text <- gsub(".*\\[(.+?)\\]\\(.*\\).*", "\\1", content)
        link_url <- gsub(".*\\[.+?\\]\\((.+?)\\).*", "\\1", content)
        
        # Create HTML link
        output <- paste0(output, "<a href='", link_url, "'>", link_text, "</a>")
      }
      # For GitHub, LinkedIn, etc. show the URL as the text
      else if (!is.na(label) && label %in% c("github", "linkedin", "website") && 
              !is.na(content) && content != "") {
        output <- paste0(output, "<a href='", content, "'>", content, "</a>")
      }
      # Default case - just show the content after the icon
      else if (!is.na(content) && content != "") {
        output <- paste0(output, content)
      }
      # Fallback: use label if content is empty
      else if (!is.na(label) && label != "") {
        output <- paste0(output, label)
      }
      
      # Print the final line
      cat(paste0(output, "\n"))
    }
  } else {
    # Fallback if we don't have enough columns
    for (i in seq_len(nrow(cv$contact_info))) {
      row <- cv$contact_info[i, , drop = FALSE]
      values <- as.character(unlist(row))
      non_empty <- values[values != ""]
      if (length(non_empty) > 0) {
        cat(paste0("- ", non_empty[1], "\n"))
      }
    }
  }
  
  invisible(cv)
}

#' @description Create a bar chart showing Google Scholar citations for the last 5 years
#' @param scholar_id Your Google Scholar ID
#' @param bar_color Color for the citation bars
#' @param text_color Color for the text
#' @param base_size Base font size for the chart
print_scholar_citations <- function(cv, scholar_id, bar_color = "#969696", text_color = "#777777", base_size = 14) {
  # Completely suppress all warnings and messages
  oldw <- getOption("warn")
  options(warn = -1)
  # Check if required packages are installed - with warnings suppressed
  required_packages <- c("scholar", "ggplot2", "dplyr", "lubridate", "base64enc")
  for (pkg in required_packages) {
    if (!suppressWarnings(requireNamespace(pkg, quietly = TRUE))) {
      message(paste("Installing", pkg, "package for citation visualization"))
      suppressWarnings(utils::install.packages(pkg, repos = "http://cran.us.r-project.org"))
    }
  }
  
  # Load packages silently with warnings suppressed
  suppressWarnings({
    suppressPackageStartupMessages({
      library(scholar)
      library(ggplot2)
      library(dplyr)
      library(lubridate)
      library(base64enc)
    })
  })
  
  # Initialize HTML content
  html_content <- ""
  
  # Catch any errors from Google Scholar retrieval
  tryCatch({
    # Get citation data for the last 5 years
    current_year <- lubridate::year(lubridate::today())
    years <- (current_year - 4):current_year
    
    # Get citation history
    citation_history <- scholar::get_citation_history(scholar_id)
    
    # Filter for last 5 years and ensure all years are present
    citations_data <- citation_history %>%
      dplyr::filter(year %in% years)
    
    # Add any missing years with zero citations
    missing_years <- setdiff(years, citations_data$year)
    if (length(missing_years) > 0) {
      missing_data <- data.frame(year = missing_years, cites = 0)
      citations_data <- rbind(citations_data, missing_data)
    }
    
    # Sort by year
    citations_data <- citations_data %>%
      dplyr::arrange(year)
    
    # Create the bar chart using ggplot2
    plot <- ggplot2::ggplot(citations_data, aes(x = as.factor(year), y = cites)) +
      ggplot2::geom_bar(stat = "identity", fill = "black") +
      ggplot2::labs(title = NULL, 
                   x = "", 
                   y = "") +
      ggplot2::theme_minimal(base_size = base_size) +
      ggplot2::theme(
        axis.text = ggplot2::element_text(color = "black"),
        axis.title = ggplot2::element_text(color = "black"),
        axis.line = ggplot2::element_line(color = "black"),
        panel.grid.minor = ggplot2::element_blank(),
        panel.grid.major.x = ggplot2::element_blank(),
        panel.grid.major.y = ggplot2::element_line(color = "#EEEEEE")
      )
    
    # Convert to a temporary image file
    temp_file <- tempfile(fileext = ".png")
    ggplot2::ggsave(temp_file, plot, width = 6, height = 4, dpi = 100)
    
    # Read the image and convert to base64
    img_data <- readBin(temp_file, "raw", file.info(temp_file)$size)
    base64_img <- base64enc::base64encode(img_data)
    
    # Clean up temp file
    unlink(temp_file)
    
    # Create HTML with embedded image
    html_content <- paste0(
      '<div style="text-align: center; margin-top: 20px; margin-bottom: 15px;">', 
      '<img src="data:image/png;base64,', base64_img, '" ', 
      'style="width: 100%; max-width: 400px; margin-top: 10px;" alt="Google Scholar Citations">',
      '</div>'
    )
    
  }, error = function(e) {
    # If there's an error, display a message
    message("Error retrieving Google Scholar data: ", e$message)
    html_content <- paste0(
      '<div style="text-align: center; color: #777777; margin: 20px;">', 
      '<i class="fa fa-exclamation-circle"></i> ', 
      'Unable to fetch Google Scholar citations. ', 
      'Please check your scholar ID and internet connection.',
      '</div>'
    )
  })
  
  # Restore original warning level
  options(warn = oldw)
  
  # Print the HTML content directly to the output
  cat(html_content)
  
  invisible(cv)
}



## remake function to change the dimensions of the graphic directly

#' Build interactive network logo
#'
#' Constructs a network based on your position data to be used as a logo.
#' Interactive in HTML version and static in the PDF version. Notes are entries,
#' colored by section and connected if they occurred in the same year
#'
#' @param position_data position data from your `CV_Printer` class.
#'
#' @return Interactive force-directed layout network of your CV data
#' @export
build_network_logo_custom <- function(position_data = NULL, 
                                     width = "100%", 
                                     height = "250px", 
                                     node_size = 10,
                                     link_strength = 0.8,
                                     charge_strength = -300,
                                     color_palette = c("#4292c6", "#41ab5d", "#ef6548", "#984ea3", "#ff7f00", "#a65628"),
                                     margin_top = "-40px", 
                                     margin_bottom = "0px",
                                     img_width = 450,
                                     img_height = 350,
                                     random_data = FALSE,
                                     num_nodes = 12,
                                     num_edge_factor = 1.5) {
  # Completely suppress all warnings and messages
  oldw <- getOption("warn")
  options(warn = -1)
  # Get current environment for checking PDF mode
  cv <- parent.frame()$CV
  pdf_mode <- if(!is.null(cv$pdf_mode)) cv$pdf_mode else FALSE
  
  # Check if custom image should be used instead of network logo
  if (!is.null(cv$custom_image_path) && file.exists(cv$custom_image_path)) {
    return(display_custom_image(cv, margin_top, margin_bottom, width, height))
  }
  # Check if required packages are installed - with warnings suppressed
  required_packages <- c("igraph", "base64enc")
  for (pkg in required_packages) {
    if(!suppressWarnings(requireNamespace(pkg, quietly = TRUE))) {
      message(paste("Installing", pkg, "package for network visualization"))
      suppressWarnings(utils::install.packages(pkg, repos = "http://cran.us.r-project.org"))
    }
  }
  
  # Load required packages silently to prevent attachment messages in output
  # Use suppressWarnings to hide version warnings
  suppressWarnings({
    suppressPackageStartupMessages({
      library(igraph)
      library(base64enc)
    })
  })
  
  # Generate random data if requested, otherwise use position data
  if (random_data) {
    # Generate random nodes with community structure
    set.seed(42)  # For reproducibility
    
    # Determine number of communities
    num_communities <- min(5, length(color_palette))
    
    # Calculate nodes per community (roughly equal distribution)
    nodes_per_community <- ceiling(num_nodes / num_communities)
    
    # Create vertices dataframe with community assignments
    communities <- rep(LETTERS[1:num_communities], each = nodes_per_community)[1:num_nodes]
    vertices_df <- data.frame(
      id = 1:num_nodes,
      section = communities
    )
    
    # Parameters for connectivity
    within_community_probability <- 0.7    # High probability of connection within communities
    between_community_probability <- 0.03   # Low probability of connection between communities
    
    # Initialize empty edge dataframe
    edges_df <- data.frame(source = integer(0), target = integer(0))
    
    # Create within-community edges
    for (community in LETTERS[1:num_communities]) {
      # Get all nodes in this community
      community_nodes <- vertices_df$id[vertices_df$section == community]
      
      if (length(community_nodes) > 1) {
        # Create all possible edges within community
        possible_edges <- expand.grid(
          source = community_nodes,
          target = community_nodes
        ) %>%
          dplyr::filter(source < target)  # Avoid duplicates and self-loops
        
        # Sample edges with high probability
        for (i in 1:nrow(possible_edges)) {
          if (runif(1) < within_community_probability) {
            edges_df <- rbind(edges_df, possible_edges[i, ])
          }
        }
      }
    }
    
    # Create between-community edges (fewer)
    # This ensures the graph is connected across communities
    between_edges <- data.frame(source = integer(0), target = integer(0))
    
    for (i in 1:(num_communities-1)) {
      for (j in (i+1):num_communities) {
        community1 <- LETTERS[i]
        community2 <- LETTERS[j]
        
        # Get random representatives from each community
        nodes1 <- vertices_df$id[vertices_df$section == community1]
        nodes2 <- vertices_df$id[vertices_df$section == community2]
        
        if (length(nodes1) > 0 && length(nodes2) > 0) {
          # Create all possible edges between communities
          possible_edges <- expand.grid(
            source = nodes1,
            target = nodes2
          )
          
          # Sample edges with low probability
          for (k in 1:nrow(possible_edges)) {
            if (runif(1) < between_community_probability) {
              between_edges <- rbind(between_edges, possible_edges[k, ])
            }
          }
        }
      }
    }
    
    # Make sure we have at least some between-community edges to keep the graph connected
    if (nrow(between_edges) == 0) {
      # Connect each community to the next one with at least one edge
      for (i in 1:(num_communities-1)) {
        community1 <- LETTERS[i]
        community2 <- LETTERS[i+1]
        
        nodes1 <- vertices_df$id[vertices_df$section == community1]
        nodes2 <- vertices_df$id[vertices_df$section == community2]
        
        if (length(nodes1) > 0 && length(nodes2) > 0) {
          between_edges <- rbind(between_edges, data.frame(
            source = sample(nodes1, 1),
            target = sample(nodes2, 1)
          ))
        }
      }
    }
    
    # Combine within and between community edges
    edges_df <- rbind(edges_df, between_edges)
    
    # Ensure proper ordering of source/target to avoid duplicates
    edges_df <- edges_df %>%
      dplyr::mutate(
        min_id = pmin(source, target),
        max_id = pmax(source, target)
      ) %>%
      dplyr::select(source = min_id, target = max_id) %>%
      unique()
    
    # Create the graph from the community-structured data
    g <- igraph::graph_from_data_frame(edges_df, directed = FALSE, vertices = vertices_df)
    
  } else {
    # Use the original position data
    positions <- position_data %>%
      dplyr::mutate(
        id = dplyr::row_number(),
        title = stringr::str_remove_all(title, '(\\(.+?\\))|(\\[)|(\\])'),
        section = stringr::str_replace_all(section, "_", " ") %>% stringr::str_to_title()
      )
    
    # Create simple edge list by connecting nodes in the same section
    section_groups <- positions %>%
      dplyr::group_by(section) %>%
      dplyr::summarize(node_ids = list(id), .groups = 'drop')
    
    # Function to create edges between all nodes in a group
    create_group_edges <- function(ids) {
      if (length(ids) <= 1) return(NULL)
      expand.grid(source = ids, target = ids) %>%
        dplyr::filter(source < target) %>%
        dplyr::select(source, target)
    }
    
    # Create edges between nodes in the same section
    edges_df <- purrr::map_dfr(section_groups$node_ids, create_group_edges)
    
    # Add some cross-section connections to ensure the graph is connected
    if (length(unique(positions$section)) > 1) {
      # Get one representative node from each section
      section_reps <- section_groups %>%
        dplyr::mutate(rep_id = purrr::map_dbl(node_ids, ~ .x[1])) %>%
        dplyr::pull(rep_id)
      
      # Connect sequential representatives to ensure connectivity
      section_connections <- data.frame(
        source = section_reps[-length(section_reps)],
        target = section_reps[-1]
      )
      
      # Combine with section-based edges
      edges_df <- rbind(edges_df, section_connections)
    }
    
    # Create the graph from position data
    g <- igraph::graph_from_data_frame(edges_df, directed = FALSE, 
                                     vertices = data.frame(id = positions$id, 
                                                          section = positions$section))
  }
  
  # Set node colors based on section
  unique_sections <- unique(igraph::V(g)$section)
  color_map <- setNames(
    color_palette[1:length(unique_sections)],
    unique_sections
  )
  
  node_colors <- color_map[igraph::V(g)$section]
  
  # Create the plot in a temporary file and convert to base64
  temp_file <- tempfile(fileext = ".png")
  
  # Extract numeric dimensions from width and height if they're percentages
  # Default to 600x800 (portrait) if we can't parse the dimensions
  img_width <- 600
  img_height <- 800
  
  # Generate a portrait-oriented image with higher resolution
  png(temp_file, width = img_width, height = img_height, bg = "transparent", res = 300)
  
  # Set smaller margins to avoid the 'figure margins too large' error
  par(mar = c(0, 0, 0, 0))
  
  # Use a layout that spreads nodes more evenly in a circular pattern - with warnings suppressed
  layout <- suppressWarnings(
    igraph::layout_with_fr(g, niter = 1000, area = 8*(vcount(g)^2), repulserad = vcount(g)^3.5)
  )
  
  # Plot with appropriate node size and edge thickness
  plot(g, 
       vertex.color = node_colors,
       vertex.frame.color = node_colors,  # Match frame to fill color for solid appearance
       vertex.size = node_size,          # Use the node size directly without multiplier
       vertex.label = NA,
       edge.width = 0.6,                 # Even thinner edges
       edge.color = "#888888",           # Lighter edge color
       margin = c(0, 0, 0, 0),          # No margins
       layout = layout)
  dev.off()
  
  # Read the image file and encode to base64
  img_data <- readBin(temp_file, "raw", file.info(temp_file)$size)
  base64_img <- base64enc::base64encode(img_data)
  
  # Create the data URI
  data_uri <- paste0("data:image/png;base64,", base64_img)
  
  # Clean up the temp file
  if (file.exists(temp_file)) {
    file.remove(temp_file)
  }
  
  # Network visualization embedded as base64 data URI - message suppressed
  
  # Return the HTML with the embedded image
  # Use the width and height parameters passed to the function
  result <- knitr::raw_html(paste0(
    '<div style="text-align: center; margin-top: ', margin_top, '; margin-bottom: ', margin_bottom, ';">',
    '<img src="', data_uri, '" style="width: ', width, '; height: ', height, '" alt="Network visualization of professional experience">',
    '</div>'
  ))
  
  # Restore original warning level
  options(warn = oldw)
  
  return(result)
}

#' @description Print the ASIDE section entries from the aside_entries.csv file
#' @param cv The CV object containing aside_sections and aside_entries data
print_aside_section <- function(cv) {
  # Check if the CV object contains the aside entries data
  if (!("aside_sections" %in% names(cv)) || !("aside_entries" %in% names(cv))) {
    # If not available, return a message
    cat("Aside data not available. Please create aside_sections.csv and aside_entries.csv files.")
    return(invisible(cv))
  }
  
  sections <- cv$aside_sections %>% dplyr::arrange(sort_order)
  entries <- cv$aside_entries %>% dplyr::arrange(category, sort_order)
  
  # Add CSS for the table-based approach
  cat('<style>
  .skills-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 0.3em;
  }
  .skill-category-cell {
    font-weight: bold;
    padding-bottom: 0.2em;
    border-bottom: none;
  }
  .skill-items-cell {
    padding-top: 0;
    padding-bottom: 0.3em;
    border-top: none;
  }
  .skill-item {
    display: block;
    margin-bottom: 0.1em;
    line-height: 1.1;
  }
  tr.skill-row {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }
  .page-break {
    page-break-before: always !important;
    break-before: page !important;
    display: block;
    width: 100%;
    height: 1px;
  }
</style>\n')
  
  # Create tables with max 3 categories per table
  max_categories_per_page <- 3
  total_categories <- sum(sapply(seq_len(nrow(sections)), function(i) {
    section <- sections[i, ]
    section_entries <- entries %>% dplyr::filter(category == section$category)
    return(nrow(section_entries) > 0)
  }))
  
  # Counter for categories
  category_count <- 0
  
  # Start first table
  cat('<table class="skills-table">\n')
  
  # Output each category as a table row
  for (i in seq_len(nrow(sections))) {
    section <- sections[i, ]
    section_entries <- entries %>% dplyr::filter(category == section$category)
    
    if (nrow(section_entries) > 0) {
      # Increment category counter
      category_count <- category_count + 1
      
      # If we've reached the max per page and this isn't the last category, close table and start a new one
      if (category_count > max_categories_per_page && category_count <= total_categories) {
        # Close current table
        cat('</table>\n\n')
        
        # Add explicit page break
        cat('<div class="page-break"></div>\n\n')
        
        # Start new table
        cat('<table class="skills-table">\n')
        
        # Reset counter to 1 for the new page
        category_count <- 1
      }
      
      # Start a new table row for this category
      cat('<tr class="skill-row">\n')
      
      # Category header cell
      cat(paste0('  <td class="skill-category-cell">', section$display_name, '</td>\n'))
      cat('</tr>\n')
      
      # Start a new row for the items
      cat('<tr class="skill-row">\n')
      cat('  <td class="skill-items-cell">\n')
      
      # Print entries
      for (j in seq_len(nrow(section_entries))) {
        entry_text <- section_entries$entry[j]
        if (section$is_code == "TRUE") {
          cat(paste0('    <span class="skill-item">`', entry_text, '`</span>\n'))
        } else {
          cat(paste0('    <span class="skill-item">', entry_text, '</span>\n'))
        }
      }
      
      # Close the items cell and row
      cat('  </td>\n')
      cat('</tr>\n')
      
      # Add an empty spacer row (but smaller now)
      cat('<tr class="spacer-row"><td style="height: 0.1em;"></td></tr>\n')
    }
  }
  
  # Close the table
  cat('</table>\n')
  
  invisible(cv)
}
