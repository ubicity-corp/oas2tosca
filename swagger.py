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


