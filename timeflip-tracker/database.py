import datetime
import os
import sys

import mariadb
from logger import get_logger
from metrics import cut_timeflip_facet_info

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

    timeflip_logger = get_logger()
    timeflip_logger.info(
        f"Connect to database with host {db_host}, port {db_port}, database {db_database}, user {db_user}, password *******"
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
    global database_cursor, database_connection
    query_string = "SELECT * FROM timeflip_events ORDER BY createdDate DESC LIMIT 1"

    try:
        database_cursor.execute(query_string)
    except mariadb.InterfaceError:
        # Initiate a reconnection if we lost it
        database_connection.reconnect()
        database_cursor = database_connection.cursor()

        database_cursor.execute(query_string)
    results = database_cursor.fetchall()

    return results[0] if len(results) == 1 else None


def insert_event(device_name, mac_addr, facet_num, facet_val):
    global database_connection, database_cursor
    cur_time = datetime.datetime.now()
    last_event = get_last_event()

    timeflip_logger = get_logger()
    timeflip_logger.info(
        f"Inserting New Event: {device_name} {mac_addr} {facet_num} {facet_val}"
    )

    timeflip_logger.debug(f"Last Event: {last_event}")

    if last_event:
        last_time = last_event[1]
        elapsed = cur_time - last_time
        duration = int(elapsed.total_seconds())
    else:
        duration = 0

    cut_timeflip_facet_info(
        cur_time.isoformat(), device_name, mac_addr, facet_num, facet_val
    )

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

    timeflip_logger.debug(f"Event insert statement:\n {insert_statement}")

    try:
        database_cursor.execute(insert_statement)
    except mariadb.InterfaceError:
        # Initiate a reconnection if we lost it
        database_connection.reconnect()
        database_cursor = database_connection.cursor()

        database_cursor.execute(insert_statement)

    database_connection.commit()
