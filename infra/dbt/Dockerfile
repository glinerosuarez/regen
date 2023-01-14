FROM python:3.8.16-slim-bullseye

# Set working directory
WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -qq -y \
    git gcc build-essential libpq-dev --fix-missing --no-install-recommends \
    && apt-get clean

# Make sure we are using latest pip
RUN pip install --upgrade pip

# Create directory for dbt config
RUN mkdir -p /root/.dbt

# Copy requirements.txt
COPY infra/dbt/requirements.txt requirements.txt

# Install dependencies
RUN pip install -r requirements.txt

# Copy dbt profile
COPY infra/dbt/profiles.yml /root/.dbt/profiles.yml
