# Copyright 2018 Building Energy Gateway.  All rights reserved.

import argparse
import sqlite3
import os
import time
import collections
import json
import br


_statistics = 0

db = '../bg_db/queue.sqlite'
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
                request TEXT,
                response TEXT
            );

        ''');

        cur.execute( '''INSERT OR IGNORE INTO Constants ( min_delay_sec, max_poll_sec ) VALUES (?,?)''', ( 1.5, 5.0 ) )
        cur.execute( '''INSERT OR IGNORE INTO Requests ( start_time, completed, completion_time, request, response ) VALUES (?,?,?,?,?)''', ( 0, 1, 0, 'dummy', '' ) )
        conn.commit()


def sync_request( target_args ):

    # Create entry representing current request
    start_time = time.time()
    property = target_args['property']
    cmd = 'read ' + target_args['address'] + ' ' + target_args['type'] + ' ' + str( target_args['instance'] ) + ' ' + property
    cur.execute( '''INSERT OR IGNORE INTO Requests ( start_time, completed, completion_time, request, response ) VALUES (?,?,?,?,?)''', ( start_time, 0, 0, cmd, '' ) )
    this_rq_id = cur.lastrowid
    conn.commit()

    # Count the backlog
    cur.execute( 'SELECT COUNT(*) FROM Requests WHERE id<? AND completed=0', ( this_rq_id, ) )
    n_backlog = cur.fetchone()[0] - 1

    # Get timing constants
    cur.execute( 'SELECT min_delay_sec, max_poll_sec FROM Constants' )
    rows = cur.fetchall()
    row = rows[0]
    min_delay_sec = 0.1 if br._standalone else row[0]
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
    cur.execute( 'DELETE FROM Requests WHERE id=?', ( prev_rq_id, ) )

    # Issue the BACnet request
    try:
        rsp_data = br.read_property( target_args )
    except Exception as e:
        rsp_data = { 'success': False, 'message': 'br.read_property() encountered exception: ' + str(e), property: '', 'units': '' }


    # Update request entry in database.  (It will no longer exist if successor has deleted it due to timeout.)
    completion_time = time.time()
    cur.execute( 'UPDATE Requests SET completed=?, completion_time=?, response=? WHERE id=?', ( 1, completion_time, str( rsp_data[property] ) + ' ' + rsp_data['units'], this_rq_id, ) )
    conn.commit()

    # Build the response
    rsp = {}
    rsp['data'] = collections.OrderedDict( sorted( rsp_data.items() ) )
    rsp['success'] = True
    rsp['message'] = ''
    if _statistics:
        rsp_stats = {}
        rsp_stats['response_time'] = str( round( ( completion_time - start_time ) * 1000 ) ) + ' ms'
        rsp_stats['slept'] = [slept_1, slept_2, slept_3]
        rsp_stats['timed_out'] = timed_out
        rsp['statistics'] = collections.OrderedDict( sorted( rsp_stats.items() ) )
    rsp = collections.OrderedDict( sorted( rsp.items() ) )

    return rsp


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description='Propagate a BACnet read request from the Building Energy Gateway to a BACnet agent' )
    parser.add_argument( '-a', dest='address',  help='Target IP address' )
    parser.add_argument( '-t', dest='type',  help='Target type' )
    parser.add_argument( '-i', dest='instance',  help='Target instance' )
    parser.add_argument( '-p', dest='property',  help='Target property' )

    args = parser.parse_args()


    try:
        open_db()

    except:
        dc_rsp = { 'success': False, 'message': 'bg.open_db() failed' }

    else:

        try:

            target_args = {
                'address': args.address,
                'type': args.type,
                'instance': int( args.instance ),
                'property': args.property
            }

            dc_rsp = sync_request( target_args )

        except:
            dc_rsp = { 'success': False, 'message': 'bg.sync_request() failed' }

    s_rsp = json.dumps( dc_rsp )
    print( s_rsp )
