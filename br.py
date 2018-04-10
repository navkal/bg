# Copyright 2018 BACnet Gateway.  All rights reserved.

import argparse
#### import bacpypes

def read( args ):

    # --> fake --> fake --> fake --> fake -->
    import time
    time.sleep( 0.1 )
    # <-- fake <-- fake <-- fake <-- fake <--


    rsp = {}

    return rsp


if __name__ == '__main__':
    parser = argparse.ArgumentParser( description='Issue a BACnet read request' )
    parser.add_argument('-t', dest='tbd',  help='tbd')
    args = parser.parse_args()


    rsp = read( args )
    print( rsp )
