# Copyright 2018 Building Energy Gateway.  All rights reserved.

import time
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

        for agent_row in reader:

            # Skip empty and comment lines
            if ( len( agent_row ) > 0 ) and not agent_row[0].startswith( '#' ):

                # Add map entry
                facility = agent_row[0].strip()
                address = socket.inet_ntoa( struct.pack( '>L', int( agent_row[1].strip(), 16 ) ) )
                fac_addr_map[facility] = address

    with open( 'stations.csv', newline='' ) as csvfile:
        reader = csv.reader( csvfile )

        for station_row in reader:

            # Skip empty and comment lines
            if ( len( station_row ) > 0 ) and not station_row[0].startswith( '#' ):

                # Add map entry
                facility = station_row[0].strip()
                address = facility
                fac_addr_map[facility] = address

    return fac_addr_map


def make_rsp( rq ):

    msg = ''

    # Map facility to address
    if 'facility' in rq and rq['facility'] in fac_addr_map:
        rq['address'] = fac_addr_map[rq['facility']]

    # Set default type
    if 'type' not in rq:
        rq['type'] = 'analogInput'

    # Set default property
    if 'property' not in rq:
        rq['property'] = 'presentValue'

    # If all arguments are present...
    if ( 'address' in rq ) and ( 'type' in rq ) and ( 'instance' in rq ) and ( 'property' in rq ):

        # Retrieve value, units, and timestamp from cache
        cache_value = cache_db.get_cache_value( rq['address'], rq['type'], rq['instance'], rq['property'], cur, conn )

        if cache_value:
            rq[rq['property']] = cache_value['value']
            rq['units'] = cache_value['units']
            rq['timestamp'] = cache_value['timestamp']
        else:
            msg = 'No data'

    else:
        msg = 'Missing arguments'

    # Remove mapped address
    if 'facility' in rq and rq['facility'] in fac_addr_map:
        del rq['address']

    # Create response
    rq['message'] = msg
    rq['success'] = ( msg == '' )
    rsp = collections.OrderedDict( sorted( rq.items() ) )

    return rsp


if __name__ == '__main__':

    start_time = time.time()
    rq_count = 0
    rsp_count = 0
    rsp_list = []

    db = '../bg_db/cache.sqlite'

    if os.path.exists( db ):

        # Get arguments
        parser = argparse.ArgumentParser( description='Get multiple values from cache' )
        parser.add_argument( '-b', dest='bulk_request' )
        args = parser.parse_args()

        if args.bulk_request:

            # Extract request
            bulk_rq = json.loads( args.bulk_request.replace( "'", '"' ) )
            rq_count = len( bulk_rq )

            # If supplied request is a list with at least one element...
            if isinstance( bulk_rq, list ) and len( bulk_rq ):

                # Build facility-to-address map
                fac_addr_map = make_fac_addr_map()

                # Connect to the database
                conn = sqlite3.connect( db )
                cur = conn.cursor()

                # Build response
                for rq in bulk_rq:
                    rsp = make_rsp( rq )
                    if rsp['success']:
                        rsp_count += 1
                    rsp_list.append( rsp )

    # Build response map
    rsp_map = {}
    for rsp in rsp_list:
        if rsp['success'] and ( 'facility' in rsp ):
            facility = rsp['facility']
            if facility not in rsp_map:
                rsp_map[facility] = {}
            rsp_map[facility][rsp['instance']] = rsp

    # Build bulk response
    bulk_rsp = {
        'rq_count': rq_count,
        'rsp_count': rsp_count,
        'rsp_list': rsp_list,
        'rsp_map': rsp_map,
        'elapsed_sec': round( ( time.time() - start_time ) * 1000 ) / 1000
    }
    bulk_rsp = collections.OrderedDict( sorted( bulk_rsp.items() ) )

    # Return result
    print( json.dumps( bulk_rsp ) )
