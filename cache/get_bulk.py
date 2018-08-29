# Copyright 2018 BACnet Gateway.  All rights reserved.

import time
import os
import argparse
import sqlite3
import collections
import json

start_time = time.time()
msg = None

db = '../bg_db/cache.sqlite'

if os.path.exists( db ):

    # Get arguments
    parser = argparse.ArgumentParser( description='Get multiple BACnet values from cache' )
    parser.add_argument( '-b', dest='bulk_request' )
    args = parser.parse_args()

    if args.bulk_request:
        bulk_request = args.bulk_request.replace( "'", '"' )

        print( bulk_request )
        exit()







    # Connect to the database
    conn = sqlite3.connect( db )
    cur = conn.cursor()

    # Read cache
    cur.execute( '''
        SELECT
            Cache.id, Cache.value, Units.units, Cache.update_timestamp
        FROM Cache
            LEFT JOIN Addresses ON Cache.address_id=Addresses.id
            LEFT JOIN Types ON Cache.type_id=Types.id
            LEFT JOIN Properties ON Cache.property_id=Properties.id
            LEFT JOIN Units ON Cache.units_id = Units.id
        WHERE ( Addresses.address=? AND Types.type=? AND Cache.instance=? AND Properties.property=? );
    ''', ( args.address, args.type, args.instance, args.property )
    )
    row = cur.fetchone()

    if row:
        # Update access timestamp
        cur.execute( 'UPDATE Cache SET access_timestamp=? WHERE id=?', ( round( time.time() ), row[0] ) )
        conn.commit()

        # Collect data
        rsp_data = { 'address': args.address, 'type': args.type, 'instance': args.instance, 'property': args.property }
        rsp_data[args.property] = row[1]
        rsp_data['units'] = row[2]
        rsp_data['timestamp'] = row[3] * 1000
        rsp_data['success'] = True
        rsp_data['message'] = ''

        # Collect debug info
        rsp_debug = {}
        rsp_debug['response_time'] = str( round( ( time.time() - start_time ) * 1000 ) ) + ' ms'
        rsp_debug['slept'] = [False, False, False]
        rsp_debug['timed_out'] = False

        # Build the response
        rsp = {}
        rsp['data'] = collections.OrderedDict( sorted( rsp_data.items() ) )
        rsp['debug'] = collections.OrderedDict( sorted( rsp_debug.items() ) )
        rsp['success'] = True
        rsp['message'] = ''
        rsp = collections.OrderedDict( sorted( rsp.items() ) )

    else:
        msg = 'No data'

else:
    msg = 'No cache'


if msg:
    cache_rsp = { 'success': False, 'message': msg }
else:
    cache_rsp = rsp

# Return result
print( json.dumps( cache_rsp ) )
