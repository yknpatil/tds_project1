# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces the image size by not storing pip's cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container at /app
# This includes your main.py and any other project files
COPY . /app

# Inform Docker that the container listens on the specified network port at runtime
# This is mainly for documentation and doesn't publish the port automatically
EXPOSE 8000

# Command to run the application when the container starts
# main:app refers to the 'app' FastAPI instance in your 'main.py' file
# --host 0.0.0.0 makes the app accessible from outside the container
# --port 8000 tells Uvicorn to listen on port 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]