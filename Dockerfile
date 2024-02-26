FROM python:3.10

WORKDIR /app

COPY requirements.txt /app

#COPY config.yaml /etc/timeflip-tracker/

RUN pip install -r requirements.txt

COPY timeflip-tracker/ /app/timeflip-tracker

VOLUME /var/run/dbus/

VOLUME /etc/timeflip-tracker/

ENTRYPOINT ["python", "timeflip-tracker/main.py"]
