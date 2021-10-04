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


def get_version(data):
    """Return the version of the OpenAPI/Swagger data

    Args:
      data(dict): OpenAPI document

    Returns
      version(string)

    Raises:
      KeyError: when no version information found
    """

    try:
        # OpenAPI v2 uses the 'swagger' attribute to store version
        # information
        return data['swagger']
    except KeyError:
        # OpenAPI v3 uses the 'openapi' attribute to store version
        # information
        return data['openapi']


class Swagger(object):
    """Version-independent swagger object"""

    def __init__(self, swagger_data):
        """Constructor """

        # First, call superclass constructor
        super(Swagger, self).__init__()

        # Initialize
        self.data = swagger_data
        self.tosca = dict()


    def get_info(self):
        """Process the (required) Info Object. This object provides metadata
        about the API. The metadata can be used by the clients if
        needed. A swagger 2 Info Object has the following properties:

        title(string): Required. The title of the application.

        description(string): A short description of the
          application. GFM syntax can be used for rich text
          representation.

        termsOfService(string): The Terms of Service for the API.

        contact(Contact Object): The contact information for the
          exposed API.

        license(License Object): The license information for the
          exposed API.

        version(string): Required Provides the version of the
          application API (not to be confused with the specification
          version)

        """
        return self.data['info']


    def initialize_profiles(self, top, info):
        for name, profile in self.profiles.items():
            profile.initialize(top, info)
        
    def finalize_profiles(self):
        for name, profile in self.profiles.items():
            profile.finalize()
        
