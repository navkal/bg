# Copyright 2018 BACnet Gateway.  All rights reserved.

import os
import sqlite3
import datetime



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
                REMOTE_ADDR TEXT,
                HTTP_X_FORWARDED_FOR TEXT,
                REMOTE_PORT TEXT,
                HTTP_REFERER TEXT,
                REQUEST_METHOD TEXT,
                QUERY_STRING TEXT,
                REQUEST_URI TEXT,
                access_count INTEGER,
                access_time_1 TEXT,
                access_time_n TEXT,
                REQUEST_TIME_1 INTEGER,
                REQUEST_TIME_n INTEGER
            );
        ''')

        conn.commit()

    return conn, cur


def track_client():

    # Test whether entry already exists
    cur.execute( 'SELECT id FROM Clients WHERE REMOTE_ADDR=? AND HTTP_X_FORWARDED_FOR=? AND REMOTE_PORT=?', ( args.REMOTE_ADDR, args.HTTP_X_FORWARDED_FOR, args.REMOTE_PORT ) )
    row = cur.fetchone()

    access_time = datetime.datetime.fromtimestamp( args.REQUEST_TIME ).strftime('%Y-%m-%d %H:%M:%S')

    if row:

        # Entry exists; update it
        cur.execute( 'UPDATE Clients SET access_count=access_count+1, access_time_n=?, REQUEST_TIME_n=? WHERE id=?', ( access_time, args.REQUEST_TIME, row[0] ) )

    else:

        # Entry does not exist; insert it
        cur.execute( '''

            INSERT INTO Clients (
                REMOTE_ADDR,
                HTTP_X_FORWARDED_FOR,
                REMOTE_PORT,
                HTTP_REFERER,
                REQUEST_METHOD,
                QUERY_STRING,
                REQUEST_URI,
                access_count,
                access_time_1,
                access_time_n,
                REQUEST_TIME_1,
                REQUEST_TIME_n
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)

            ''', (
                args.REMOTE_ADDR,
                args.HTTP_X_FORWARDED_FOR,
                args.REMOTE_PORT,
                args.HTTP_REFERER,
                args.REQUEST_METHOD,
                args.QUERY_STRING,
                args.REQUEST_URI,
                1,
                access_time,
                access_time,
                args.REQUEST_TIME,
                args.REQUEST_TIME
                )
        )

    conn.commit()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser( description='Track BACnet Gateway clients' )
    parser.add_argument( '--REMOTE_ADDR', dest='REMOTE_ADDR' )
    parser.add_argument( '--HTTP_X_FORWARDED_FOR', dest='HTTP_X_FORWARDED_FOR' )
    parser.add_argument( '--REMOTE_PORT', dest='REMOTE_PORT' )
    parser.add_argument( '--HTTP_REFERER', dest='HTTP_REFERER' )
    parser.add_argument( '--REQUEST_METHOD', dest='REQUEST_METHOD' )
    parser.add_argument( '--QUERY_STRING', dest='QUERY_STRING' )
    parser.add_argument( '--REQUEST_URI', dest='REQUEST_URI' )
    parser.add_argument( '--REQUEST_TIME', dest='REQUEST_TIME', type=int )
    parser.add_argument( '-r', dest='remove', action='store_true' )
    args = parser.parse_args()

    conn, cur = open_db()
    track_client()
