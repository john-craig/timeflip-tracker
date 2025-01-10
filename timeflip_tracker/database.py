import datetime
import os
import sys

import mariadb
from timeflip_tracker.logger import get_logger
from timeflip_tracker.metrics import cut_timeflip_facet_info

database_connection = None
database_cursor = None


def connect_database():
    global database_connection, database_cursor
    timeflip_logger = get_logger()
    db_host = os.getenv("MARIADB_HOST")
    db_port = os.getenv("MARIADB_PORT")
    db_user = os.getenv("MARIADB_USER")
    db_pass = os.getenv("MARIADB_PASSWORD")
    db_database = os.getenv("MARIADB_DATABASE")

    db_port = int(db_port) if db_port else 3306
    db_database = db_database if db_database else "timeflip"

    if db_host is None or db_user is None or db_pass is None:
        timeflip_logger.info("Unable to connect to database")
        return None

    database_connection = mariadb.connect(
        host=db_host, port=db_port, user=db_user, password=db_pass, database=db_database
    )

    timeflip_logger.info(
        f"Connect to database with host {db_host}, port {db_port}, database {db_database}, user {db_user}, password *******"
    )

    database_cursor = database_connection.cursor()

    database_cursor.execute(
        """CREATE TABLE IF NOT EXISTS timeflip_events (
        eventId INT NOT NULL AUTO_INCREMENT,
        createdDate DATETIME DEFAULT CURRENT_TIMESTAMP,
        modifiedDate DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        deviceName VARCHAR(255),
        macAddr CHAR(17),
        facetNum TINYINT,
        facetVal VARCHAR(255),
        facetRed TINYINT UNSIGNED,
        facetGreen TINYINT UNSIGNED ,
        facetBlue TINYINT UNSIGNED ,
        startTime DATETIME DEFAULT CURRENT_TIMESTAMP,
        endTime DATETIME DEFAULT 0,
        duration BIGINT AS (IF(endTime <> 0,
            TIMESTAMPDIFF(SECOND, startTime, endTime),
            TIMESTAMPDIFF(SECOND, startTime, CURRENT_TIMESTAMP)))
        VIRTUAL,
        PRIMARY KEY (eventId)
    )"""
    )

    return database_cursor


def close_database():
    global database_connection

    if database_connection is not None:
        database_connection.close()


def get_all_events():
    global database_cursor, database_connection

    if database_cursor is None or database_connection is None:
        return

    query_string = "SELECT * FROM timeflip_events"

    try:
        database_cursor.execute(query_string)
    except mariadb.InterfaceError:
        # Initiate a reconnection if we lost it
        database_connection.reconnect()
        database_cursor = database_connection.cursor()

        database_cursor.execute(query_string)

    timeflip_logger = get_logger()
    timeflip_logger.debug(f"Database Dump:\n {database_cursor.fetchall()}")


def get_prev_event():
    global database_cursor, database_connection
    query_string = "SELECT * FROM timeflip_events ORDER BY createdDate DESC LIMIT 1"

    if database_cursor is None or database_connection is None:
        return

    try:
        database_cursor.execute(query_string)
    except mariadb.InterfaceError:
        # Initiate a reconnection if we lost it
        database_connection.reconnect()
        database_cursor = database_connection.cursor()

        database_cursor.execute(query_string)
    results = database_cursor.fetchall()

    return results[0] if len(results) == 1 else None


def update_event_end(event_id, end_time):
    global database_connection, database_cursor

    if database_cursor is None or database_connection is None:
        return

    update_statement = f"""
        UPDATE timeflip_events
        SET endTime = '{end_time}'
        WHERE eventId = {event_id}
    """

    timeflip_logger = get_logger()
    timeflip_logger.debug(f"Event update statement:\n {update_statement}")

    try:
        database_cursor.execute(update_statement)
    except mariadb.InterfaceError:
        # Initiate a reconnection if we lost it
        database_connection.reconnect()
        database_cursor = database_connection.cursor()

        database_cursor.execute(update_statement)


def insert_event(device_name, mac_addr, facet_num, facet_val, facet_color):
    global database_connection, database_cursor

    if database_cursor is None or database_connection is None:
        return

    cur_time = datetime.datetime.now()
    prev_event = get_prev_event()

    timeflip_logger = get_logger()
    timeflip_logger.info(
        f"Inserting New Event: {device_name} {mac_addr} {facet_num} {facet_val}"
    )

    timeflip_logger.debug(f"Last Event: {prev_event}")

    if prev_event:
        if (
            prev_event[3] == device_name
            and prev_event[4] == mac_addr
            and prev_event[5] == facet_num
            and prev_event[6] == facet_val
        ):
            timeflip_logger.info(
                "Even has same activity as previous event; not inserting"
            )
            return

        prev_id = prev_event[0]
        update_event_end(prev_id, cur_time.isoformat())

    cut_timeflip_facet_info(
        cur_time.isoformat(), device_name, mac_addr, facet_num, facet_val
    )

    insert_statement = f"""
        INSERT INTO timeflip_events
            (deviceName, macAddr,
            facetNum, facetVal,
            facetRed, facetGreen, facetBlue)
        VALUES (
            '{device_name}',
            '{mac_addr}',
            {facet_num},
            '{facet_val}',
            {facet_color[0]},
            {facet_color[1]},
            {facet_color[2]}
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
