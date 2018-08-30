# Copyright 2018 BACnet Gateway.  All rights reserved.

import time

def get_cache_value( address, type, instance, property, cur, conn ):

    cache_value = None

    # Retrieve value, units, and timestamp from cache
    cur.execute( '''
        SELECT
            Cache.id, Cache.value, Units.units, Cache.update_timestamp
        FROM Cache
            LEFT JOIN Addresses ON Cache.address_id=Addresses.id
            LEFT JOIN Types ON Cache.type_id=Types.id
            LEFT JOIN Properties ON Cache.property_id=Properties.id
            LEFT JOIN Units ON Cache.units_id = Units.id
        WHERE ( Addresses.address=? AND Types.type=? AND Cache.instance=? AND Properties.property=? );
    ''', ( address, type, instance, property )
    )

    row = cur.fetchone()

    if row:
        # Update access timestamp
        cur.execute( 'UPDATE Cache SET access_timestamp=? WHERE id=?', ( int( time.time() ), row[0] ) )
        conn.commit()
        cache_value = { 'value': row[1], 'units': row[2], 'timestamp': row[3] * 1000 }

    return cache_value
