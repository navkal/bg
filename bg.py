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
                start_time FLOAT,
                completed INTEGER,
                completion_time FLOAT,
                request TEXT
            );

        ''');

        cur.execute( '''INSERT OR IGNORE INTO Constants ( min_delay_sec, max_poll_sec ) VALUES (?,?)''', ( 0.1, 3.0 ) )
        cur.execute( '''INSERT OR IGNORE INTO Requests ( start_time, completed, completion_time, request ) VALUES (?,?,?,?)''', ( 0, 1, 0, 'dummy' ) )
        conn.commit()


def bacnet_read( config_args, target_args ):

    # Create entry representing current request
    start_time = time.time()
    cur.execute( '''INSERT OR IGNORE INTO Requests ( start_time, completed, completion_time, request ) VALUES (?,?,?,?)''', ( start_time, 0, 0, 'tbd' ) )
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

    # Poll until previous request has completed (or until we reach timeout condition)
    abort_poll_time = time.time() + max_poll_sec
    prev_rq_id = this_rq_id - 1
    do_poll = True
    prev_completed = False
    timed_out = False

    while do_poll:
        # Determine whether predecessor has completed
        cur.execute( 'SELECT completed FROM Requests WHERE id=?', ( prev_rq_id, ) )
        prev_completed = cur.fetchone()[0]

        # Determine whether to continue polling
        timed_out = time.time() >= abort_poll_time
        do_poll = ( not prev_completed ) and ( not timed_out )

        # If continuing to poll, sleep a little first
        if do_poll:
            time.sleep( min_delay_sec )
            slept_2 = True

    # If previous request has completed, enforce minimum delay
    if prev_completed:
        cur.execute( 'SELECT completion_time FROM Requests WHERE id=?', ( prev_rq_id, ) )
        prev_completion_time = cur.fetchone()[0]
        sleep_sec = prev_completion_time + min_delay_sec - time.time()
        if sleep_sec > 0:
            time.sleep( sleep_sec )
            slept_3 = True
    else:
        # Previous request has not completed; artificially set the completed flag so it is not counted against the backlog
        cur.execute( 'UPDATE Requests SET completed=1 WHERE id=?', ( prev_rq_id, ) )
        conn.commit()

    # Remove predecessor entry from table
    # --> Commented out until further notice -->
    # cur.execute( 'DELETE FROM Requests WHERE id=?', ( prev_rq_id, ) )
    # <-- Commented out until further notice <--

    # Issue the BACnet request
    rsp = br.read( config_args, target_args )

    # Update request entry in database.  (It will no longer exist if successor has deleted it due to timeout.)
    completion_time = time.time()
    cur.execute( 'UPDATE Requests SET completed=?, completion_time=? WHERE id=?', ( 1, completion_time, this_rq_id, ) )
    conn.commit()

    # Add debug info to response
    rsp['elapsed_ms'] = round( ( completion_time - start_time ) * 1000 )
    rsp['slept'] = [slept_1, slept_2, slept_3]
    rsp['timed_out'] = timed_out

    rsp = collections.OrderedDict( sorted( rsp.items() ) )

    return rsp


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description='Propagate a BACnet read request from the BACnet Gateway to a BACnet agent' )
    parser.add_argument('-t', dest='tbd',  help='tbd')
    args = parser.parse_args()

    try:
        open_db()
    except:
        dc_rsp = { 'error': 'open_db() failed' }
    else:
        try:

            config_args = {
                'objectName': 'Betelgeuse',
                'address': '10.4.241.1',
                'objectIdentifier': 599,
                'maxApduLengthAccepted': 1024,
                'segmentationSupported': 'segmentedBoth',
                'vendorIdentifier': 15,
                'foreignBBMD': '128.253.109.254',
                'foreignTTL': 30,
            }

            target_args = {
                'address': '10.12.0.250',
                'type': 'analogInput',
                'instance': '3006238',
                'property': 'presentValue'
            }

            dc_rsp = bacnet_read( config_args, target_args )
        except:
            dc_rsp = { 'error': 'bacnet_read() failed' }

    s_rsp = json.dumps( dc_rsp )
    print( s_rsp )
