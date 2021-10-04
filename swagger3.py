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

# Profiles
import profile as p

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

        # First, get profiles
        self.get_profile_names()
        
        # Create the directories within which each profile will be
        # created.
        self.initialize_profiles(top, self.get_info())

        # Extract node types from 'path' objects
        self.process_paths()


    def get_profile_names(self):
        """Scan the 'components' section of the Swagger object to find the
        supported 'schemas'. For each schema definition, find the
        'x-swagger-router-model' keyword and split it into a profile
        name and resource name.
        """

        self.profiles = dict()

        # Make sure this swagger file has schemas
        try:
            schemas = self.data['components']['schemas']
        except KeyError:
            logger.debug("No Schemas")
            return

        # Process each schema definition
        for name, schema in schemas.items():
            self.get_profile_names_from_schema(name, schema)


    def get_profile_names_from_schema(self, name, schema):
        """Find profile names in a schema definition"""
        
        # Extract the profile name from the schema name.
        try:
            schema_name = schema['x-swagger-router-model']
            profile_name, version, resource, prefix = parse_schema_name(schema_name)
        except KeyError:
            logger.error("%s: no 'x-swagger-router-model'", name)
            return

        # Get profile object
        try:
            profile = self.profiles[profile_name]
        except KeyError:
            profile = p.Profile(profile_name, "", prefix)
            self.profiles[profile_name] = profile

        # Schemas are referenced by property definitions
        try:
            properties = schema['properties']
        except KeyError:
            # No properties
            return

        # Do any properties reference schemas?
        for property_name, property_value in properties.items():
            try:
                # No type specified. Use $ref instead
                property_schema = self.get_referenced_schema(property_value['$ref'])
                property_type = property_schema['x-swagger-router-model']
                property_profile, version, property_resource, prefix = parse_schema_name(property_type)
                if property_profile != property_profile:
                    profile.add_dependency(property_profile, prefix)
            except KeyError:
                # Property schema does not contain a $ref. Items
                # perhaps?
                try:
                    items = property_value['items']
                    property_schema = self.get_referenced_schema(items['$ref'])
                    property_type = property_schema['x-swagger-router-model']
                    property_profile, version, property_resource, prefix = parse_schema_name(property_type)
                    if property_profile != property_profile:
                        profile.add_dependency(property_profile, prefix)
                except KeyError:
                    # No items either. additionalProperties?
                    try:
                        additionalProperties = property_value['additionalProperties']
                        property_schema = self.get_referenced_schema(additionalProperties['$ref'])
                        property_type = property_schema['x-swagger-router-model']
                        property_profile, version, property_resource, prefix = parse_schema_name(property_type)
                        if property_profile != property_profile:
                            profile.add_dependency(property_profile, prefix)
                    except KeyError:
                        pass
        

    def get_referenced_schema(self, ref):
        # Only support local references for now
        try:
            if ref[0] != '#':
                logger.error("%s: not a local reference", ref)
                return None
        except Exception as e:
            logger.error("%s: not a ref (%s)", str(ref), str(e))
            return None
        # Make sure we reference a schema
        prefix = "#/components/schemas/"
        if not ref.startswith(prefix):
            return None

        # Strip prefix
        schema_name = ref[len(prefix):]
        try:
            return self.data['components']['schemas'][schema_name]
        except KeyError:
            logger.error("%s: not a ref to a schema", ref)
            return None


    def process_paths(self):
        pass
    

def parse_schema_name(schema_name):
    """Parse schema name into 'profile', 'resource', and 'prefix' tuple.
    """

    # Split schema name using '.' separator
    split = schema_name.split('.')
    length = len(split)

    # Don't bother splitting if there are not enough parts.
    if length < 2:
        return "", "", schema_name, ""
        
    prefix = split[length-2]
    profile = ".".join(split[0:length-1])
    resource = split[length-1]
    version = ""
    return (profile, version, resource, prefix)


                    
