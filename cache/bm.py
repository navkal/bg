# Copyright 2018 BACnet Gateway.  All rights reserved.

import os
import argparse
import time
import sqlite3
import collections
import json

# Retrieve value from Building Monitor cache

db = '../bgt_db/cache.sqlite'

bm_msg = None

if os.path.exists( db ):

    # Get arguments
    parser = argparse.ArgumentParser( description='Get value and units from cache' )
    parser.add_argument( '-f', dest='facility' )
    parser.add_argument( '-i', dest='instance' )
    args = parser.parse_args()

    if args.facility and args.instance:
        start_time = time.time()

        # Connect to the database
        conn = sqlite3.connect( db )
        cur = conn.cursor()

        cur.execute( '''
            SELECT facility, instance, value, units, timestamp
            FROM Cache
                LEFT JOIN Facilities ON Cache.facility_id=Facilities.id
                LEFT JOIN Units ON Cache.units_id=Units.id
            WHERE Facilities.facility=? and Cache.instance=?
        ''', ( args.facility, args.instance )
        )

        row = cur.fetchone()
        if row:

            rsp_data = { 'success': True, 'facility': row[0], 'instance': row[1], 'presentValue': row[2], 'units': row[3], 'timestamp': int( row[4] * 1000 ) }

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
            bm_msg = 'No data'
    else:
        bm_msg = 'Missing argument(s)'
else:
    bm_msg = 'No cache'


if bm_msg:
    bm_rsp = { 'success': False, 'message': bm_msg }
else:
    bm_rsp = rsp

# Return result
print( json.dumps( bm_rsp ) )
