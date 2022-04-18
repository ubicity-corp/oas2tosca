# Command-Line tool for converting an OpenAPI Specificaton file to one
# or more TOSCA profiles
#
__author__ = "Chris Lauwers"
__copyright__ = "Copyright (c) 2020-2022, Ubicity Corp."
__email__ = "lauwers@ubicity.com"

# Logging support
import logging
logger = logging.getLogger(__name__)

# Parse command line arguments
import argparse

# Version string
from . import __version__

# Support for swagger files
import oas2tosca.read_oas as ro
import oas2tosca.swagger as sw
import oas2tosca.swagger2 as sw2
import oas2tosca.swagger3 as sw3


def main():
    """Invoke OpenAPI to TOSCA converter"""

    # Create top-level command line argument parser
    parser = argparse.ArgumentParser(description='Convert Swagger to TOSCA')
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='turn on debug logging')

    parser.add_argument('-i', '--input', action='store', help='swagger input file')
    parser.add_argument('-o', '--output', action='store', help='tosca output directory')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + str(__version__))

    # Parse command line
    args = parser.parse_args()

    # Initialize logging
    if args.debug is True:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Get input file and output directory
    if args.input:
        logger.debug("Input file: %s", args.input)
    else:
        logger.error("No input file specified")
        exit(1)
    if args.output:
        logger.debug("TOSCA output directory: %s", args.output)

    # Read swagger input
    try:
        swagger_data = ro.read_swagger(args.input)
    except Exception as e:
        logger.error("Error reading '%s': %s", args.input, str(e))
        exit(1)

    # Invoke the appropriate converter
    try:
        swagger_version = sw.get_version(swagger_data)
        if swagger_version[0] == '2':
            logger.debug("Converting Swagger 2.0 file")
            swagger = sw2.Swagger2(swagger_data)
        elif swagger_version[0] == '3':
            logger.debug("Converting Swagger 3.0 file")
            swagger = sw3.Swagger3(swagger_data)
        else:
            logger.error("Unsupported Swagger version %s", swagger_version)
            exit(2)
    except KeyError:
        logger.error("Swagger version not specified")
        exit(3)

    # Convert
    try:
        swagger.convert(args.output)
    except Exception as e:
        logger.error("Error converting '%s': %s", args.input, str(e))
        exit(4)


# Main
if __name__ == "__main__":
    main()
