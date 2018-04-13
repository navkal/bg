# Copyright 2018 BACnet Gateway.  All rights reserved.

from bacpypes.service.device import LocalDeviceObject
from bacpypes.app import BIPSimpleApplication
from bacpypes.object import get_object_class, get_datatype

def read( config_args, target_args ):

    # make a device object
    this_device = LocalDeviceObject(
        objectName=config_args['objectName'],
        objectIdentifier=config_args['objectIdentifier'],
        maxApduLengthAccepted=config_args['maxApduLengthAccepted'],
        segmentationSupported=config_args['segmentationSupported'],
        vendorIdentifier=config_args['vendorIdentifier'],
        )

    # make a simple application
    this_application = BIPSimpleApplication( this_device, config_args['address'] )

    # get the services supported
    services_supported = this_application.get_services_supported()

    # let the device object know
    this_device.protocolServicesSupported = services_supported.value

    datatype = get_datatype( target_args['type'], target_args['property'] )

    rsp = { **config_args, **target_args }
    return rsp


if __name__ == '__main__':

    config_args = {
        'objectName': 'Betelgeuse',
        'address': '10.4.241.2',
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
        'instance': '3006238',
        'property': 'presentValue'
    }

    rsp = read( config_args, target_args )

    print( rsp )
