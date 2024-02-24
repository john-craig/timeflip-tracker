FROM python:3.10

WORKDIR /app

COPY timeflip-tracker/ /app/timeflip-tracker

COPY requirements.txt /app

COPY config.yaml /etc/timeflip-tracker/

RUN pip install -r requirements.txt

VOLUME /var/run/dbus/

# VOLUME /etc/timeflip-tracker

ENTRYPOINT ["python", "-u", "timeflip-tracker/main.py"]
