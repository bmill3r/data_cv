FROM rocker/verse:4.2.2

LABEL maintainer="Brendan Miller"
LABEL description="Environment for generating data-driven CVs and resumes"

# Install system dependencies for headless Chrome and R packages
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    lsb-release \
    xvfb \
    xauth \
    libx11-xcb1 \
    libxtst6 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Use chromium-browser instead of Google Chrome
RUN apt-get update && apt-get install -y \
    chromium-browser \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c('rmarkdown', 'pagedown', 'fs', 'optparse', 'remotes', 'magrittr', 'dplyr', 'tidyr', 'jsonlite', 'stringr', 'lubridate', 'purrr', 'readr', 'glue'), repos = 'http://cran.us.r-project.org')"
RUN R -e "remotes::install_github('nstrayer/datadrivencv')"

# Create working directory
WORKDIR /cv

# Setup for headless browser
ENV PAGEDOWN_CHROME="/usr/bin/chromium-browser"
ENV PAGEDOWN_CHROME_ARGS="--no-sandbox"

# Create entrypoint script
RUN echo '#!/bin/bash\n\
# Run the provided command or start R if none given\n\
if [ $# -eq 0 ]; then\n\
  R\n\
else\n\
  exec "$@"\n\
fi' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
