# Copyright 2018 Building Energy Gateway.  All rights reserved.

import sqlite3
import time
import os
from shutil import copyfile


# Save unique field value in table, if not already present, and return its row ID
def save_field( table, field_name, field_value, cursor, other_fields={} ):

    # Find out if this field value already exists in the specified table
    row_id = get_id( table, field_name, field_value, cursor )

    # Field value does not exist; insert it
    if row_id == None:
        names = field_name
        qs = '?'
        values = [ field_value ]

        for other_name in other_fields:
            names += ',' + other_name
            qs += ',?'
            values.append( other_fields[other_name] )

        cursor.execute( 'INSERT INTO ' + table + ' ( ' + names + ' ) VALUES(' + qs + ')', tuple( values ) )
        row_id = cursor.lastrowid

    # Return id
    return row_id


def get_id( table, field_name, field_value, cursor ):

    # Retrieve ID corresponding to supplied field value
    cursor.execute( 'SELECT id FROM ' + table + ' WHERE ' + field_name + '=?', ( field_value, ) )
    row = cursor.fetchone()

    if row:
        row_id = row[0]
    else:
        row_id = None

    # Return id
    return row_id


def log( logpath, msg ):

    # Format output line
    s = '[' + time.strftime( '%Y-%m-%d %H:%M:%S', time.localtime() ) + '] ' + msg

    # Print to standard output
    print( s )

    # Open, write, and close log file
    logfile = open( logpath , 'a' )
    logfile.write( s + '\n' )
    logfile.close()


def new_logs( prefix, ext='log' ):

    # Generate new log filenames
    suffix = '.' + ext
    logpath = prefix + '_' + time.strftime( '%Y-%m-%d_%H-%M-%S', time.localtime() ) + suffix
    savepath = prefix + suffix

    # Clean up pre-existing files of same names, if any
    if os.path.exists( logpath ):
        os.remove( logpath )

    if os.path.exists( savepath ):
        os.remove( savepath )

    return logpath, savepath


def save_log( logpath, savepath ):
    copyfile( logpath, savepath )
