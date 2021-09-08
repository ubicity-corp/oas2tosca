#
# Module for converting Swagger files to TOSCA
#
__author__ = "Chris Lauwers"
__copyright__ = "Copyright (c) 2021-2021, Ubicity Corp."
__version__ = "0.0.1"
__email__ = "lauwers@ubicity.com"
__status__ = "Prototype"

# Logging support
import logging
logger = logging.getLogger(__name__)

# System support
import sys

# YAML support. 
from ruamel.yaml import YAML

class Swagger(object):

    def __init__(self, swagger_data):
        """Constructor """

        # First, call superclass constructor
        super(Swagger, self).__init__()

        # Initialize
        self.data = swagger_data
        self.tosca = dict()
        self.unhandled = set()


    def write(self, output_file_name):
        """Write out TOSCA"""
        
        tosca = dict()
        tosca['tosca_definitions_version'] = 'tosca_simple_yaml_1_3'
        tosca['data_types'] = self.tosca
        
        # Open file if file name given
        if output_file_name:
            try:
                out = open(output_file_name, "w+")
            except IOError as e:
                logger.error("Unable to open file '%s", output_file_name)
                return
        else:
            out = sys.stdout
            
        # Dump YAML
        yaml = YAML()
        try:
            yaml.dump(tosca, out)
        except Exception as e:
            logger.error("Unable to write: '%s", str(e))
            return

        logger.info("Unhandled: %s", str(self.unhandled))
            
