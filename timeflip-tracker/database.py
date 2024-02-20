import datetime
import os
import sys

import mariadb


def connect_database():
    db_host = os.getenv("MARIADB_HOST")
    db_port = os.getenv("MARIADB_PORT")
    db_user = os.getenv("MARIADB_USER")
    db_pass = os.getenv("MARIADB_PASS")

    connection = mariadb.connect(
        host=db_host, port=db_port, user=db_user, password=db_pass
    )

    cursor = connection.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS timeflip_events (
        eventId INT NOT NULL AUTO_INCREMENT,
        createdDate DATETIME,
        deviceName VARCHAR(255),
        macAddr CHAR(15),
        facetNum TINYINT,
        facetVal VARCHAR(255),
        duration BIGINT,
        PRIMARY KEY (eventId)
    )"""
    )


def get_last_event():
    pass


def insert_event(device_name, mac_addr, facet_num, facet_val):
    cur_time = datetime.datetime.now()
    last_event = get_last_event()

    last_time = datetime.datetime.fromisoformat(last_event["createdDate"])

    elapsed = last_time - cur_time
    duration = elapsed.total_seconds()
