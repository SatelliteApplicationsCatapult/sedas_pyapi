FROM python:3.7-stretch

WORKDIR /app/

COPY query.py ./

RUN apt-get update \
    && apt-get install -y gcc gdal-bin python-gdal unzip zip wget \
    && pip install --upgrade pip setuptools wheel \
    && apt-get clean