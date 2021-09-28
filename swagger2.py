#
# Module for converting Swagger 2.0 files to TOSCA
#
__author__ = "Chris Lauwers"
__copyright__ = "Copyright (c) 2020-2021, Ubicity Corp."
__version__ = "0.0.1"
__email__ = "lauwers@ubicity.com"
__status__ = "Prototype"

# Logging support
import logging
logger = logging.getLogger(__name__)

# System support
import swagger

# Profiles
import profile as p

# Text formatting
import textwrap

class Swagger2(swagger.Swagger):

    def convert(self, top):
        """Convert a Swagger v2 object to TOSCA type definitions and write
        these definitions to profile directories under 'top'.

        A swagger 2 object is has the following properties:

        swagger(string): Required. Specifies the Swagger Specification
          version being used. It can be used by the Swagger UI and
          other clients to interpret the API listing. The value MUST
          be "2.0".

        info(Info Object): Required. Provides metadata about the
          API. The metadata can be used by the clients if needed.

        host(string): The host (name or ip) serving the API. This MUST
          be the host only and does not include the scheme nor
          sub-paths. It MAY include a port. If the host is not
          included, the host serving the documentation is to be used
          (including the port). The host does not support path
          templating.

        basePath(string): The base path on which the API is served,
          which is relative to the host. If it is not included, the
          API is served directly under the host. The value MUST start
          with a leading slash (/). The basePath does not support path
          templating.

        schemes([string]): The transfer protocol of the API. Values
          MUST be from the list: "http", "https", "ws", "wss". If the
          schemes is not included, the default scheme to be used is
          the one used to access the Swagger definition itself.

        consumes([string]): A list of MIME types the APIs can
          consume. This is global to all APIs but can be overridden on
          specific API calls. Value MUST be as described under Mime
          Types.

        produces([string]): A list of MIME types the APIs can
          produce. This is global to all APIs but can be overridden on
          specific API calls. Value MUST be as described under Mime
          Types.

        paths(Paths Object): Required. The available paths and
          operations for the API.

        definitions(Definitions Object): An object to hold data types
          produced and consumed by operations.

        parameters(Parameters Definitions Object): An object to hold
          parameters that can be used across operations. This property
          does not define global parameters for all operations.

        responses(Responses Definitions Object): An object to hold
          responses that can be used across operations. This property
          does not define global responses for all operations.

        securityDefinitions(Security Definitions Object): Security
          scheme definitions that can be used across the
          specification.

        security([Security Requirement Object]): A declaration of
          which security schemes are applied for the API as a
          whole. The list of values describes alternative security
          schemes that can be used (that is, there is a logical OR
          between the security requirements). Individual operations
          can override this definition.

        tags([Tag Object]): A list of tags used by the specification
          with additional metadata. The order of the tags can be used
          to reflect on their order by the parsing tools. Not all tags
          that are used by the Operation Object must be declared. The
          tags that are not declared may be organized randomly or
          based on the tools' logic. Each tag name in the list MUST be
          unique.

        externalDocs(External Documentation Object): Additional
          external documentation.

        """
        # Track types to avoid creating duplicates
        self.node_types = set()
        self.data_types = set()

        # Track definitions from which to create data types
        self.definitions = set()
        
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

        self.finalize_profiles()

        """
        # Are any of these needed?
        self.process_parameters()
        self.process_responses()
        self.process_securityDefinitions()
        self.process_security()
        self.process_tags()
        self.process_externalDocs()
        """

    def get_profile_names(self):
        """Scan the 'definitions' section of the Swagger object and parse out
        the 'group' section of each schema definition. We will use
        that group name as the profile name. For each schema, we also
        find the schemas used in property definitions. The group names
        of those schemas determine other profiles on which each
        profile depends
        """

        self.profiles = dict()

        # Make sure this swagger file has definitions
        try:
            definitions = self.data['definitions']
        except KeyError:
            logger.debug("No Definitions")
            return

        # Process each schema definition
        for schema_name, schema in definitions.items():
            self.get_profile_names_from_schema(schema_name, schema)


    def get_profile_names_from_schema(self, schema_name, schema):
        # Extract the group name from the schema name. This group name
        # will be used as the profile name.
        group, version, kind, prefix = parse_schema_name(schema_name)
        if not group:
            logger.error("%s: no group", schema_name)
            return

        # We only handle 'v1' schemas for now
        if version and version != "v1":
            logger.debug("Ignoring %s", schema_name)
            return

        # Get profile object
        try:
            profile = self.profiles[group]
        except KeyError:
            profile = p.Profile(group, version, prefix)
            self.profiles[group] = profile

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
                property_type = self.get_ref(property_value['$ref'])
                property_group, version, kind, prefix = parse_schema_name(property_type)
                if group != property_group:
                    profile.add_dependency(property_group, prefix)
            except KeyError:
                # Property schema does not contain a $ref. Items
                # perhaps?
                try:
                    items = property_value['items']
                    property_type = self.get_ref(items['$ref'])
                    property_group, version, kind, prefix = parse_schema_name(property_type)
                    if group != property_group:
                        profile.add_dependency(property_group, prefix)
                except KeyError:
                    # No items either. additionalProperties?
                    try:
                        additionalProperties = property_value['additionalProperties']
                        property_type = self.get_ref(additionalProperties['$ref'])
                        property_group, version, kind, prefix = parse_schema_name(property_type)
                        if group != property_group:
                            profile.add_dependency(property_group, prefix)
                    except KeyError:
                        pass


    def initialize_profiles(self, top, info):
        for name, profile in self.profiles.items():
            profile.initialize(top, info)
        
    def finalize_profiles(self):
        for name, profile in self.profiles.items():
            profile.finalize()
        

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


    def process_host(self):
        """Process the host (name or ip) serving the API. This MUST be the
        host only and does not include the scheme nor sub-paths. It
        MAY include a port. If the host is not included, the host
        serving the documentation is to be used (including the
        port). The host does not support path templating.
        """
        try:
            host = self.data['host']
            logger.debug("Processing Host")
        except KeyError:
            logger.debug("No Host")
            return


    def process_basePath(self):
        """Process the base path on which the API is served, which is relative
        to the host. If it is not included, the API is served directly
        under the host. The value MUST start with a leading slash
        (/). The basePath does not support path templating.
        """
        try:
            basePath = self.data['basePath']
            logger.debug("Processing BasePath")
        except KeyError:
            logger.debug("No BasePath")
            return


    def process_schemes(self):
        """Process the transfer protocol of the API. Values MUST be from the
        list: "http", "https", "ws", "wss". If the schemes is not
        included, the default scheme to be used is the one used to
        access the Swagger definition itself.
        """
        try:
            schemes = self.data['schemes']
            logger.debug("Processing Schemes")
        except KeyError:
            logger.debug("No Schemes")
            return


    def process_consumes(self):
        """Process the list of MIME types the APIs can consume. This is global
        to all APIs but can be overridden on specific API calls. Value
        MUST be as described under Mime Types.

        """
        try:
            consumes = self.data['consumes']
            logger.debug("Processing Consumes")
        except KeyError:
            logger.debug("No Consumes")
            return


    def process_produces(self):
        """Process the list of MIME types the APIs can produce. This is global
        to all APIs but can be overridden on specific API calls. Value
        MUST be as described under Mime Types.

        """
        try:
            produces = self.data['produces']
            logger.debug("Processing Produces")
        except KeyError:
            logger.debug("No Produces")
            return


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
        
            
    def process_operation_object(self, name, value):
        """An Operation Object in Swagger 2 has the following:

        tags([string]): A list of tags for API documentation
          control. Tags can be used for logical grouping of operations
          by resources or any other qualifier.

        summary(string): A short summary of what the operation
          does. For maximum readability in the swagger-ui, this field
          SHOULD be less than 120 characters.

        description(string): A verbose explanation of the operation
          behavior. GFM syntax can be used for rich text
          representation.

        externalDocs(External Documentation Object): Additional
          external documentation for this operation.

        operationId(string): Unique string used to identify the
          operation. The id MUST be unique among all operations
          described in the API. Tools and libraries MAY use the
          operationId to uniquely identify an operation, therefore, it
          is recommended to follow common programming naming
          conventions.

        consumes([string]): A list of MIME types the operation can
          consume. This overrides the consumes definition at the
          Swagger Object. An empty value MAY be used to clear the
          global definition. Value MUST be as described under Mime
          Types.

        produces([string]): A list of MIME types the operation can
          produce. This overrides the produces definition at the
          Swagger Object. An empty value MAY be used to clear the
          global definition. Value MUST be as described under Mime
          Types.

        parameters([Parameter Object | Reference Object]): A list of
          parameters that are applicable for this operation. If a
          parameter is already defined at the Path Item, the new
          definition will override it, but can never remove it. The
          list MUST NOT include duplicated parameters. A unique
          parameter is defined by a combination of a name and
          location. The list can use the Reference Object to link to
          parameters that are defined at the Swagger Object's
          parameters. There can be one "body" parameter at most.

        responses(Responses Object): Required. The list of possible
          responses as they are returned from executing this
          operation.

        schemes([string]): The transfer protocol for the
          operation. Values MUST be from the list: "http", "https",
          "ws", "wss". The value overrides the Swagger Object schemes
          definition.

        deprecated(boolean): Declares this operation to be
          deprecated. Usage of the declared operation should be
          refrained. Default value is false.

        security([Security Requirement Object]): A declaration of
          which security schemes are applied for this operation. The
          list of values describes alternative security schemes that
          can be used (that is, there is a logical OR between the
          security requirements). This definition overrides any
          declared top-level security. To remove a top-level security
          declaration, an empty array can be used

        """
        try:
            parameters = value['parameters']
        except KeyError:
            parameters = list()
        logger.debug("'%s' POST parameters:", name)
        for parameter in parameters:
            self.process_parameter_object(name, parameter)

        
    def process_parameter_object(self, name, value):
        """An Operation Object in Swagger 2 has the following:

        name(string): Required. The name of the parameter. Parameter
          names are case sensitive.
          If in is "path", the name field MUST correspond to the
          associated path segment from the path field in the Paths
          Object. See Path Templating for further information.  For
          all other cases, the name corresponds to the parameter name
          used based on the in property.

        in(string): Required. The location of the parameter. Possible
          values are "query", "header", "path", "formData" or "body".

        description(string): A brief description of the
          parameter. This could contain examples of use. GFM syntax
          can be used for rich text representation.

        required(boolean): Determines whether this parameter is
          mandatory. If the parameter is in "path", this property is
          required and its value MUST be true. Otherwise, the property
          MAY be included and its default value is false.

        schema(Schema Object): Required if 'in' is 'body'. The schema
          defining the type used for the body parameter.
        """

        # We create a node type for any resource that has a POST
        # operation with a 'body' parameter
        if not value['in'] == 'body':
            return

        # We have an operation that can create a resource. Create a
        # node type based on the body schema. For now, we only handle
        # schemas that reference another schema (in which case all
        # other properties in this schema object must be ignored
        # according to the JSONSchema spec)
        schema = value['schema']
        try:
            ref = schema['$ref']
        except KeyError:
            logger.error("%s: creating node type from in-place schema not implemented",
                         name)
            return
        
        # Get the referenced schema
        schema_ref = self.get_ref(ref)
        try:
            node_type_schema = self.data['definitions'][schema_ref]
        except KeyError:
            logger.error("%s: not found", schema_ref)
            return
        
        # Create the node type for the referenced schema
        self.create_node_type_from_schema(schema_ref, node_type_schema)
        

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
        

    def plan_data_types_for_properties(self, schema):
        """Plan the creation of a data type for schemas referenced in this
        schema
        """
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
                property_type = self.get_ref(property_value['$ref'])
                self.definitions.add(property_type)
            except KeyError:
                # Property schema does not contain a $ref. Items
                # perhaps?
                try:
                    items = property_value['items']
                    property_type = self.get_ref(items['$ref'])
                    self.definitions.add(property_type)
                except KeyError:
                    try:
                        additionalProperties = property_value['additionalProperties']
                        property_type = self.get_ref(additionalProperties['$ref'])
                        self.definitions.add(property_type)
                    except KeyError:
                        # No additional schemas
                        pass


    def process_definitions(self):
        """Process the Definitions Object which holds data types produced and
        consumed by operations.

        """
        # Make sure this swagger file has definitions
        try:
            definitions = self.data['definitions']
            logger.debug("Processing Definitions")
        except KeyError:
            logger.debug("No Definitions")
            return

        for definition in self.definitions:
            try:
                value = definitions[definition]
            except KeyError:
                logger.error("Definition %s not found", definition)
                continue
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
        group, version, kind, prefix = parse_schema_name(schema_name)
        # We only handle v1 for now
        if version and version != "v1":
            logger.debug("Ignoring %s version of %s", version, kind)
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
                property_type = self.get_ref(property_schema['$ref'])
                if not property_type in self.data_types:
                    self.create_data_type_from_schema(property_type,
                                                      self.data['definitions'][property_type])
                else:
                    logger.debug("Duplicate %s", property_type)
            except KeyError:
                # Property schema does not contain a $ref. Items
                # perhaps?
                try:
                    items = property_schema['items']
                    property_type = self.get_ref(items['$ref'])
                    if not property_type in self.data_types:
                        self.create_data_type_from_schema(property_type,
                                                          self.data['definitions'][property_type])
                    else:
                        logger.debug("Duplicate %s", property_type)
                except KeyError:
                    try:
                        additionalProperties = property_schema['additionalProperties']
                        property_type = self.get_ref(additionalProperties['$ref'])
                        if not property_type in self.data_types:
                            self.create_data_type_from_schema(property_type,
                                                              self.data['definitions'][property_type])
                        else:
                            logger.debug("Duplicate %s", property_type)
                    except KeyError:
                        # No additional schemas
                        pass
                    pass


    def get_ref(self, ref):
        # Only support local references for now
        try:
            if ref[0] != '#':
                logger.error("%s: not a local reference", ref)
                return
        except Exception as e:
            logger.error("%s: not a ref (%s)", str(ref), str(e))
            return
        # Make sure we reference a definition
        prefix = "#/definitions/"
        if ref.startswith(prefix):
            # Strip prefix
            return ref[len(prefix):]
        else:
            logger.error("%s: not a ref to a definition", ref)
            return ref

        
    def process_parameters(self):
        """Process the Parameters Definitions Object which holds parameters
        that can be used across operations. This property does not
        define global parameters for all operations.

        """
        try:
            parameters = self.data['parameters']
            logger.debug("Processing Parameters")
        except KeyError:
            logger.debug("No Parameters")
            return


    def process_responses(self):
        """Process the Responses Definitions Object which hold responses that
        can be used across operations. This property does not define
        global responses for all operations.

        """
        try:
            responses = self.data['responses']
            logger.debug("Processing Responses")
        except KeyError:
            logger.debug("No Responses")
            return


    def process_securityDefinitions(self):
        """Process the Security Definitions Object which holds Security scheme
        definitions that can be used across the specification.

        """
        try:
            securityDefinitions = self.data['securityDefinitions']
            logger.debug("Processing SecurityDefinitions")
        except KeyError:
            logger.debug("No SecurityDefinitions")
            return


    def process_security(self):
        """Process the Security Requirement Object. This object holds a
        declaration of which security schemes are applied for the API
        as a whole. The list of values describes alternative security
        schemes that can be used (that is, there is a logical OR
        between the security requirements). Individual operations can
        override this definition.

        """
        try:
            security = self.data['security']
            logger.debug("Processing Security")
        except KeyError:
            logger.debug("No Security")
            return


    def process_tags(self):
        """Process the Tag Object which holds a list of tags used by the
        specification with additional metadata. The order of the tags
        can be used to reflect on their order by the parsing
        tools. Not all tags that are used by the Operation Object must
        be declared. The tags that are not declared may be organized
        randomly or based on the tools' logic. Each tag name in the
        list MUST be unique.

        """
        try:
            tags = self.data['tags']
            logger.debug("Processing Tags")
        except KeyError:
            logger.debug("No Tags")
            return


    def process_externalDocs(self):
        """Process the External Documentation Object which defines additional
        external documentation.

        """
        try:
            externalDocs = self.data['externalDocs']
            logger.debug("Processing ExternalDocs")
        except KeyError:
            logger.debug("No ExternalDocs")
            return


def wrap_text(text_string):
    """Split a text string into multiple lines to improve legibility
    """
    # First, check to see if the text was already formatted. We do
    # this by trying to split the text string into mutliple lines
    # based on newlines contained in the string.
    lines = text_string.splitlines()
    if len(lines) > 1:
        # Already formatted
        return lines

    # Not already formatted. Wrap it ourselves.
    return textwrap.wrap(text_string)


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


