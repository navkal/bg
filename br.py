# Copyright 2018 BACnet Gateway.  All rights reserved.

from bacpypes.local.device import LocalDeviceObject
from bacpypes.app import BIPSimpleApplication
from bacpypes.apdu import ReadPropertyRequest
from bacpypes.pdu import Address
from bacpypes.iocb import IOCB
from bacpypes.task import TaskManager


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
    this_application = BIPSimpleApplication( this_device, config_args['address'] )

    # build a request
    request = ReadPropertyRequest(
        objectIdentifier=( target_args['type'], target_args['instance'] ),
        propertyIdentifier=target_args['property']
    )
    request.pduDestination = Address( target_args['address'] )

    # make an IOCB
    iocb = IOCB( request )

    # give it to the application
    TaskManager()
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
        rsp = { **config_args, **target_args }

    else:
        rsp = { 'nothing': 'happened'}

    return rsp


if __name__ == '__main__':

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
