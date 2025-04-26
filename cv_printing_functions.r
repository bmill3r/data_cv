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
                              sheet_is_publicly_readable = TRUE) {

  cv <- list(
    pdf_mode = pdf_mode,
    links = c()
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
    cv$entries_data <- readr::read_csv(paste0(data_location, "entries.csv"), skip = 1)
    cv$skills       <- readr::read_csv(paste0(data_location, "language_skills.csv"), skip = 1)
    cv$text_blocks  <- readr::read_csv(paste0(data_location, "text_blocks.csv"), skip = 1)
    cv$contact_info <- readr::read_csv(paste0(data_location, "contact_info.csv"), skip = 1)
    
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
print_text_block <- function(cv, label){
  text_block <- dplyr::filter(cv$text_blocks, loc == label) %>%
    dplyr::pull(text)

  strip_res <- sanitize_links(cv, text_block)

  cat(strip_res$text)

  invisible(strip_res$cv)
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
  ## if using blank rows to increase separation, have empty rows and replace NAs with empty strings
  cv$contact_info[is.na(cv$contact_info)] <- ""
  glue::glue_data(
    cv$contact_info,
    "- <i class='fa fa-{icon}'></i> {contact}"
  ) %>% print()

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
build_network_logo_custom <- function(position_data, 
                                     width = "100%", 
                                     height = "250px", 
                                     node_size = 12,
                                     link_strength = 0.7,
                                     charge_strength = -150,
                                     color_palette = c("#4292c6", "#41ab5d", "#ef6548", "#984ea3", "#ff7f00", "#a65628"),
                                     margin_top = "-40px", 
                                     margin_bottom = "0px"){
  
  # Get current environment for checking PDF mode
  cv <- parent.frame()$CV
  pdf_mode <- if(!is.null(cv$pdf_mode)) cv$pdf_mode else FALSE
  
  # Check if required packages are installed
  required_packages <- c("igraph", "base64enc")
  for (pkg in required_packages) {
    if(!requireNamespace(pkg, quietly = TRUE)) {
      message(paste("Installing", pkg, "package for network visualization"))
      utils::install.packages(pkg, repos = "http://cran.us.r-project.org")
    }
  }
  
  # Load required packages silently to prevent attachment messages in output
  suppressPackageStartupMessages({
    library(igraph)
    library(base64enc)
  })
  
  positions <- position_data %>%
    dplyr::mutate(
      id = dplyr::row_number(),
      title = stringr::str_remove_all(title, '(\\(.+?\\))|(\\[)|(\\])'),
      section = stringr::str_replace_all(section, "_", " ") %>% stringr::str_to_title()
    )
  
  combination_indices <- function(n){
    rep_counts <- (n:1) - 1
    dplyr::tibble(
      a = rep(1:n, times = rep_counts),
      b = purrr::flatten_int( purrr::map(rep_counts, ~{tail(1:n, .x)}) )
    )
  }
  
  current_year <- lubridate::year(lubridate::ymd(Sys.Date()))
  edges <- positions %>%
    dplyr::select(id, start_year, end_year) %>%
    dplyr::mutate(
      end_year = ifelse(end_year > current_year, current_year, end_year),
      start_year = ifelse(start_year > current_year, current_year, start_year)
    ) %>%
    purrr::pmap_dfr(function(id, start_year, end_year){
      dplyr::tibble(
        year = start_year:end_year,
        id = id
      )
    }) %>%
    dplyr::group_by(year) %>%
    tidyr::nest() %>%
    dplyr::rename(ids_for_year = data) %>%
    purrr::pmap_dfr(function(year, ids_for_year){
      combination_indices(nrow(ids_for_year)) %>%
        dplyr::transmute(
          year = year,
          source = ids_for_year$id[a],
          target = ids_for_year$id[b]
        )
    })
  
  # Generate network visualization as embedded base64 image - message suppressed
  
  # Create igraph object from edge list
  edges_df <- data.frame(
    source = edges$source,
    target = edges$target
  )
  
  g <- igraph::graph_from_data_frame(edges_df, directed = FALSE, 
                                    vertices = data.frame(id = positions$id, 
                                                         section = positions$section))
  
  # Set node colors based on section
  unique_sections <- unique(positions$section)
  color_map <- setNames(
    color_palette[1:length(unique_sections)],
    unique_sections
  )
  
  node_colors <- color_map[igraph::V(g)$section]
  
  # Create the plot in a temporary file and convert to base64
  temp_file <- tempfile(fileext = ".png")
  
  # Generate a portrait-oriented image with higher resolution
  png(temp_file, width = 600, height = 900, bg = "transparent", res = 300)
  
  # Use a layout that spreads nodes more evenly - with warnings suppressed
  layout <- suppressWarnings(
    igraph::layout_with_fr(g, niter = 500)
  )
  
  # Plot with appropriate node size and edge thickness
  plot(g, 
       vertex.color = node_colors,
       vertex.size = node_size * 1.5, # Moderate node size
       vertex.label = NA,
       edge.width = 1.3,       # Thinner edges
       edge.color = "#666666", # Darker edge color for contrast
       margin = c(0.01, 0.01, 0.01, 0.01), # Very minimal margins
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
  # Display the visualization at a much larger size
  knitr::raw_html(paste0(
    '<div style="text-align: center; margin-top: ', margin_top, '; margin-bottom: ', margin_bottom, ';">',
    '<img src="', data_uri, '" style="width: 90%; height: auto; min-height: 400px;" alt="Network visualization of professional experience">',
    '</div>'
  ))
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
  
  # Process the aside sections and entries
  sections <- cv$aside_sections %>%
    dplyr::arrange(sort_order)
  
  entries <- cv$aside_entries %>%
    dplyr::arrange(category, sort_order)
  
  # Generate HTML for each section
  for (i in 1:nrow(sections)) {
    section <- sections[i, ]
    section_entries <- entries %>% 
      dplyr::filter(category == section$category)
    
    if (nrow(section_entries) > 0) {
      # Print section header
      cat(paste0('<div class="skill-category">', section$display_name, '</div>\n'))
      
      # Print entries with appropriate formatting
      for (j in 1:nrow(section_entries)) {
        entry_text <- section_entries$entry[j]
        
        # Format code entries differently
        if (section$is_code == "TRUE") {
          cat(paste0('<span class="skill-item">`', entry_text, '`</span>\n'))
        } else {
          cat(paste0('<span class="skill-item">', entry_text, '</span>\n'))
        }
      }
      
      # Add a blank line between sections
      if (i < nrow(sections)) {
        cat("\n")
      }
    }
  }
  
  invisible(cv)
}
