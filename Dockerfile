FROM python:3.13-slim-bookworm

RUN pip3 install --upgrade pip
COPY requirements-test.txt requirements-test.txt
RUN pip3 install -r requirements-test.txt

WORKDIR /app

