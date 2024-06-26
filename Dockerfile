# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the app directory contents into the container at /app
COPY . /app

# Use Poetry to install the dependencies from pyproject.toml and poetry.lock files
# Assume pyproject.toml and optionally poetry.lock exists and define the project's dependencies
COPY pyproject.toml poetry.lock* /app/

# Configure Poetry and install dependencies
# Avoid creating a virtual environment within the Docker container
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Now install the project package, in editable mode if needed
RUN poetry run pip install -e .

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable for Streamlit
ENV STREAMLIT_SERVER_PORT 8501

# Run main.py when the container launches
CMD ["streamlit", "run", "app/main.py"]
