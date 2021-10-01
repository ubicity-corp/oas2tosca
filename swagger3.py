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

    def convert(self, top):
        """An OpenAPI v3 file has the following sections:

        openapi(string): REQUIRED. This string MUST be the semantic
          version number of the OpenAPI Specification version that the
          OpenAPI document uses. The openapi field SHOULD be used by
          tooling specifications and clients to interpret the OpenAPI
          document. This is not related to the API info version
          string.

        info (Info Object): REQUIRED. Provides metadata about the
          API. The metadata MAY be used by tooling as required.

        servers([Server Object)]: An array of Server Objects, which
          provide connectivity information to a target server. If the
          servers property is not provided, or is an empty array, the
          default value would be a Server Object with a url value of
          /.

        paths (Paths Object): REQUIRED. The available paths and
          operations for the API.

        components (Components Object): An element to hold various
          schemas for the specification.

        security ([Security Requirement Object)]: A declaration of
          which security mechanisms can be used across the API. The
          list of values includes alternative security requirement
          objects that can be used. Only one of the security
          requirement objects need to be satisfied to authorize a
          request. Individual operations can override this
          definition. To make security optional, an empty security
          requirement ({}) can be included in the array.

        tags ([Tag Object)]: A list of tags used by the specification
          with additional metadata. The order of the tags can be used
          to reflect on their order by the parsing tools. Not all tags
          that are used by the Operation Object must be declared. The
          tags that are not declared MAY be organized randomly or
          based on the tools' logic. Each tag name in the list MUST be
          unique.

        externalDocs (External Documentation Object): Additional
          external documentation.
        """

        logger.info("Converting OAS3 file into %s", top)
        
