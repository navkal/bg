# Copyright 2018 Building Energy Gateway.  All rights reserved.

import csv
import socket
import struct


def make_facility_map( path='' ):

    facility_map = {}

    with open( path + 'facilities.csv', newline='' ) as csvfile:
        reader = csv.reader( csvfile )

        # Skip header line
        next( reader )

        for facility_row in reader:

            # Skip empty and comment lines
            if ( len( facility_row ) > 0 ) and not facility_row[0].strip().startswith( '#' ):

                # Add map entry
                facility = facility_row[0].strip()
                facility_type = facility_row[1].strip()
                facility_map[facility] = { 'facility': facility, 'facility_type': facility_type, 'address': None, 'default_type': None, 'url': None }

                if facility_type == 'bacnetAgent':
                    address = socket.inet_ntoa( struct.pack( '>L', int( facility_row[2].strip(), 16 ) ) )
                    facility_map[facility]['address'] = address
                    ########### DEBUG - get IP addresses of facilities ###########
                    # print( '{0:18} {1}'.format( facility, address ) )
                    ########### DEBUG - get IP addresses of facilities ###########
                    facility_map[facility]['default_type'] = 'analogInput'

                elif facility_type == 'weatherStation':
                    facility_map[facility]['address'] = facility
                    facility_map[facility]['default_type'] = 'weatherData'
                    facility_map[facility]['url'] = facility_row[3].strip()

                else:
                    # Unrecognized facility type
                    pass

    return facility_map
