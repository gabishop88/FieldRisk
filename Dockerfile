FROM rocker/r-ver:4.4.0

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install required system dependencies for R packages and tools like APSIM
RUN apt-get update -y && apt-get install -y \
  zlib1g-dev \
  git \
  wget \
  curl \
  unzip \
  tar \
  apt-transport-https \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Install Microsoft package feed for .NET
# RUN wget https://packages.microsoft.com/config/debian/11/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && \
#     dpkg -i packages-microsoft-prod.deb && \
#     rm packages-microsoft-prod.deb

# Install .NET runtime 
# RUN apt-get update && apt-get install -y dotnet-runtime-8.0 && \
#     rm -rf /var/lib/apt/lists/*

# Set up global R options for all sessions
RUN mkdir -p /usr/local/lib/R/etc/ /usr/lib/R/etc/
RUN echo "options(renv.config.pak.enabled = FALSE, repos = c(CRAN = 'https://cran.rstudio.com/'), download.file.method = 'libcurl', Ncpus = 4)" | tee /usr/local/lib/R/etc/Rprofile.site | tee /usr/lib/R/etc/Rprofile.site

# Install R package manager tools
RUN R -e 'install.packages("remotes")'
RUN R -e 'remotes::install_version("renv", version = "1.0.3")'

# Copy the renv cache into the image
COPY app/simulations/renv_cache /root/.cache/R/renv

# Copy and restore the R project package environment
COPY app/simulations/renv.lock renv.lock
RUN R -e 'renv::restore()'

# Copy APSIM-X files to the Docker image (version 2025.4.7717.0)
COPY app/simulations/next_gen_apsim/data.tar.gz /tmp/
COPY app/simulations/next_gen_apsim/control.tar.gz /tmp/
COPY app/simulations/next_gen_apsim/debian-binary /tmp/

# Extract APSIM files to a permanent location and clean up temp files
RUN tar -xzf /tmp/data.tar.gz -C / && \
    tar -xzf /tmp/control.tar.gz -C / && \
    rm /tmp/data.tar.gz /tmp/control.tar.gz /tmp/debian-binary

# Add APSIM-X to environment path
ENV APSIM_PATH=/usr/local/apsimx
ENV PATH=$APSIM_PATH:$PATH

WORKDIR /app

COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
RUN uv sync --frozen --no-dev

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8501
CMD ["streamlit", "run", "main.py", "--server.address=0.0.0.0"]
