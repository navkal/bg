# Copyright 2018 BACnet Gateway.  All rights reserved.

import os
import sqlite3
import time



def open_db():

    db = '../bg_db/clients.sqlite'

    # Optionally remove database
    if ( args.remove ):
        try:
            os.remove( db )
        except:
            pass

    # Determine whether database exists
    db_exists = os.path.exists( db )

    # Connect to database
    conn = sqlite3.connect( db )
    cur = conn.cursor()

    if not db_exists:

        # Initialize database
        cur.executescript('''
            CREATE TABLE IF NOT EXISTS Clients (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                remote_address TEXT,
                http_x_forwarded_for TEXT,
                access_count INTEGER,
                first_access_timestamp INTEGER,
                last_access_timestamp INTEGER
            );
        ''')

        conn.commit()

    return conn, cur


def track_client():

    # Test whether entry already exists
    cur.execute( 'SELECT id FROM Clients WHERE remote_address=? AND http_x_forwarded_for=?', ( args.ip, args.fwd_ip ) )
    row = cur.fetchone()

    # Get current time
    timestamp = int( time.time() )

    if row:

        # Entry exists; update it
        cur.execute( 'UPDATE Clients SET access_count=access_count+1, last_access_timestamp=? WHERE id=?', ( timestamp, row[0] ) )

    else:

        # Entry does not exist; insert it
        cur.execute( 'INSERT INTO Clients ( remote_address, http_x_forwarded_for, access_count, first_access_timestamp, last_access_timestamp ) VALUES (?,?,?,?,?)', ( args.ip, args.fwd_ip, 1, timestamp, timestamp ) )

    conn.commit()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser( description='Track BACnet Gateway clients' )
    parser.add_argument( '-i', dest='ip', help='Remote IP address' )
    parser.add_argument( '-f', dest='fwd_ip', help='Forwarded for IP address' )
    parser.add_argument( '-r', dest='remove', action='store_true', help='Remove database' )
    args = parser.parse_args()

    conn, cur = open_db()
    track_client()
