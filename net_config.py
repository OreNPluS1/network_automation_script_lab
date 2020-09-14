from telnetlib import Telnet
import socket
import netmiko
import script_messages
import configparser
import os

DEVICE_TYPE_STR = "cisco_ios_telnet"
IOU = []
SWITCH = []


def is_number(num):
    """
    Simple logic to check if a string can be cast to int
    :param num: value
    :return: boolean
    """
    try:
        int(num)
        return True
    except ValueError:
        return False


def telnet_open_console(host, port):
    with Telnet(host, port) as tn:
        tn.interact()


def netmiko_connect(device_info):
    """
    Make new cisco device connection
    :param device_info: object, connection details to a device
    :return: object, created by netmiko.ConnectHandler
    """
    return netmiko.ConnectHandler(**device_info)


def add_device(auto_add=False):
    """
    Add an IOU device object or Switch device object to the respective list of devices
    :param auto_add: Auto add from ini file
    :return: int status code, 0 for success, 1 for error
    """
    if auto_add:
        # Set-Up ini file
        devices_auto_config = configparser.ConfigParser()
        devices_list_ini_path = input(script_messages.AddDeviceStrings.DEVICES_INI_PATH_ASK)
        if not os.path.isfile(devices_list_ini_path):
            print(script_messages.WARN_FILE_DOES_NOT_EXIST)

        devices_auto_config.read(devices_list_ini_path)
        device_type = devices_auto_config['MAIN']['device_type']
        devices_ip = devices_auto_config['MAIN']['ip']
        
        # iterate over IOU and SWITCH sections
        if 'IOU' in devices_auto_config:
            for device_auto_details in devices_auto_config['IOU']:
                device_port = int(devices_auto_config['IOU'][device_auto_details])
                status_code = device_connect_append(1, {'device_type': devices_type,
                                                        'host': device_ip,
                                                        'port': device_port})
                if status_code == 1:
                    try_again = 'y'
                    while try_again == 'y':
                        print(script_messages.AddDeviceStrings.ASK_TRY_AGAIN)
                        try_again = input(script_messages.ask_yes_or_not())
                        if try_again == 'y':
                            status_code = device_connect_append(1, device_auto_details)
                            if status_code == 0:
                                try_again = 'n'

        if "SWITCH" in devices_auto_config:
            for device_auto_details in devices_auto_config['SWITCH']:
                status_code = device_connect_append(2, devices_auto_config['SWITCH'][device_auto_details])
                if status_code == 1:
                    try_again = 'y'
                    while try_again == 'y':
                        print(script_messages.AddDeviceStrings.ASK_TRY_AGAIN)
                        try_again = input(script_messages.ask_yes_or_not())
                        if try_again == 'y':
                            status_code = device_connect_append(2, device_auto_details)
                            if status_code == 0:
                                try_again = 'n'
        return 0

    # Manual add
    ip_address = input(script_messages.AddDeviceStrings.IP_ADDRESS_ASK)
    values_verify = False
    destination_port = 0
    device_type = 0
    # Get values with validations
    while not values_verify:
        destination_port = input(script_messages.AddDeviceStrings.PORT_ASK)
        device_type = input(script_messages.AddDeviceStrings.DEVICE_TYPE_ASK)

        # Verify numeric values
        if is_number(destination_port) and is_number(device_type):
            destination_port = int(destination_port)
            device_type = int(device_type)

            # Verify valid port number
            if 0 <= destination_port <= 65535:
                # Verify existing device type
                if device_type == 1 or device_type == 2:
                    values_verify = True
                else:
                    print(script_messages.AddDeviceStrings.BAD_DEVICE_TYPE_SELECTION)
            else:
                print(script_messages.AddDeviceStrings.BAD_PORT_INPUT)
        else:
            print(script_messages.VALUE_NOT_A_NUMBER)

    device_connect = {
        'device_type': DEVICE_TYPE_STR,
        'host': ip_address,
        'port': int(destination_port)
    }
    return device_connect_append(device_type, device_connect)


def device_connect_append(device_type, device_details):
    """
    Append a device object to the devices list (1 for IOU, 2 for SWITCH)
    :param device_type: int, 1 for IOU or 2 for SWITCH
    :param device_details: object for netmiko_connect()
    :return: status code
    """
    try:
        if device_type == 1:
            IOU.append(netmiko_connect(device_details))
        elif device_type == 2:
            SWITCH.append(netmiko_connect(device_details))
    except socket.gaierror:
        print(script_messages.AddDeviceStrings.ERR_SOCKET_GAIERROR)
        return 1
    except ConnectionRefusedError:
        print(script_messages.AddDeviceStrings.ERR_CONNECTION_REFUSED)
        return 1
    except ConnectionError:
        print(script_messages.AddDeviceStrings.ERR_CONNECTION_GENERAL)
        return 1
    except netmiko.ssh_exception.NetmikoAuthenticationException:
        print(script_messages.AddDeviceStrings.ERR_LOGIN_FAILED)
    return 0


def show_interface_running_conf(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    """
    :param device: Device connection object
    """
    output = device.send_command('sh ip int br')
    print(output)


def configure_vlan(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    pass


def configure_ospf(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    pass


def configure_interface(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    pass


def device_selection_menu():
    """
    Let a user choose a device that was entered to the script
    :return: The device object the was chosen
    """
    device_selection = 0
    device_verify = False

    while not device_verify:
        device_selection = input(script_messages.MainMenuStrings.IOU_OR_SWITCH)
        # Verify that the input is a number
        if is_number(device_selection):
            device_selection = int(device_selection)
            # Verify that the choice exists
            if device_selection == 1 or device_selection == 2:
                device_verify = True
        else:
            print(script_messages.VALUE_NOT_A_NUMBER)

    # device selection 1 is IOU devices and 2 is SWITCH devices
    if device_selection == 1:
        device_number = 0
        device_number_verify = False
        # verify the device is selected by number
        while not device_number_verify:
            device_number = input(script_messages.generate_device_list(IOU) + '>')
            if is_number(device_number):
                device_number = int(device_number)
                device_number_verify = True
            else:
                print(script_messages.VALUE_NOT_A_NUMBER)

        return IOU[device_number]
    elif device_selection == 2:
        device_number = 0
        device_number_verify = False
        # verify the device is selected by number
        while not device_number_verify:
            device_number = input(script_messages.generate_device_list(SWITCH) + '>')
            if is_number(device_number):
                device_number = int(device_number)
                device_number_verify = True
            else:
                print(script_messages.VALUE_NOT_A_NUMBER)

        return SWITCH[device_number]


def main_menu():
    """
    Main menu function, let the user navigate in the script functions
    :return: boolean value to determine if exit the script or not
    """
    num_verify = False
    menu_selection = 0
    while not num_verify:
        menu_selection = input(script_messages.MainMenuStrings.MAIN_MENU)
        num_verify = is_number(menu_selection)
        if not num_verify:
            print(script_messages.VALUE_NOT_A_NUMBER)

    menu_selection = int(menu_selection)
    if menu_selection == 0:
        # exit the script
        return True
    elif menu_selection == 1:
        # add device/s
        print(script_messages.MainMenuStrings.ASK_AUTO_ADD_DEVICE)
        auto_selection = script_messages.ask_yes_or_not()
        if auto_selection == 'y':
            add_device(True)
        elif auto_selection == 'n':
            add_device(False)
    elif menu_selection == 500:
        selected_device = device_selection_menu()
        show_interface_running_conf(selected_device)

    return False


def main():
    print("Cisco configuration script")
    exit_script = False
    while not exit_script:
        exit_script = main_menu()


if __name__ == "__main__":
    main()
