# Copyright 2018 BACnet Gateway.  All rights reserved.

import argparse
import sqlite3
import os
import time
import collections
import json
import br


db = 'bg.sqlite'
conn = None
cur = None



def open_db():

    global conn
    global cur

    db_exists = os.path.exists( db )

    conn = sqlite3.connect( db )
    cur = conn.cursor()

    if not db_exists:

        cur.executescript('''

            CREATE TABLE IF NOT EXISTS Constants (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                min_delay_sec FLOAT,
                max_poll_sec FLOAT
            );

            CREATE TABLE IF NOT EXISTS Requests (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                completed INTEGER,
                completion_time FLOAT,
                request TEXT
            );

        ''');

        cur.execute( '''INSERT OR IGNORE INTO Constants ( min_delay_sec, max_poll_sec ) VALUES (?,?)''', ( 0.1, 3.0 ) )
        cur.execute( '''INSERT OR IGNORE INTO Requests ( completed, completion_time, request ) VALUES (?,?,?)''', ( 1, 0, 'dummy' ) )
        conn.commit()


def bacnet_read( args ):

    # Create entry representing current request
    cur.execute( '''INSERT OR IGNORE INTO Requests ( completed, completion_time, request ) VALUES (?,?,?)''', ( 0, 0, 'request received at ' + str( time.time() ) ) )
    this_rq_id = cur.lastrowid
    conn.commit()

    # Count the backlog
    cur.execute( 'SELECT COUNT(*) FROM Requests WHERE id<? AND completed=0', ( this_rq_id, ) )
    n_backlog = cur.fetchone()[0] - 1

    # Get timing constants
    cur.execute( 'SELECT min_delay_sec, max_poll_sec FROM Constants' )
    rows = cur.fetchall()
    row = rows[0]
    min_delay_sec = row[0]
    max_poll_sec = row[1]

    slept_1 = slept_2 = slept_3 = False

    # If there is a backlog, take a nap before starting to poll
    if n_backlog > 0:
        time.sleep( min_delay_sec * n_backlog )
        slept_1 = True

    # Poll until previous request has completed (or timeout)
    abort_poll_time = time.time() + max_poll_sec
    prev_rq_id = this_rq_id - 1

    timed_out = False
    prev_completed = 0
    do_poll = prev_completed == 0 and time.time() < abort_poll_time
    while do_poll:
        cur.execute( 'SELECT completed FROM Requests WHERE id=?', ( prev_rq_id, ) )
        prev_completed = cur.fetchone()[0]
        timed_out = time.time() >= abort_poll_time
        do_poll = prev_completed == 0 and not timed_out
        if do_poll:
            time.sleep( min_delay_sec )
            slept_2 = True

    if prev_completed == 0:
        # Previous request has not completed; artificially set the completed flag
        cur.execute( 'UPDATE Requests SET completed=1 WHERE id=?', ( prev_rq_id, ) )
        conn.commit()
    else:
        # Previous request has completed; enforce minimum delay
        cur.execute( 'SELECT completion_time FROM Requests WHERE id=?', ( prev_rq_id, ) )
        prev_completion_time = cur.fetchone()[0]
        sleep_sec = prev_completion_time + min_delay_sec - time.time()
        if sleep_sec > 0:
            time.sleep( sleep_sec )
            slept_3 = True

        # Remove previous request from table
        cur.execute( 'DELETE FROM Requests WHERE id=?', ( prev_rq_id, ) )

    # Issue the BACnet request
    rsp = br.read( args )

    # Update request entry in database
    completion_time = time.time()
    cur.execute( 'UPDATE Requests SET completed=?, completion_time=? WHERE id=?', ( 1, completion_time, this_rq_id, ) )
    conn.commit()

    # Add debug info to response
    rsp['completion_time'] = completion_time
    rsp['slept_1'] = slept_1
    rsp['slept_2'] = slept_2
    rsp['slept_3'] = slept_3
    rsp['timed_out'] = timed_out

    rsp = collections.OrderedDict( sorted( rsp.items() ) )

    return rsp


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description='Propagate a BACnet read request from the BACnet Gateway to a BACnet agent' )
    parser.add_argument('-t', dest='tbd',  help='tbd')
    args = parser.parse_args()

    open_db()
    dict_bacnet_response = bacnet_read( args )

    json_bacnet_response = json.dumps( dict_bacnet_response )
    print( json_bacnet_response )
