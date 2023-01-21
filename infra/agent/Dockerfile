FROM python:3.7-slim

WORKDIR /app

COPY infra/agent/requirements.txt .

# Install OS dependencies
RUN apt-get update && apt-get install -qq -y \
    git gcc build-essential libpq-dev --fix-missing --no-install-recommends \
    && apt-get clean

# Make sure we are using latest pip
RUN pip install --upgrade pip

# Install dependencies
RUN pip install -r requirements.txt

# Enable python print statements to be dumped to the I/O stream
ENV PYTHONUNBUFFERED 1

# Copy source files
COPY src .

# Make main.py executable
RUN chmod +x main.py