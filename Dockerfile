FROM python:3.12-slim

COPY timeflip-tracker /opt

COPY requirements.txt /opt

RUN pip install -r /opt/requirements.txt
