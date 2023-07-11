FROM python:3.11-slim-bookworm

RUN pip3 install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

WORKDIR /app

