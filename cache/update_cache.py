# Copyright 2018 BACnet Gateway.  All rights reserved.

import os
import argparse
import sqlite3
import time
from datetime import timedelta
import requests
import json

import sys
sys.path.append( '../live' )
import bg


log_filename = None


def update_cache():

    cur.execute( '''
        SELECT
            Cache.id, Addresses.address, Types.type, Cache.instance, Properties.property
        FROM Cache
            LEFT JOIN Addresses ON Cache.address_id=Addresses.id
            LEFT JOIN Types ON Cache.type_id=Types.id
            LEFT JOIN Properties ON Cache.property_id=Properties.id
    ''' )
    rows = cur.fetchall()

    for row in rows:
        time.sleep( args.sleep_interval )
        print( row )
        value, units = get_value( row[1], row[2], row[3], row[4] )
        print( value, units )


def get_value( address, type, instance, property ):

    value = None
    units = None

    # Set up request arguments
    bg_args = {
        'address': address,
        'type': type,
        'instance': instance,
        'property': property,
        'live': True
    }

    # Issue request to HTTP service
    url = 'http://' + args.hostname + ':' + str( args.port )
    bg_rsp = requests.post( url, data=bg_args )

    # Convert JSON response to Python dictionary
    dc_rsp = json.loads( bg_rsp.text )

    # Extract BACnet response from the dictionary
    bn_rsp = dc_rsp['bacnet_response']

    # Extract result from BACnet response
    if ( bn_rsp['success'] ):

        data = bn_rsp['data']

        if data['success']:
            value = data['presentValue']
            units = data['units']

    return value, units



def log( msg ):

    # Format output line
    t = time.localtime()
    s = '[' + time.strftime( '%Y-%m-%d %H:%M:%S', t ) + '] ' + msg

    # Print to standard output
    print( s )

    # Optionally format new log filename
    global log_filename
    if not log_filename or not os.path.exists( log_filename ):
        log_filename = '../../bgt_db/load_cache_' + time.strftime( '%Y-%m-%d_%H-%M-%S', t ) + '.log'

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

            # Get command line arguments
            parser = argparse.ArgumentParser( description='Update cache of recently requested BACnet values', add_help=False )
            parser.add_argument( '-h', dest='hostname' )
            parser.add_argument( '-p', dest='port' )
            parser.add_argument( '-s', dest='sleep_interval', type=int )
            args = parser.parse_args()

            # Open database
            conn = sqlite3.connect( db )
            cur = conn.cursor()

            # Update cache continuously
            while True:
                start_time = time.time()
                update_cache()
                log( 'Updated all values.  Elapsed time: ' + str( timedelta( seconds=int( time.time() - start_time ) ) ) )
