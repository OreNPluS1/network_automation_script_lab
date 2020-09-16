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
    :param num: string value
    :return: boolean
    """
    try:
        int(num)
        return True
    except ValueError:
        return False


def write_to_file(output):
    """
    Ask the user if he wants to save the output to a file
    :param output: output from a command
    :return: 0 for success
    """
    print(script_messages.ASK_SAVE_OUTPUT_TO_FILE)
    answer = script_messages.ask_yes_or_not()
    if answer == 'y':
        destination_file = input(script_messages.ASK_FILE_NAME) + '.txt'
        try:
            with open(destination_file, 'w') as output_file:
                output_file.write(output)
        except Exception as error:
            print(error)
    return 0


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
                status_code = device_connect_append(1, {'device_type': device_type,
                                                        'host': devices_ip,
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
                device_port = int(devices_auto_config['SWITCH'][device_auto_details])
                status_code = device_connect_append(2, {'device_type': device_type,
                                                        'host': devices_ip,
                                                        'port': device_port})
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


def show_interfaces(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    """
    Show interface configurations
    :param device: Device connection object
    :return: 0 for success
    """
    output = device.send_command('sh ip int br')
    print(output)
    write_to_file(output)
    return 0


def show_ip_routing_table(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    """
    Show current ip routing table
    :param device: Device connection object
    :return: 0 for success
    """
    output = device.send_command('sh ip route')
    print(output)
    write_to_file(output)
    return 0


def show_vlan(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    """
    Show configured vlan's
    :param device: Device connection object
    :return: 0 for success
    """
    output = device.send_command('show vlan')
    print(output)
    write_to_file(output)
    return 0


def show_mac_table(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    """
    Show mac address table
    :param device: Device connection object
    :return: 0 for success
    """
    output = device.send_command('show mac address-table')
    print(output)
    write_to_file(output)
    return 0


def create_vlan(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    """
    Create a new vlan on the switch
    :param device: Device connection object
    :return: 0 for success
    """
    print(script_messages.ConfigureVlanStrings.ASK_SHOW_VLAN)
    answer = script_messages.ask_yes_or_not()
    if answer == 'y':
        show_vlan(device)

    vlan_number = input(script_messages.GeneralConfiguration.ASK_VLAN_NUMBER)
    while not is_number(vlan_number):
        print(script_messages.VALUE_NOT_A_NUMBER)
        vlan_number = input(script_messages.GeneralConfiguration.ASK_VLAN_NUMBER)
    selected_vlan = 'vlan {0}'.format(vlan_number)

    vlan_name = input(script_messages.ConfigureVlanStrings.ASK_VLAN_NAME)
    vlan_naming = 'name {0}'.format(vlan_name)

    commands_set = [selected_vlan,
                    vlan_naming,
                    'state active',
                    'no shutdown']
    device.send_config_set(commands_set)
    return 0


def configure_vlan(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    """
    Configure vlan for selected interface
    :param device: Device connection object
    :return: 0 for success
    """
    print(script_messages.ConfigureVlanStrings.ASK_SHOW_VLAN)
    answer = script_messages.ask_yes_or_not()
    if answer == 'y':
        show_vlan(device)
    selected_interface = input(script_messages.GeneralConfiguration.ASK_INTERFACE)
    selected_interface = 'int {0}'.format(selected_interface)

    # Ask the user if he wants to config a trunk, if not, just config a vlan for the interface
    print(script_messages.ConfigureVlanStrings.ASK_CONFIG_TRUNK)
    config_trunk = script_messages.ask_yes_or_not()
    if config_trunk == 'y':
        # Config a trunk
        commands_set = [selected_interface,
                        'switchport trunk encapsulation dot1q',
                        'switchport mode trunk',
                        'exit']
        device.send_config_set(commands_set)
        return 0
    else:
        # Config a vlan for the interface
        vlan_number = input(script_messages.GeneralConfiguration.ASK_VLAN_NUMBER)
        while not is_number(vlan_number):
            print(script_messages.VALUE_NOT_A_NUMBER)
            vlan_number = input(script_messages.GeneralConfiguration.ASK_VLAN_NUMBER)
        vlan_command = "switchport access vlan {0}".format(vlan_number)
        command_set = [selected_interface,
                       vlan_command,
                       'exit']
        device.send_config_set(command_set)
        return 0


def configure_ospf(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    """
    Configure router ospf for the selected device
    :param device: Device connection object
    :return: 0 for success
    """
    # Ask for the ospf process id
    ospf_process_id = input(script_messages.ConfigureOspfStrings.ASK_PROCESS_ID)
    while not is_number(ospf_process_id):
        print(script_messages.VALUE_NOT_A_NUMBER)
        ospf_process_id = input(script_messages.ConfigureOspfStrings.ASK_PROCESS_ID)
    ospf_process_id = "router ospf {0}".format(ospf_process_id)

    # Ask for the network arguments
    mask_ip_address = input(script_messages.ConfigureOspfStrings.ASK_MASK_IP_ADDRESS)
    wildcard_mask_address = input(script_messages.ConfigureOspfStrings.ASK_WILDCARD_MASK_ADDRESS)
    area_number = input(script_messages.ConfigureOspfStrings.ASK_AREA)
    while not is_number(area_number):
        print(script_messages.VALUE_NOT_A_NUMBER)
        area_number = input(script_messages.ConfigureOspfStrings.ASK_AREA)

    network_command = "network {ip_address} {wildcard_mask} area {area_id}".format(ip_address=mask_ip_address,
                                                                                   wildcard_mask=wildcard_mask_address,
                                                                                   area_id=area_number)
    ospf_config_commands = [ospf_process_id,
                            network_command,
                            'exit']
    device.send_config_set(ospf_config_commands)
    return 0


def configure_interface(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    """
    Configure interface settings
    :param device: Device connection object
    :return: 0 for success
    """
    print(script_messages.ConfigureInterfaceStrings.ASK_SHOW_INTERFACE_IP_CONFIGURATIONS)
    answer = script_messages.ask_yes_or_not()
    if answer == 'y':
        show_interfaces(device)

    # Ask if the user wants to configure a subinterface
    print(script_messages.ConfigureInterfaceStrings.ASK_IS_SUBINTERFACE)
    is_subinterface = script_messages.ask_yes_or_not()

    # select interface
    selected_interface = input(script_messages.GeneralConfiguration.ASK_INTERFACE)
    interface_command = 'int {0}'.format(selected_interface)

    # Setup the interface ip settings
    interface_ip_address = input(script_messages.ConfigureInterfaceStrings.ASK_INTERFACE_IP)
    interface_subnet_mask = input(script_messages.ConfigureInterfaceStrings.ASK_INTERFACE_SUBNET_MASK)
    ip_address_command = 'ip address {ip_address} {subnet_mask}'.format(ip_address=interface_ip_address,
                                                                        subnet_mask=interface_subnet_mask)

    # If this is a subinterface, configure the encapsulation command
    if is_subinterface == 'y':
        vlan_number = input(script_messages.GeneralConfiguration.ASK_VLAN_NUMBER)
        while not is_number(vlan_number):
            print(script_messages.VALUE_NOT_A_NUMBER)
            vlan_number = input(script_messages.GeneralConfiguration.ASK_VLAN_NUMBER)
        encapsulation_command = 'encapsulation dot1Q {vlan_number}'.format(vlan_number=vlan_number)
        interface_configuration_commands = [interface_command,
                                            encapsulation_command,
                                            ip_address_command,
                                            'no shutdown',
                                            'exit']
    else:
        interface_configuration_commands = [interface_command,
                                            ip_address_command,
                                            'no shutdown',
                                            'exit']
    device.send_config_set(interface_configuration_commands)
    return 0


def interface_shutdown_mode(device: netmiko.cisco.cisco_ios.CiscoIosTelnet):
    """
    Set interface to 'no shutdown'
    :param device: Device connection object
    :return: 0 for success
    """
    print(script_messages.ConfigureInterfaceStrings.ASK_SHOW_INTERFACE_IP_CONFIGURATIONS)
    answer = script_messages.ask_yes_or_not()
    if answer == 'y':
        show_interfaces(device)

    # select interface
    selected_interface = input(script_messages.GeneralConfiguration.ASK_INTERFACE)
    interface_command = 'int {0}'.format(selected_interface)

    interface_configuration_commands = [interface_command,
                                        'no shutdown',
                                        'exit']

    device.send_config_set(interface_configuration_commands)
    return 0


def device_selection_menu(device_selection=0):
    """
    Let a user choose a device that was entered to the script
    :return: The device object the was chosen
    """
    device_verify = False

    while (not device_verify) and (device_selection == 0):
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


def router_conf_menu():
    num_verify = False
    menu_selection = 0
    while not num_verify:
        menu_selection = input(script_messages.RouterMenuStrings.ROUTER_MENU)
        num_verify = is_number(menu_selection)
        if not num_verify:
            print(script_messages.VALUE_NOT_A_NUMBER)

    menu_selection = int(menu_selection)
    if menu_selection == 0:
        # Exit the router configuration menu
        return True
    elif menu_selection == 1:
        # Configure an interface
        selected_device = device_selection_menu(1)
        configure_interface(selected_device)
    elif menu_selection == 2:
        # Configure router ospf
        selected_device = device_selection_menu(1)
        configure_ospf(selected_device)
    elif menu_selection == 3:
        #  Show current interfaces configuration
        selected_device = device_selection_menu(1)
        show_interfaces(selected_device)
    elif menu_selection == 4:
        # Show current ip routing table
        selected_device = device_selection_menu(1)
        show_ip_routing_table(selected_device)
    elif menu_selection == 5:
        # Turn on an interface
        selected_device = device_selection_menu(1)
        interface_shutdown_mode(selected_device)
    return False


def switch_conf_menu():
    """
    Switch configuration menu
    :return: boolean value to determine if exit the menu or not
    """
    num_verify = False
    menu_selection = 0
    while not num_verify:
        menu_selection = input(script_messages.SwitchMenuStrings.SWITCH_MENU)
        num_verify = is_number(menu_selection)
        if not num_verify:
            print(script_messages.VALUE_NOT_A_NUMBER)

    menu_selection = int(menu_selection)
    if menu_selection == 0:
        # Exit the switch configuration menu
        return True
    elif menu_selection == 1:
        # Create a vlan
        selected_device = device_selection_menu(2)
        create_vlan(selected_device)
    elif menu_selection == 2:
        # Configure vlan interface settings
        selected_device = device_selection_menu(2)
        configure_vlan(selected_device)
    elif menu_selection == 3:
        # Show current vlan settings
        selected_device = device_selection_menu(2)
        show_vlan(selected_device)
    elif menu_selection == 4:
        # Show MAC table
        selected_device = device_selection_menu(2)
        show_mac_table(selected_device)
    return False


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
    elif menu_selection == 2:
        # Enter Switch Settings menu
        exit_menu = False
        while not exit_menu:
            exit_menu = switch_conf_menu()
    elif menu_selection == 3:
        exit_menu = False
        while not exit_menu:
            exit_menu = router_conf_menu()

    return False


def main():
    print("Cisco configuration script")
    exit_script = False
    while not exit_script:
        exit_script = main_menu()


if __name__ == "__main__":
    main()
