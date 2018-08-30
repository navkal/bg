# Copyright 2018 BACnet Gateway.  All rights reserved.

import os
import argparse
import json
import csv
import socket
import struct
import sqlite3
import cache_db
import collections


def make_fac_addr_map():

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

    return fac_addr_map


def make_rsp( item ):

    rsp = None

    # Map facility to address
    if 'facility' in item and item['facility'] in fac_addr_map:
        item['address'] = fac_addr_map[item['facility']]

    # Set default type
    if 'type' not in item:
        item['type'] = 'analogInput'

    # Set default property
    if 'property' not in item:
        item['property'] = 'presentValue'

    # If all arguments are present...
    if ( 'address' in item ) and ( 'type' in item ) and ( 'instance' in item ) and ( 'property' in item ):

        # Retrieve value, units, and timestamp from cache
        row = cache_db.get_cache_value( item['address'], item['type'], item['instance'], item['property'], cur, conn )

        if row:

            # Copy cache values into item
            item[item['property']] = row[1]
            item['units'] = row[2]
            item['timestamp'] = row[3]

            # Create response
            rsp = collections.OrderedDict( sorted( item.items() ) )

    return rsp


if __name__ == '__main__':

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

            # If supplied request is a list with at least one element...
            if isinstance( bulk_rq, list ) and len( bulk_rq ):

                # Build facility-to-address map
                fac_addr_map = make_fac_addr_map()

                # Connect to the database
                conn = sqlite3.connect( db )
                cur = conn.cursor()

                # Build response
                for item in bulk_rq:
                    rsp = make_rsp( item )
                    if rsp:
                        bulk_rsp.append( rsp )

    # Return result
    print( json.dumps( bulk_rsp ) )
