# Copyright 2018 BACnet Gateway.  All rights reserved.

import os
import argparse
import sqlite3
import time
import json



db = '../bg_db/cache.sqlite'

if os.path.exists( db ):

    # Get arguments
    parser = argparse.ArgumentParser( description='Get BACnet value from cache' )
    parser.add_argument( '-a', dest='address' )
    parser.add_argument( '-t', dest='type' )
    parser.add_argument( '-i', dest='instance' )
    parser.add_argument( '-p', dest='property' )
    args = parser.parse_args()

    cached_value = { 'address': args.address, 'type': args.type, 'instance': args.instance, 'requestedProperty': args.property }

    # Connect to the database
    conn = sqlite3.connect( db )
    cur = conn.cursor()

    # Read cache
    cur.execute( '''
        SELECT
            Cache.id, Cache.value, Units.units
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
        cur.execute( 'UPDATE Cache SET access_timestamp=? WHERE id=?', ( int( time.time() ), row[0] ) )

        # Build return value
        cached_value[args.property] = row[1]
        cached_value['units'] = row[2]
        cached_value['success'] = True
        cached_value['message'] = ''
    else:
        cached_value['success'] = False
        cached_value['message'] = 'Requested value not found in cache'

# Return result
print( json.dumps( cached_value ) )
