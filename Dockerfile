# Use an official Python runtime as a parent image
FROM python:3.9-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the contents of the local directory ./dkim-service into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN apk add --no-cache gcc musl-dev && \
    pip install --trusted-host pypi.python.org -r requirements.txt && \
    apk del gcc musl-dev

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=dkim.py

# Run app.py when the container launches
CMD ["flask", "run", "--host", "0.0.0.0"]
