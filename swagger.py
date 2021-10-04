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
        
    def process_paths(self):
        """Process the (required) Paths Object, which defines a list of
        available paths and associated operations for the API.
        """
        # Check if this swagger file has paths
        try:
            paths = self.data['paths']
            logger.debug("Processing Paths Object")
        except KeyError:
            paths = None
        if not paths:
            logger.error("No Paths Object")
            return

        for name, value in paths.items():
            self.process_path_object(name, value)

            


    def process_path_object(self, name, value):
        """A Path Object in Swagger 2 has the following:

        $ref(string): Allows for an external definition of this path
          item. The referenced structure MUST be in the format of a
          Path Item Object. If there are conflicts between the
          referenced definition and this Path Item's definition, the
          behavior is undefined.
        get(Operation Object): A definition of a GET operation on this
          path.
        put(Operation Object): A definition of a PUT operation on this
          path.
        post(Operation Object): A definition of a POST operation on
          this path.
        delete(Operation Object): A definition of a DELETE operation
          on this path.
        options(Operation Object): A definition of a OPTIONS operation
          on this path.
        head(Operation Object): A definition of a HEAD operation on
          this path.
        patch(Operation Object): A definition of a PATCH operation on
          this path.
        parameters([Parameter Object | Reference Object]): A list of
          parameters that are applicable for all the operations
          described under this path. These parameters can be
          overridden at the operation level, but cannot be removed
          there. The list MUST NOT include duplicated parameters. A
          unique parameter is defined by a combination of a name and
          location. The list can use the Reference Object to link to
          parameters that are defined at the Swagger Object's
          parameters. There can be one "body" parameter at most.

        In addition, Swagger 3 adds the following:

        summary(string): An optional, string summary, intended to
          apply to all operations in this path.

        description(string): An optional, string description, intended
          to apply to all operations in this path. CommonMark syntax
          MAY be used for rich text representation.

        trace(Operation Object): A definition of a TRACE operation on
          this path.

        servers([Server Object]): An alternative server array to
          service all operations in this path.
        """

        # Can we create a resource on this path?
        try:
            post = value['post']
        except KeyError:
            post = None
        if not post:
            logger.debug("'%s' does not have POST", name)
            return
        
        # Are there path-level parameters?
        try:
            parameters = value['parameters']
        except KeyError:
            parameters = list()
        logger.debug("'%s' parameters:", name)
        for parameter in parameters:
            self.process_parameter_object(name, parameter)
            
        self.process_operation_object(name, post)

        
    def create_node_type_from_schema(self, schema_name, schema):
        """Create a TOSCA node type from a JSON Schema"""
        
        # Avoid duplicates
        if schema_name in self.node_types:
            logger.info("%s: duplicate", schema_name)
            return
        self.node_types.add(schema_name)
        
        # If this schema is intended to define a node type, the schema
        # 'type' better be 'object'.
        try:
            if not schema['type'] == 'object':
                logger.error("Node type '%s' with type '%s'", schema_name, schema['type'])
                return
        except KeyError:
                logger.error("Trying to create node type '%s' without a type",
                             schema_name)
                return

        # Parse group, version, prefix, and kind from the schema name. 
        group, version, kind, prefix = parse_schema_name(schema_name)
        # For now, we only handle v1
        if version and version != 'v1':
            logger.debug("Ignoring %s version of %s", version, kind)
            return

        # k8s 'resources' include a 'x-kubernetes-group-version-kind'
        # attribute. Note that the value of
        # 'x-kubernetes-group-version-kind' is a list. Not sure why.
        try:
            group_version_kind_list = schema['x-kubernetes-group-version-kind']
        except KeyError:
            logger.error("%s: creating node type without group version kind", schema_name)

        # Make sure we plan to define data types for any properties
        # defined in this schema
        self.plan_data_types_for_properties(schema)

        # Create the node type in the profile for this schema
        profile = self.profiles[group]
        profile.emit_node_type(kind, schema)
        

    def process_definitions(self):
        """Process the Definitions Object which holds data types produced and
        consumed by operations.

        """
        # Make sure this swagger file has definitions
        definitions = self.get_definitions()
        for definition in self.definitions:
            try:
                value = definitions[definition]
            except KeyError:
                logger.error("Definition %s not found", definition)
                continue
            # Get the schema name
            self.create_data_type_from_schema(definition, value)
            if definition in self.node_types:
                logger.info("%s is also node type", key)


    def create_data_type_from_schema(self, schema_name, schema):
        """Create a TOSCA data type from a JSON Schema"""

        # Avoid duplicates
        if schema_name in self.data_types:
            logger.debug("%s: duplicate", schema_name)
            return
        self.data_types.add(schema_name)

        # If this schema is intended to define a data type, this
        # schema must not reference another schema.
        try:
            ref = schema['$ref']
            logger.error("%s REFERENCES %s", schema_name, ref)
            return
        except KeyError:
            pass

        # Get the full schema name
        schema_name = self.get_full_schema_name(schema_name, schema)
        logger.info("Creating data type for %s", schema_name)
        
        # Parse group, version, and kind from the schema name. 
        group, version, kind, prefix = parse_schema_name(schema_name)
        logger.info("In profile %s", group)
        
        # We only handle v1 for now
        if version and version != "v1":
            logger.info("Ignoring %s version of %s", version, kind)
            return
        
        # k8s schemas for data types must not include a
        # 'x-kubernetes-group-version-kind' attribute. Note that the
        # value of 'x-kubernetes-group-version-kind' is a list. Not
        # sure why.
        try:
            group_version_kind_list = schema['x-kubernetes-group-version-kind']
            logger.error("%s: creating data type with group version kind", schema_name)
        except KeyError:
            pass
        
        # Make sure we define data types for any properties defined in
        # this schema
        try:
            self.create_data_types_for_properties(schema)
        except Exception as e:
            logger.error("%s: %s", schema_name, str(e))

        # Create the data type in the profile for this schema
        profile = self.profiles[group]
        profile.emit_data_type(kind, schema)


    def create_data_types_for_properties(self, schema):
        """Create data types for property schemas referenced in this schema
        """
        # Does this schema have property definitions?
        try:
            properties = schema['properties']
        except KeyError:
            # No properties
            return

        # Do any properties reference schemas?
        for property_name, property_schema in properties.items():
            try:
                schema_name = self.get_ref(property_schema['$ref'])
                self.create_data_type_from_schema(schema_name,
                                                  self.data['definitions'][schema_name])
            except KeyError:
                # Property schema does not contain a $ref. Items
                # perhaps?
                try:
                    items = property_schema['items']
                    schema_name = self.get_ref(items['$ref'])
                    self.create_data_type_from_schema(schema_name,
                                                      self.data['definitions'][schema_name])
                except KeyError:
                    try:
                        additionalProperties = property_schema['additionalProperties']
                        schema_name = self.get_ref(additionalProperties['$ref'])
                        self.create_data_type_from_schema(schema_name,
                                                          self.data['definitions'][schema_name])
                    except KeyError:
                        # No additional schemas
                        pass
                    pass



def parse_schema_name(schema_name):
    """Parse schema name into 'group', 'version', 'kind', and 'prefix'
    tuple.
    """

    # Split schema name using '.' separator
    split = schema_name.split('.')
    length = len(split)

    # Don't bother splitting if there are not enough parts.
    if length < 3:
        return "", "", schema_name, ""
        
    # Versions start with 'v1' or 'v2'
    if split[length-2][:2] == 'v1' or split[length-2][:2] == 'v2':
        version = split[length-2]
        prefix = split[length-3]
        group = ".".join(split[0:length-2])
    else:
        version = ""
        prefix = split[length-2]
        group = ".".join(split[0:length-1])
    kind = split[length-1]
    return (group, version, kind, prefix)


