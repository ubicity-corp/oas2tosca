#
# Module for reading swagger JSON
#
__author__ = "Chris Lauwers"
__copyright__ = "Copyright (c) 2020-2021, Ubicity Corp."
__version__ = "0.0.1"
__email__ = "lauwers@ubicity.com"
__status__ = "Prototype"

# Logging support
import logging
logger = logging.getLogger(__name__)

# YAML support. We'll use a YAML reader to read JSON
from ruamel.yaml import YAML

# System support
import sys

def read_swagger(swagger_file_name):
    """Parse swagger file content (in JSON) using the YAML parser

    Args:
      swagger_file_name(str): name of the swagger file

    Returns:
      dict containing parsed YAML data

    Raises:
      IOError: when unable to read file
      
    """

    # Open file
    swagger_file = open(swagger_file_name)

    # Read JSON data from the swagger file
    swagger_file_data = swagger_file.read()

    # Return parsed file content as YAML. We use the RoundTripLoader
    # (the default) since it stores line numbers in the comments
    # section.
    yaml = YAML()
    return yaml.load(swagger_file_data)
