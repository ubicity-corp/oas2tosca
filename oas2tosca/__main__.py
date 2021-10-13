# Command-Line tool for converting an OpenAPI Specificaton file to one
# or more TOSCA profiles
#
__author__ = "Chris Lauwers"
__copyright__ = "Copyright (c) 2020-2021, Ubicity Corp."
__version__ = "0.0.1"
__email__ = "lauwers@ubicity.com"
__status__ = "Prototype"

# Logging support
import logging
logger = logging.getLogger(__name__)

# Parse command line arguments
import argparse

# Support for swagger files
from read import read_swagger
import swagger as sw
import swagger2
import swagger3


def main():
    """Invoke OpenAPI to TOSCA converter"""

    # Create top-level command line argument parser
    parser = argparse.ArgumentParser(description='Convert Swagger to TOSCA')
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='turn on debug logging')

    parser.add_argument('-i', '--input', action='store', help='swagger input file')
    parser.add_argument('-o', '--output', action='store', help='tosca output directory')

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
        swagger_data = read_swagger(args.input)
    except Exception as e:
        logger.error("Error reading '%s': %s", args.input, str(e))
        exit(1)

    # Invoke the appropriate converter
    try:
        swagger_version = sw.get_version(swagger_data)
        if swagger_version[0] == '2':
            logger.info("Converting Swagger 2.0 file")
            swagger = swagger2.Swagger2(swagger_data)
        elif swagger_version[0] == '3':
            logger.info("Converting Swagger 3.0 file")
            swagger = swagger3.Swagger3(swagger_data)
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