# Copyright 2018 BACnet Gateway.  All rights reserved.

import os
import argparse
import sqlite3
import time
import datetime
import requests

idle_max = datetime.timedelta( days=7 )
stale_max = datetime.timedelta( minutes=30 )

log_filename = None


def update_cache():
    start_time = time.time()

    cur.execute( '''
        SELECT
            Cache.id, Addresses.address, Types.type, Cache.instance, Properties.property, Cache.update_timestamp, Cache.access_timestamp
        FROM Cache
            LEFT JOIN Addresses ON Cache.address_id=Addresses.id
            LEFT JOIN Types ON Cache.type_id=Types.id
            LEFT JOIN Properties ON Cache.property_id=Properties.id
    ''' )

    rows = cur.fetchall()

    n_deleted = 0
    n_updated = 0

    for row in rows:

        # Wait
        time.sleep( args.sleep_interval )

        # Calculate time intervals
        now = datetime.datetime.now()
        stale = now - datetime.datetime.fromtimestamp( row[5] )
        idle = now - datetime.datetime.fromtimestamp( row[6] )

        if idle > idle_max:

            # Entry has not been used; delete it
            cur.execute( 'DELETE FROM Cache WHERE id=?', ( row[0], ) )
            conn.commit()

            n_deleted += 1

        elif stale > stale_max:

            # Entry is stale; post request to update it
            post_request( row[1], row[2], row[3], row[4] )

            n_updated += 1

    if n_deleted or n_updated:
        log( 'Deleted ' + str( n_deleted ) + ' and updated ' + str( n_updated ) + ' of ' + str( len( rows ) ) + ' entries.  Elapsed time: ' + str( datetime.timedelta( seconds=int( time.time() - start_time ) ) ) )


def post_request( address, type, instance, property ):

    # Set up request arguments
    bg_args = {
        'address': address,
        'type': type,
        'instance': instance,
        'property': property,
        'live': True
    }

    # Issue request to BACnet Gateway
    url = 'http://' + args.hostname + ':' + str( args.port )
    requests.post( url, data=bg_args )


def log( msg ):

    # Format output line
    t = time.localtime()
    s = '[' + time.strftime( '%Y-%m-%d %H:%M:%S', t ) + '] ' + msg

    # Print to standard output
    print( s )

    # Optionally format new log filename
    global log_filename
    if not log_filename or not os.path.exists( log_filename ):
        log_filename = '../../bg_db/update_cache_' + time.strftime( '%Y-%m-%d_%H-%M-%S', t ) + '.log'

    # Open, write, and close log file
    logfile = open( log_filename , 'a' )
    logfile.write( s + '\n' )
    logfile.close()


if __name__ == '__main__':

    # Get list of running processes
    ps = os.popen( 'ps -elf' ).read()

    # Find out how many occurrences of this script are running
    dups = ps.count( __file__ )

    # If no other occurrences of this script are running, proceed to update cache
    if dups <= 1:

        db = '../../bg_db/cache.sqlite'

        # If database exists...
        if os.path.exists( db ):

            # Open database
            conn = sqlite3.connect( db )
            cur = conn.cursor()

            # Get command line arguments
            parser = argparse.ArgumentParser( description='Update cache of recently requested BACnet values', add_help=False )
            parser.add_argument( '-h', dest='hostname' )
            parser.add_argument( '-p', dest='port' )
            parser.add_argument( '-s', dest='sleep_interval', type=int )
            args = parser.parse_args()

            # Update cache continuously
            while True:
                update_cache()
