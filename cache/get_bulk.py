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


def make_facility_map():

    facility_map = {}

    with open( 'facilities.csv', newline='' ) as csvfile:
        reader = csv.reader( csvfile )

        # Skip header line
        next( reader )

        for facility_row in reader:

            # Skip empty and comment lines
            if ( len( facility_row ) > 0 ) and not facility_row[0].strip().startswith( '#' ):

                # Add map entry
                facility = facility_row[0].strip()
                facility_type = facility_row[1].strip()
                facility_map[facility] = { 'facility': facility, 'facility_type': facility_type }

                if facility_type == 'bacnetAgent':
                    address = socket.inet_ntoa( struct.pack( '>L', int( facility_row[2].strip(), 16 ) ) )
                    facility_map[facility]['address'] = address
                    facility_map[facility]['default_type'] = 'analogInput'

                elif facility_type == 'weatherStation':
                    facility_map[facility]['address'] = facility
                    facility_map[facility]['default_type'] = 'weatherData'

                else:
                    # Unrecognized facility type; don't create map entry
                    pass

    return facility_map


def make_rsp( rq ):

    msg = ''

    if 'facility' in rq and rq['facility'] in facility_map:
        map_entry = facility_map[rq['facility']]

        # Map facility to address
        rq['address'] = map_entry['address']

        # Set default type
        if 'type' not in rq:
            rq['type'] = map_entry['default_type']

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

    # Remove mapped address from result
    if 'facility' in rq and rq['facility'] in facility_map:
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
                facility_map = make_facility_map()

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
