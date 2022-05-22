FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Enable python print statements to be dumped to the I/O stream
ENV PYTHONUNBUFFERED 1

COPY . .