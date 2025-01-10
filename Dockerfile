FROM python:3.10

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY timeflip_tracker/ /app/timeflip_tracker

VOLUME /var/run/dbus/

VOLUME /etc/timeflip-tracker/

ENTRYPOINT ["python", "-u", "timeflip_tracker/main.py"]
