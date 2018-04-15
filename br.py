# Copyright 2018 BACnet Gateway.  All rights reserved.

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



def read_property( config_args, target_args ):

    with catch_warnings():
        simplefilter("ignore")
        start_task_manager()

    app = make_application( config_args )

    rsp = send_request( target_args, app )

    return rsp


def start_task_manager():
    t = Thread( target=task_manager )
    t.setDaemon( True )
    t.start()


def task_manager():
    enable_sleeping()
    run()


def make_application( config_args ):

    dev = LocalDeviceObject(
        objectName=config_args['objectName'],
        objectIdentifier=config_args['objectIdentifier'],
        maxApduLengthAccepted=config_args['maxApduLengthAccepted'],
        segmentationSupported=config_args['segmentationSupported'],
        vendorIdentifier=config_args['vendorIdentifier']
    )

    app = BIPSimpleApplication( dev, config_args['address'] )

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
        rsp = { 'error': 'unexpected termination of IOCB wait without ioError or ioResponse' }

    print( 'RETURNING', rsp )
    return rsp


if __name__ == '__main__':

    ca = {
        'objectName': 'Betelgeuse',
        'address': '10.4.241.2',
        'objectIdentifier': 599,
        'maxApduLengthAccepted': 1024,
        'segmentationSupported': 'segmentedBoth',
        'vendorIdentifier': 15,
        'foreignBBMD': '128.253.109.254',
        'foreignTTL': 30,
    }

    ta = {
        'address': '10.12.0.250',
        'type': 'analogInput',
        'instance': 3006238,
        'property': 'presentValue'
    }

    rsp = read_property( ca, ta )

    print( rsp )
