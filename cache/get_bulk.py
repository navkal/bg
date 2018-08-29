# Copyright 2018 BACnet Gateway.  All rights reserved.

import time
import os
import argparse
import sqlite3
import collections
import json

start_time = time.time()

msg = None
rsp = []

db = '../bg_db/cache.sqlite'

if os.path.exists( db ):

    # Get arguments
    parser = argparse.ArgumentParser( description='Get multiple BACnet values from cache' )
    parser.add_argument( '-b', dest='bulk_request' )
    args = parser.parse_args()

    if args.bulk_request:

        # Extract request
        bulk_rq = json.loads( args.bulk_request.replace( "'", '"' ) )

        # Traverse bulk request
        for rq in bulk_rq:
            print( rq )
            rsp.append( rq )

        # Connect to the database
        conn = sqlite3.connect( db )
        cur = conn.cursor()



if msg:
    bulk_rsp = { 'success': False, 'message': msg }
else:
    bulk_rsp = rsp

# Return result
print( json.dumps( bulk_rsp ) )
