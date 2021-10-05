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

def get_version(data):
    """Return the version of the OpenAPI/Swagger data. TODO: return
    semantic version components.

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
    """Version-independent swagger object. Version-dependent processing is
    defined in version-specific subclasses
    """

    def __init__(self, swagger_data):
        """Constructor """

        # First, call superclass constructor
        super(Swagger, self).__init__()

        # Track the swagger data
        self.data = swagger_data

        # Track types to avoid creating duplicates
        self.node_types = set()
        self.data_types = set()

        # Track schemas from which to create data types
        self.definitions = set()
        

    def convert(self, top):
        """Convert a Swagger object to TOSCA type definitions and write
        these definitions to profile directories under 'top'.

        The conversion process works as follows:

        1. Scan all the schemas defined in the swagger file, and
           generate a set of 'TOSCA Profile Names' from the
           corresponding schema names. For each profile, also track
           the other profiles on which the profile depends
           (e.g. because properties use schemas defined in other
           profiles).

        2. Scan all the “paths” in the swagger file to find those path
           objects that include a POST operation (under the assumption
           that those paths represent objects that can be
           “instantiated”).

        3. Create TOSCA Node Types based on the schemas used for the
           payload in the POST operation.

        4. For each property defined in those payload schemas, find
           the corresponding schema in the swagger file that is used
           as the “type” for that property, and create a corresponding
           data type.

        """
        # Get the names of the profiles that need to be created and
        # their dependencies on other profiles
        self.get_profile_names()

        # Create the directories within which each profile will be
        # created.
        self.initialize_profiles(top, self.get_info())

        # Extract node types from 'path' objects
        self.process_paths()

        # Create data types based on 'definitions'
        self.process_definitions()

        # Clean up
        self.finalize_profiles()


    def get_profile_names(self):
        """For each schema defined in the Swagger object, parse the schema
        name into a 'profile' name and a 'resource' name. We use these
        profile names to generate the set of profiles that need to be
        created.  For each schema, we also find the schemas used in
        property definitions. The 'profile' parts of those schema
        names determine other profiles on which each profile depends
        """

        self.profiles = dict()

        # Get the set of schema definitions
        definitions = self.get_definitions()

        # Process each schema definition
        for schema_name, schema in definitions.items():
            self.get_profile_names_from_schema(schema_name, schema)


    def get_info(self):
        """Retrieve the (required) Info Object. This object provides metadata
        about the API. The metadata can be used by the clients if
        needed. 

        A swagger Info Object has the following properties:

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
        group, version, kind, prefix = self.parse_schema_name(schema_name, schema)
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

        # Parse group, version, and kind from the schema name. 
        group, version, kind, prefix = self.parse_schema_name(schema_name, schema)
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


    def parse_schema_name(self, schema_name, schema):
        """Parse schema name into a type info tuple that consists of
        'profile', 'version', 'name', and 'prefix'.
        """

        # Try to extract the model name from the schema.
        try:
            model_name = schema['x-swagger-router-model']
        except KeyError:
            # No router model. Just use schema name
            model_name = schema_name

        # Split schema name using '.' separator
        split = model_name.split('.')
        length = len(split)

        # If there is only one part, just return the model name as the
        # type name.
        if length < 2:
            return "", "", model_name, ""

        # If there are two parts, split the model name into a profile
        # name and a type, and use the model name as the prefix.
        if length == 2:
            return split[0], "", split[1], split[0]

        # Check if there is a version string. Versions start with 'v1'
        # or 'v2'
        if split[length-2][:2] == 'v1' or split[length-2][:2] == 'v2':
            version = split[length-2]
            prefix = split[length-3]
            profile = ".".join(split[0:length-2])
        else:
            version = ""
            prefix = split[length-2]
            profile = ".".join(split[0:length-1])
        name = split[length-1]
        return (profile, version, name, prefix)


