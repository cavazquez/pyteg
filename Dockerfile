FROM python:3.11-slim-bookworm

RUN pip3 install --upgrade pip
COPY requirements-nogui.txt requirements-nogui.txt
RUN pip3 install -r requirements-nogui.txt

WORKDIR /app

