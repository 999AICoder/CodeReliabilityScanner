# Use an official Python runtime as the base image
#FROM python:3.9-slim
FROM python:3.12.7-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.docker.txt
RUN pip install --upgrade pip
RUN pip install uv
RUN uv pip install --system --upgrade setuptools
RUN uv pip install --system --no-cache-dir -r requirements.docker.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Set environment variables
ENV DOCKER_ENV=1
ENV NAME=World
ENV PYTHONWARNINGS="ignore::SyntaxWarning"
ENV GOOGLE_CLOUD_PROJECT=""

# Install Google Cloud SDK and other dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    git \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update && apt-get install -y google-cloud-sdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Run app.py when the container launches
CMD ["python", "app.py"]
