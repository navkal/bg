# Copyright 2018 BACnet Gateway.  All rights reserved.

from threading import Thread

from bacpypes.local.device import LocalDeviceObject
from bacpypes.app import BIPSimpleApplication
from bacpypes.core import run, enable_sleeping
from bacpypes.apdu import ReadPropertyRequest
from bacpypes.pdu import Address
from bacpypes.iocb import IOCB
from bacpypes.object import get_datatype
from bacpypes.constructeddata import Array

this_application = None

def stub( config_args, target_args ):
    return { **config_args, **target_args }

def read( config_args, target_args ):

    # make a device object
    this_device = LocalDeviceObject(
        objectName=config_args['objectName'],
        objectIdentifier=config_args['objectIdentifier'],
        maxApduLengthAccepted=config_args['maxApduLengthAccepted'],
        segmentationSupported=config_args['segmentationSupported'],
        vendorIdentifier=config_args['vendorIdentifier']
    )

    # make a simple application
    global this_application
    this_application = BIPSimpleApplication( this_device, config_args['address'] )

    # Start the console
    t = Thread( target=console )
    t.start()

    # Start the Task Manager
    enable_sleeping()
    run()



def console():

    # build a request
    request = ReadPropertyRequest(
        objectIdentifier=( target_args['type'], target_args['instance'] ),
        propertyIdentifier=target_args['property']
    )
    request.pduDestination = Address( target_args['address'] )

    # make an IOCB
    iocb = IOCB( request )

    # give it to the application
    this_application.request_io( iocb )

    # wait for it to complete
    print( 'bf wait' )
    iocb.wait()
    print( 'af wait' )


    # do something for error/reject/abort
    if iocb.ioError:
        rsp = { 'error': str( iocb.ioError ) }

    # do something for success
    elif iocb.ioResponse:

        apdu = iocb.ioResponse
        datatype = get_datatype( apdu.objectIdentifier[0], apdu.propertyIdentifier )
        if issubclass( datatype, Array ) and (apdu.propertyArrayIndex is not None):
            if apdu.propertyArrayIndex == 0:
                value = apdu.propertyValue.cast_out( Unsigned )
            else:
                value = apdu.propertyValue.cast_out( datatype.subtype )
        else:
            value = apdu.propertyValue.cast_out( datatype )

        apdu = iocb.ioResponse
        datatype = get_datatype( apdu.objectIdentifier[0], apdu.propertyIdentifier )

        print( '====================> ', value )
        rsp = { 'value': value }

    else:
        rsp = { 'nothing': 'happened' }

    print( 'RETURNING', rsp )
    return rsp


if __name__ == '__main__':

    # Pick up debug parameters
    from bacpypes.consolelogging import ConfigArgumentParser
    args = ConfigArgumentParser(description=__doc__).parse_args()

    config_args = {
        'objectName': 'Betelgeuse',
        'address': '10.4.241.1',
        'objectIdentifier': 599,
        'maxApduLengthAccepted': 1024,
        'segmentationSupported': 'segmentedBoth',
        'vendorIdentifier': 15,
        'foreignBBMD': '128.253.109.254',
        'foreignTTL': 30,
    }

    target_args = {
        'address': '10.12.0.250',
        'type': 'analogInput',
        'instance': 3006238,
        'property': 'presentValue'
    }

    rsp = read( config_args, target_args )

    print( rsp )
