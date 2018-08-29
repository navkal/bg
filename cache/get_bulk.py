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

        if len( bulk_rq ):

            # Build facility-to-address mapping
            with open( 'agents.csv', newline='' ) as csvfile:
                reader = csv.reader( csvfile )
                n_agent = 0
                for agent_row in reader:
                    if n_agent == 0:
                        prefix = agent_row[0]
                    else:
                        print( '{0}: {1} = {2}'.format( n_agent, agent_row[0], prefix + agent_row[1] ) )
                        addr_long = int( prefix + agent_row[1], 16 )
                        ip = socket.inet_ntoa( struct.pack( '>L', addr_long ) )
                        print( ip )

                    n_agent += 1


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
