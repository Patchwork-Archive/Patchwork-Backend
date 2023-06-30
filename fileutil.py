import configparser

def read_config(file_path: str):
    """
    Reads a config file and returns a dictionary of the config
    :param: file_path: str
    :return: dict
    """
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

def check_file_exists(file_path: str):
    """
    Checks if a file exists
    :param: file_path: str
    :return: bool
    """
    try:
        open(file_path)
        return True
    except FileNotFoundError:
        return False