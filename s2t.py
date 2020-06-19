#
# Command-Line tool for converting swagger to TOSCA data types
#
__author__ = "Chris Lauwers"
__copyright__ = "Copyright (c) 2020, Ubicity Corp."
__version__ = "0.0.1"
__email__ = "lauwers@ubicity.com"
__status__ = "Prototype"

# Logging support
import logging
logger = logging.getLogger(__name__)

# Parse command line arguments
import argparse

# File system manipulation functions
import os

# JSON support
import json

# Support for swagger files
import swagger

#
# Create top-level command line argument parser
#
parser = argparse.ArgumentParser(description='Convert Swagger to TOSCA')
parser.add_argument('-d', '--debug', action='store_true', default=False,
                    help='turn on debug logging')

parser.add_argument('-i', '--input', action='store', help='swagger input file')
parser.add_argument('-o', '--output', action='store', help='tosca output file')

#
# Parse command line
#
args = parser.parse_args()

#
# Initialize logging
#
if args.debug is True:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# Execute 
if args.input:
    logger.debug("Input file: %s", args.input)
else:
    logger.error("No input file specified")
    exit(1)
    
if args.output:
    logger.debug("TOSCA output file: %s", args.output)

# Create swagger processor
swagger = swagger.Swagger()

# Read swagger input
errors = swagger.read(args.input)
if errors:
    logger.error("Error reading <%s>:\n%s",
                 swagger.file_name,
                 json.dumps(errors, ensure_ascii=False, indent=2))

# Convert to TOSCA    
swagger.convert()

# Write
swagger.write(args.output)

