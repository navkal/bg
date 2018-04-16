# Copyright 2018 BACnet Gateway.  All rights reserved.

from socket import gethostbyname, gethostname
from warnings import catch_warnings, simplefilter
from threading import Thread

from bacpypes.local.device import LocalDeviceObject
from bacpypes.app import BIPSimpleApplication
from bacpypes.core import enable_sleeping, run
from bacpypes.apdu import ReadPropertyRequest
from bacpypes.pdu import Address
from bacpypes.iocb import IOCB
from bacpypes.object import get_datatype
from bacpypes.constructeddata import Array
from bacpypes.primitivedata import Unsigned



def read_property( target_args ):

    with catch_warnings():
        simplefilter("ignore")
        start_task_manager()

    app = make_application()

    rsp = send_request( target_args, app )

    return rsp


def start_task_manager():
    enable_sleeping()
    t = Thread( target=task_manager )
    t.setDaemon( True )
    t.start()


def task_manager():
    run()


def make_application():

    dev = LocalDeviceObject(
        objectName='Betelgeuse',
        objectIdentifier=599,
        maxApduLengthAccepted=1024,
        segmentationSupported='segmentedBoth',
        vendorIdentifier=15
    )

    app = BIPSimpleApplication( dev, gethostbyname( gethostname() ) )

    return app


def send_request( target_args, app ):

    # build a request
    request = ReadPropertyRequest(
        objectIdentifier=( target_args['type'], target_args['instance'] ),
        propertyIdentifier=target_args['property']
    )
    request.pduDestination = Address( target_args['address'] )

    # make an IOCB
    iocb = IOCB( request )

    # give it to the application
    app.request_io( iocb )

    # wait for it to complete
    iocb.wait()

    # Handle completion: error, success, neither
    if iocb.ioError:
        # Error
        rsp = { 'error': str( iocb.ioError ) }

    elif iocb.ioResponse:
        # Success

        # Get the response PDU
        apdu = iocb.ioResponse

        # Extract the returned value
        datatype = get_datatype( apdu.objectIdentifier[0], apdu.propertyIdentifier )
        if issubclass( datatype, Array ) and (apdu.propertyArrayIndex is not None):
            if apdu.propertyArrayIndex == 0:
                value = apdu.propertyValue.cast_out( Unsigned )
            else:
                value = apdu.propertyValue.cast_out( datatype.subtype )
        else:
            value = apdu.propertyValue.cast_out( datatype )

        # Load returned value into response
        rsp = { 'value': value }

    else:
        # Neither
        rsp = { 'error': 'Request terminated unexpectedly' }

    return rsp


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser( description='Issue BACnet read request' )
    parser.add_argument( '-a', dest='address',  help='Target IP address' )
    parser.add_argument( '-t', dest='type',  help='Target type' )
    parser.add_argument( '-i', dest='instance',  help='Target instance' )
    parser.add_argument( '-p', dest='property',  help='Target property' )

    args = parser.parse_args()

    target_args = {
        'address': args.address,
        'type': args.type,
        'instance': int( args.instance ),
        'property': args.property
    }

    rsp = read_property( target_args )

    print( rsp )
