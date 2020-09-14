import netmiko
VALUE_NOT_A_NUMBER = "A value you entered is not a number, please try again"
WARN_FILE_DOES_NOT_EXIST = "Warning: this file does not exist"


class AddDeviceStrings:
    """
    This class contains strings constants for the device add function
    """
    IP_ADDRESS_ASK = "Enter an IP address > "
    PORT_ASK = "Enter the destination port > "
    DEVICE_TYPE_ASK = "Please choose type: 1. IOU 2. Switch > "
    DEVICES_INI_PATH_ASK = "Please enter path to devices file\n> "

    BAD_PORT_INPUT = "Bad input, please enter a valid port number between 0 and 65535"
    BAD_DEVICE_TYPE_SELECTION = "Bad Input, please select either device 1 or 2"

    ERR_BAD_PATH = "The path you provided for the ini file is bad"
    ERR_SOCKET_GAIERROR = "IP address is bad; or there is no connection, please try again."
    ERR_CONNECTION_REFUSED = "Target actively refused to connect, is this the right port?"
    ERR_CONNECTION_GENERAL = "There was something wrong with the connection, please try again"
    ERR_LOGIN_FAILED = "An error occurred when trying to connect to the device, please try again"

    ASK_TRY_AGAIN = "Device not added, try again?"


class MainMenuStrings:
    """
    This class contains main menu strings
    """
    MAIN_MENU = "Select an option: \n0.Exit \n1.Add a device \n>"
    ASK_AUTO_ADD_DEVICE = "Do you want to add devices from ini file?"
    IOU_OR_SWITCH = "Select device type: \n1.IOU \n2.SWITCH \n>"


def device_selection(devices):
    """
    This function creates a device selection prompt
    :param devices: array of device objects
    :return: String for the device selection prompt
    """
    devices = generate_device_list(devices)
    return "Please select a device:\n {0}>".format(devices)


def generate_device_list(device_array):
    """
    This function generates device name list to choose from
    :param device_array: array of devices
    :return: String that contains list of devices
    """
    prompts = ''
    list_index = 0
    for device in device_array:
        prompts = prompts + '{index}. {device_name}\n'.format(index=list_index, device_name=device.find_prompt())
        list_index += 1
    return prompts


def ask_yes_or_not():
    """
    Ask for y or n input
    :return: string, 'y' or 'n'
    """
    answer = input('(y/n) >')
    while not answer == 'y' or answer == 'n':
        answer = input('wrong input, please select (y)es or (n)ot >')
    return answer
