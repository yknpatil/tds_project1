FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/requirements.txt

# Install build essentials for packages that require compilation (like Pydantic V2)
# and other potential system dependencies.
# 'build-essential' provides gcc, g++, make, etc.
# 'pkg-config' might be needed for some libraries.
# 'cargo' and 'rustc' are for Rust if you specifically need them for other things,
# but for pydantic, build-essential is often enough as it links against system libraries.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    # Optional: libffi-dev for cryptography or cffi if needed by other deps
    # libpq-dev for PostgreSQL clients like psycopg2
    # Add other -dev packages if your specific libraries require them
    && \
    rm -rf /var/lib/apt/lists/*

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container at /app
COPY . /app

# Inform Docker that the container listens on the specified network port at runtime
EXPOSE 8000

# Command to run the application when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
