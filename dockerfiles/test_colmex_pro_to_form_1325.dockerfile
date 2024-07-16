FROM ubuntu:20.04

# Set the environment variable for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y wget xz-utils fontconfig libfreetype6 libjpeg8-dev zlib1g-dev libxext6 libxrender1 libssl1.1  \
    xfonts-base xfonts-75dpi && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add repository for python 3.10
RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa

# Install necessary packages
RUN apt-get update && \
    apt-get install -y python3.10 python3.10-distutils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.10
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3.10 get-pip.py && \
    rm get-pip.py

# Install wkhtmltopdf - ARM64
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_arm64.deb && \
    apt-get install -y ./wkhtmltox_0.12.6-1.bionic_arm64.deb && \
    rm wkhtmltox_0.12.6-1.bionic_arm64.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /colmex_pro_to_form_1325

# Copy the requirements.txt file
COPY requirements.txt .

# Copy the directory contents into the container
COPY colmex_pro_to_form_1325 .

# Install Python dependencies
RUN python3.10 -m pip install --no-cache-dir --upgrade pip numpy && \
    python3.10 -m pip install --no-cache-dir -r requirements.txt

# Run tests
CMD ["python3.10", "-m", "pytest", "-v"]
