# Copyright 2018 BACnet Gateway.  All rights reserved.

import time
import os
import argparse
import sqlite3
import collections
import json
import cache_db


_statistics = 0

start_time = time.time()
msg = None


db = '../bg_db/cache.sqlite'

if os.path.exists( db ):

    # Get arguments
    parser = argparse.ArgumentParser( description='Get BACnet value from cache' )
    parser.add_argument( '-a', dest='address' )
    parser.add_argument( '-t', dest='type' )
    parser.add_argument( '-i', dest='instance' )
    parser.add_argument( '-p', dest='property' )
    args = parser.parse_args()

    # Connect to the database
    conn = sqlite3.connect( db )
    cur = conn.cursor()

    # Retrieve value, units, and timestamp from cache
    cache_value = cache_db.get_cache_value( args.address, args.type, args.instance, args.property, cur, conn )

    if cache_value:

        # Collect data
        # rsp_data = { 'address': args.address, 'type': args.type, 'instance': args.instance, 'property': args.property }
        rsp_data = { 'type': args.type, 'instance': args.instance, 'property': args.property } # Omit address for security purposes
        rsp_data[args.property] = cache_value['value']
        rsp_data['units'] = cache_value['units']
        rsp_data['timestamp'] = cache_value['timestamp']
        rsp_data['success'] = True
        rsp_data['message'] = ''

        # Build the response
        rsp = {}
        rsp['data'] = collections.OrderedDict( sorted( rsp_data.items() ) )
        rsp['success'] = True
        rsp['message'] = ''
        if _statistics:
            rsp_stats = {}
            rsp_stats['response_time'] = str( round( ( time.time() - start_time ) * 1000 ) ) + ' ms'
            rsp_stats['slept'] = [False, False, False]
            rsp_stats['timed_out'] = False
            rsp['statistics'] = collections.OrderedDict( sorted( rsp_stats.items() ) )
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
