# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.docker.txt
RUN pip install --no-cache-dir -r requirements.docker.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Set environment variables
ENV DOCKER_ENV=1
ENV NAME World

# Run app.py when the container launches
CMD ["python", "app.py"]
