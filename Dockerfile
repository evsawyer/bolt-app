# Use an official Python image
FROM python:3.13

# Set environment variables to ensure Poetry installs correctly
ENV POETRY_VERSION=2.1.1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# --- Add this line for confirmation ---
RUN echo "**** Dockerfile: I am being built! ****"
# --- End of confirmation line ---

# Copy the project files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application files
COPY . .

# Expose the port your app will run on
EXPOSE 8080

# Run the application
CMD ["python", "src/bolt_app/socket-app-session-id.py"]