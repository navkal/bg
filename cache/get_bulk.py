# Copyright 2018 BACnet Gateway.  All rights reserved.

import time
import os
import argparse
import csv
import socket
import struct
import sqlite3
import json

start_time = time.time()

bulk_rsp = []

db = '../bg_db/cache.sqlite'

if os.path.exists( db ):

    # Get arguments
    parser = argparse.ArgumentParser( description='Get multiple BACnet values from cache' )
    parser.add_argument( '-b', dest='bulk_request' )
    args = parser.parse_args()

    if args.bulk_request:

        # Extract request
        bulk_rq = json.loads( args.bulk_request.replace( "'", '"' ) )

        if len( bulk_rq ):

            # Build facility-to-address mapping
            fac_addr_map = {}

            with open( 'agents.csv', newline='' ) as csvfile:
                reader = csv.reader( csvfile )

                first = True

                for agent_row in reader:

                    # Skip empty and comment lines
                    if ( len( agent_row ) > 0 ) and not agent_row[0].startswith( '#' ):

                        if first:
                            # Get prefix from first line
                            prefix = agent_row[0].strip()
                            first = False
                        else:
                            # Add map entry
                            facility = agent_row[0].strip()
                            address = socket.inet_ntoa( struct.pack( '>L', int( prefix + agent_row[1].strip(), 16 ) ) )
                            fac_addr_map[facility] = address


            # Connect to the database
            conn = sqlite3.connect( db )
            cur = conn.cursor()

            # Build response
            for rq in bulk_rq:

                # Validate instance
                if ( 'instance' in rq ) and str( rq['instance'] ).isdigit() and ( int( rq['instance'] ) > 0 ):

                    # Map facility to address
                    if 'facility' in rq and rq['facility'] in fac_addr_map:
                        rq['address'] = fac_addr_map[rq['facility']]

                    # Set default type
                    if 'type' not in rq:
                        rq['type'] = 'analogInput'

                    # Set default property
                    if 'property' not in rq:
                        rq['property'] = 'presentValue'

                    # Read cache
                    cur.execute( '''
                        SELECT
                            Cache.value, Units.units, Cache.update_timestamp
                        FROM Cache
                            LEFT JOIN Addresses ON Cache.address_id=Addresses.id
                            LEFT JOIN Types ON Cache.type_id=Types.id
                            LEFT JOIN Properties ON Cache.property_id=Properties.id
                            LEFT JOIN Units ON Cache.units_id = Units.id
                        WHERE ( Addresses.address=? AND Types.type=? AND Cache.instance=? AND Properties.property=? );
                    ''', ( rq['address'], rq['type'], rq['instance'], rq['property'] )
                    )
                    row = cur.fetchone()
                    if row:
                        rq[rq['property']] = row[0]
                        rq['units'] = row[1]
                        rq['timestamp'] = row[2]
                    print( rq )

                    bulk_rsp.append( rq )






# Return result
print( json.dumps( bulk_rsp ) )
