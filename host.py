import netifaces
from socket import gethostbyname, gethostname

# Get host address
def get_host_address():
    not_used_1, not_used_2, address = pick_host_address()
    return address

# Pick IP address by looking at interfaces found on host
def pick_host_address():

    # Get list of interface names
    interfaces = netifaces.interfaces()

    # Look for interface name typically found on Ubuntu, giving priority to virtual interface created by VPN client
    interface_name = ''
    for name in interfaces:
        if name.startswith( 'ppp' ): # Virtual
            interface_name = name
            break
        elif name.startswith( 'enp' ) or  name.startswith( 'eth' ):  # Physical
            interface_name = name

    # Determine IP address
    if interface_name:
        # Got an Ubuntu interface name.  Extract corresponding IP address.
        addresses = netifaces.ifaddresses( interface_name )
        address = addresses[netifaces.AF_INET][0]['addr']
    else:
        # Didn't get an Ubuntu interface name.  Use method of last resort.
        address = gethostbyname( gethostname() )

    return interfaces, interface_name, address


if __name__ == '__main__':

    interfaces, interface_name, address = pick_host_address()

    print( 'Found available interfaces:', interfaces )
    if interface_name:
        print( 'Picked interface:', interface_name )
    print( 'Picked IP address:', address )
