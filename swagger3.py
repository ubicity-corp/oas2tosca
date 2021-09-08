#
# Module for converting Swagger 3.0 files to TOSCA
#
__author__ = "Chris Lauwers"
__copyright__ = "Copyright (c) 2021, Ubicity Corp."
__version__ = "0.0.1"
__email__ = "lauwers@ubicity.com"
__status__ = "Prototype"

# Logging support
import logging
logger = logging.getLogger(__name__)

# System support
import swagger

class Swagger3(swagger.Swagger):

    def convert(self):
        """ The k8s swagger file has the following sections:
          - definitions
          - info
          - paths
          - security
          - securityDefinitions
          - swagger
        """
        
        # Print which keys we have
        for key in self.data.keys():
            print(key)
            
