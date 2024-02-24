import datetime
import os
import sys

import mariadb

database_connection = None
database_cursor = None


def connect_database():
    global database_connection, database_cursor
    db_host = os.getenv("MARIADB_HOST")
    db_port = os.getenv("MARIADB_PORT")
    db_user = os.getenv("MARIADB_USER")
    db_pass = os.getenv("MARIADB_PASSWORD")
    db_database = os.getenv("MARIADB_DATABASE")

    db_port = int(db_port) if db_port else 3306
    db_database = db_database if db_database else "timeflip"

    database_connection = mariadb.connect(
        host=db_host, port=db_port, user=db_user, password=db_pass, database=db_database
    )

    database_cursor = database_connection.cursor()

    database_cursor.execute(
        """CREATE TABLE IF NOT EXISTS timeflip_events (
        eventId INT NOT NULL AUTO_INCREMENT,
        createdDate DATETIME,
        deviceName VARCHAR(255),
        macAddr CHAR(17),
        facetNum TINYINT,
        facetVal VARCHAR(255),
        duration BIGINT,
        PRIMARY KEY (eventId)
    )"""
    )

    return database_cursor


def close_database():
    global database_connection
    database_connection.close()


def get_last_event():
    global database_cursor
    database_cursor.execute(
        "SELECT * FROM timeflip_events ORDER BY createdDate DESC LIMIT 1"
    )
    results = database_cursor.fetchall()

    return results[0] if len(results) == 1 else None


def insert_event(device_name, mac_addr, facet_num, facet_val):
    global database_connection, database_cursor
    cur_time = datetime.datetime.now()
    last_event = get_last_event()

    if last_event:
        last_time = last_event[1]
        elapsed = cur_time - last_time
        duration = int(elapsed.total_seconds())
    else:
        duration = 0

    insert_statement = f"""
        INSERT INTO timeflip_events
            (createdDate, deviceName, macAddr,
            facetNum, facetVal, duration)
        VALUES (
            '{cur_time.isoformat()}',
            '{device_name}',
            '{mac_addr}',
            {facet_num},
            '{facet_val}',
            {duration}
        )
    """

    print(insert_statement)

    res = database_cursor.execute(insert_statement)
    database_connection.commit()
