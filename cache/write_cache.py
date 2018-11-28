# Copyright 2018 Building Energy Gateway.  All rights reserved.

import os
import sqlite3
import time

import sys
sys.path.append( 'util' )
import db_util
import csv_util


def open_db():

    db = '../bg_db/cache.sqlite'

    # Optionally remove database
    if ( args.remove ):
        try:
            os.remove( db )
        except:
            pass

    # Determine whether database exists
    db_exists = os.path.exists( db )

    # Connect to database
    conn = sqlite3.connect( db )
    cur = conn.cursor()

    if not db_exists:

        # Initialize database
        cur.executescript('''

            CREATE TABLE IF NOT EXISTS Cache (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                address_id INTEGER,
                type_id INTEGER,
                instance TEXT,
                property_id INTEGER,
                value INTEGER,
                units_id INTEGER,
                update_timestamp INTEGER,
                access_timestamp INTEGER
            );

            CREATE TABLE IF NOT EXISTS Addresses (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                address TEXT UNIQUE,
                facility TEXT UNIQUE,
                facility_type_id INTEGER
            );

            CREATE TABLE IF NOT EXISTS FacilityTypes (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                facility_type TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS Types (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                type TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS Properties (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                property TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS Units (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
                units TEXT UNIQUE
            );

        ''')

        conn.commit()

    return conn, cur


def write_value():

    # Test whether entry already exists
    cur.execute( '''
        SELECT
            Cache.id
        FROM Cache
            LEFT JOIN Addresses ON Cache.address_id=Addresses.id
            LEFT JOIN Types ON Cache.type_id=Types.id
            LEFT JOIN Properties ON Cache.property_id=Properties.id
        WHERE ( Addresses.address=? AND Types.type=? AND Cache.instance=? AND Properties.property=? );
    ''', ( args.address, args.type, args.instance, args.property )
    )
    row = cur.fetchone()

    units_id = db_util.save_field( 'Units', 'units', args.units, cur )
    update_timestamp = int( time.time() )

    if row:

        # Entry exists; update it
        cur.execute( 'UPDATE Cache SET value=?, units_id=?, update_timestamp=? WHERE id=?', ( args.value, units_id, update_timestamp, row[0] ) )

    else:

        # Entry does not exist; insert it

        # Find facility type
        facility_map = csv_util.make_facility_map()
        facility = None
        facility_type = None
        for fac in facility_map:
            if facility_map[fac]['address'] == args.address:
                facility = facility_map[fac]['facility']
                facility_type = facility_map[fac]['facility_type']
                break

        # Insert into database
        facility_type_id = db_util.save_field( 'FacilityTypes', 'facility_type', facility_type, cur )
        address_id = db_util.save_field( 'Addresses', 'address', args.address, cur, other_fields={ 'facility': facility, 'facility_type_id': facility_type_id } )
        type_id = db_util.save_field( 'Types', 'type', args.type, cur )
        property_id = db_util.save_field( 'Properties', 'property', args.property, cur )
        access_timestamp = update_timestamp
        cur.execute( 'INSERT INTO Cache ( address_id, type_id, instance, property_id, value, units_id, update_timestamp, access_timestamp ) VALUES (?,?,?,?,?,?,?,?)',
            ( address_id, type_id, args.instance, property_id, args.value, units_id, update_timestamp, access_timestamp ) )

    conn.commit()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser( description='Save value to cache' )
    parser.add_argument( '-a', dest='address' )
    parser.add_argument( '-t', dest='type' )
    parser.add_argument( '-i', dest='instance' )
    parser.add_argument( '-p', dest='property' )
    parser.add_argument( '-v', dest='value')
    parser.add_argument( '-u', dest='units' )
    parser.add_argument( '-r', dest='remove', action='store_true' )

    args = parser.parse_args()

    conn, cur = open_db()
    write_value()
