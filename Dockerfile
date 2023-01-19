FROM python:3.7.16-slim-bullseye

WORKDIR /app

COPY . .

# Make sure we are using latest pip
RUN pip install --upgrade pip

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Enable python print statements to be dumped to the I/O stream
ENV PYTHONUNBUFFERED 1
