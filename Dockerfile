FROM python:3.10-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

#ENV KBANK_CONSUMER_ID=
#ENV KBANK_CONSUMER_SECRET=

EXPOSE 9111
CMD ["python", "app.py"]