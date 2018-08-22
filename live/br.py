# Copyright 2018 BACnet Gateway.  All rights reserved.

from host import get_host_address
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


_standalone = 1
_standalone_meter = 3
_standalone_doonits = 0


def read_property( target_args ):

    with catch_warnings():
        simplefilter("ignore")
        start_task_manager()

    app = make_application()

    for i in range( 0, 10 ):
        rsp = get_value_and_units( target_args, app )
        if rsp['success']:
            break
        else:
            import time
            time.sleep( 0.1 )

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

    addr = get_host_address()

    # Make the application
    app = BIPSimpleApplication( dev, addr )

    return app


def get_value_and_units( target_args, app ):

    rq_prop = target_args['property']

    if _standalone:

        success = True
        message = ''

        if _standalone_meter:
            import time
            t = time.time()
            zeroes = 10 ** _standalone_meter
            value = t - int( t / zeroes ) * zeroes
            if _standalone_doonits:
                rsp_units = { 'units': ( 'foonits' if ( int( value ) % _standalone_doonits ) else 'doonits' ) }
            else:
                rsp_units = { 'units': 'foonits'}
        else:
            import random
            value = random.randrange( 250000000, 990000000 ) / 10000000
            rsp_units = { 'units': ( 'foonits' if ( int( value ) % 10 ) else 'doonits' ) }

        rsp_value = { target_args['property']: value }

    else:

        success, message, rsp_value = send_request( target_args, app )

        if success:
            target_args['property'] = 'units'
            not_used_1, not_used_2, rsp_units = send_request( target_args, app )
            rsp_units = translate_units( rsp_units )
        else:
            rsp_units = { 'units': ''}

    rsp_value['requested_property'] = rq_prop
    rsp = { 'success': success, 'message': message, **rsp_value, **rsp_units }

    return rsp


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
        success = False
        message = str( iocb.ioError )
        result = ''

    elif iocb.ioResponse:
        # Success
        success = True
        message = ''

        # Get the response PDU
        apdu = iocb.ioResponse

        # Extract the returned value
        datatype = get_datatype( apdu.objectIdentifier[0], apdu.propertyIdentifier )
        if issubclass( datatype, Array ) and (apdu.propertyArrayIndex is not None):
            if apdu.propertyArrayIndex == 0:
                result = apdu.propertyValue.cast_out( Unsigned )
            else:
                result = apdu.propertyValue.cast_out( datatype.subtype )
        else:
            result = apdu.propertyValue.cast_out( datatype )

    else:
        # Neither
        success = False
        message = 'Request terminated unexpectedly'
        result = ''

    rsp = { target_args['property']: result }

    return success, message, rsp


def translate_units( rsp_units ):

    dcUnits = {
        'degreesFahrenheit': 'deg F',
        'kilowattHours': 'kWh',
        'kilowatts': 'kW',
        'partsPerMillion': 'ppm',
        'watts': 'W'
    }

    if rsp_units['units'] in dcUnits:
        rsp_units['units'] = dcUnits[rsp_units['units']]

    return rsp_units


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
