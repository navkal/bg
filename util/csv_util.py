# Copyright 2018 Building Energy Gateway.  All rights reserved.

import csv
import socket
import struct


def get_facilities( path='' ):

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
