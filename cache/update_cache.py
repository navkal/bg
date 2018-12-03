# Copyright 2018 Building Energy Gateway.  All rights reserved.

import os
import argparse
import sqlite3
import time
import datetime
import requests
import csv

import sys
sys.path.append( '../util' )
import db_util
import csv_util

idle_max = datetime.timedelta( days=7 )
stale_max = datetime.timedelta( minutes=30 )

log_filename = None


def update_cache():
    start_time = time.time()

    cur.execute( '''
        SELECT
            Cache.id, Types.type, Cache.instance, Properties.property, FacilityTypes.facility_type, Addresses.facility, Addresses.address, Cache.update_timestamp, Cache.access_timestamp
        FROM Cache
            LEFT JOIN Types ON Cache.type_id=Types.id
            LEFT JOIN Properties ON Cache.property_id=Properties.id
            LEFT JOIN Addresses ON Cache.address_id=Addresses.id
            LEFT JOIN FacilityTypes ON Addresses.facility_type_id=FacilityTypes.id
    ''' )

    rows = cur.fetchall()

    n_deleted = 0
    n_updated = 0

    for row in rows:

        # Wait
        time.sleep( args.sleep_interval )

        # Calculate time intervals
        now = datetime.datetime.now()
        stale = now - datetime.datetime.fromtimestamp( row[7] )
        idle = now - datetime.datetime.fromtimestamp( row[8] )

        if idle > idle_max:

            # Entry has not been used; delete it
            delete_entry( row[0] )

            n_deleted += 1

        elif stale > stale_max:

            # Entry is stale; post request to update it
            post_request( row[1], row[2], row[3], row[4], row[5], row[6] )

            n_updated += 1

    if n_deleted or n_updated:
        db_util.log( logpath, 'Deleted ' + str( n_deleted ) + ' and updated ' + str( n_updated ) + ' of ' + str( len( rows ) ) + ' entries.  Elapsed time: ' + str( datetime.timedelta( seconds=int( time.time() - start_time ) ) ) )


def delete_entry( cache_id ):

    # Get direct references to rows in other tables
    cur.execute( 'SELECT address_id, type_id, property_id, units_id FROM Cache WHERE id=?', ( cache_id, ) )
    cache_row = cur.fetchone()
    address_id = cache_row[0]
    type_id = cache_row[1]
    property_id = cache_row[2]
    units_id = cache_row[3]

    # Get indirect references to rows in other tables
    cur.execute( 'SELECT facility_type_id FROM Addresses WHERE id=?', ( address_id, ) )
    addresses_row = cur.fetchone()
    facility_type_id = addresses_row[0]

    # Delete the row
    cur.execute( 'DELETE FROM Cache WHERE id=?', ( cache_id, ) )

    # Clear obsolete references
    clear_reference( 'Cache', 'units_id', units_id, 'Units' )
    clear_reference( 'Cache', 'property_id', property_id, 'Properties' )
    clear_reference( 'Cache', 'type_id', type_id, 'Types' )
    clear_reference( 'Cache', 'address_id', address_id, 'Addresses' )
    clear_reference( 'Addresses', 'facility_type_id', facility_type_id, 'FacilityTypes' )

    conn.commit()


def clear_reference( ref_source, id_name, id_value, ref_target ):
    cur.execute( 'SELECT COUNT(id) FROM ' + ref_source + ' WHERE ' + id_name + '=?', ( id_value, ) )
    if cur.fetchone()[0] == 0:
        cur.execute( 'DELETE FROM ' + ref_target + ' WHERE id=?', ( id_value, ) )


def post_request( type, instance, property, facility_type, facility, address ):

    # Set up request arguments
    bg_args = {
        'type': type,
        'instance': instance,
        'property': property,
        'live': True
    }

    if facility_type == 'weatherStation':
        bg_args['facility'] = facility
    else:
        bg_args['address'] = address

    # Issue request to Building Energy Gateway
    url = 'http://' + args.hostname + ':' + str( args.port )
    requests.post( url, data=bg_args )


if __name__ == '__main__':

    # Get list of running processes
    ps = os.popen( 'ps -elf' ).read()

    # Find out how many occurrences of this script are running
    dups = ps.count( __file__ )

    # If no other occurrences of this script are running, proceed to update cache
    if dups <= 1:

        db = '../../bg_db/cache.sqlite'

        # If database exists...
        if os.path.exists( db ):

            # Open database
            conn = sqlite3.connect( db )
            cur = conn.cursor()

            # Get command line arguments
            parser = argparse.ArgumentParser( description='Update cache of recently requested values', add_help=False )
            parser.add_argument( '-h', dest='hostname' )
            parser.add_argument( '-p', dest='port' )
            parser.add_argument( '-s', dest='sleep_interval', type=int )
            args = parser.parse_args()

            logpath, notused = db_util.new_logs( '../../bg_db/update_cache' )
            db_util.log( logpath, os.path.basename( __file__ ) + ' starting' )

            # Update cache continuously
            while True:
                update_cache()
