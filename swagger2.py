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

# Text formatting
import textwrap

class Swagger2(swagger.Swagger):

    def convert(self, output_file_name):
        """Convert a Swagger file to TOSCA type definitions and write to the
        file specified by 'output_file_name'.

        """
        # Open the file
        self.open(output_file_name)
        
        self.process_info()            
        self.process_host()
        self.process_basePath()
        self.process_schemes()
        self.process_consumes()
        self.process_produces()
        self.process_paths()
        self.process_definitions()
        self.process_parameters()
        self.process_responses()
        self.process_securityDefinitions()
        self.process_security()
        self.process_tags()
        self.process_externalDocs()

        
    def process_info(self):
        """Process the (required) Info Object. This object provides metadata
        about the API. The metadata can be used by the clients if
        needed.
        """
        try:
            info = self.data['info']
        except KeyError:
            logger.error("No Info")
            return

        indent = ""
        self.emit_metadata(indent, info)

    def emit_metadata(self, indent, data):
        self.out.write(
            "%smetadata:\n"
            % indent
        )
        indent = indent + '  '
        self.emit_key_value_data(indent, data)

    def emit_key_value_data(self, indent, data):
        for key, value in data.items():
            if isinstance(value, str):
                self.out.write("%s%s: %s\n" %
                               (indent, key, value))
            else:
                self.out.write("%s%s:\n" %
                               (indent, key))
                self.emit_key_value_data(indent+"  ", value)


    def process_host(self):
        """Process the host (name or ip) serving the API. This MUST be the
        host only and does not include the scheme nor sub-paths. It
        MAY include a port. If the host is not included, the host
        serving the documentation is to be used (including the
        port). The host does not support path templating.
        """
        try:
            host = self.data['host']
        except KeyError:
            logger.info("No Host")
            return

        logger.info("Processing Host")

    def process_basePath(self):
        """Process the base path on which the API is served, which is relative
        to the host. If it is not included, the API is served directly
        under the host. The value MUST start with a leading slash
        (/). The basePath does not support path templating.
        """
        try:
            basePath = self.data['basePath']
        except KeyError:
            logger.info("No BasePath")
            return

        logger.info("Processing BasePath")

    def process_schemes(self):
        """Process the transfer protocol of the API. Values MUST be from the
        list: "http", "https", "ws", "wss". If the schemes is not
        included, the default scheme to be used is the one used to
        access the Swagger definition itself.
        """
        try:
            schemes = self.data['schemes']
        except KeyError:
            logger.info("No Schemes")
            return

        logger.info("Processing Schemes")

    def process_consumes(self):
        """Process the list of MIME types the APIs can consume. This is global
        to all APIs but can be overridden on specific API calls. Value
        MUST be as described under Mime Types.

        """
        try:
            consumes = self.data['consumes']
        except KeyError:
            logger.info("No Consumes")
            return

        logger.info("Processing Consumes")

    def process_produces(self):
        """Process the list of MIME types the APIs can produce. This is global
        to all APIs but can be overridden on specific API calls. Value
        MUST be as described under Mime Types.

        """
        try:
            produces = self.data['produces']
        except KeyError:
            logger.info("No Produces")
            return

        logger.info("Processing Produces")

    def process_paths(self):
        """Process the (required) Paths Object, which defines a list of
        available paths and associated operations for the API.
        """
        # Check if this swagger file has paths
        try:
            paths = self.data['paths']
        except KeyError:
            paths = None
        if not paths:
            logger.error("No Paths Object")
            return

        logger.info("Processing Paths Object")
        indent = ""
        for name, value in paths.items():
            self.process_path_object(indent, name, value)

            
    def process_path_object(self, indent, name, value):
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
            self.process_parameter_object(indent, name, parameter)
            
        self.process_operation_object(indent, name, post)
        
            
    def process_operation_object(self, indent, name, value):
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
            self.process_parameter_object(indent, name, parameter)

        
    def process_parameter_object(self, indent, name, value):
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
        if value['in'] == 'body':
            schema = value['schema']
        else:
            return

        # We have an operation that can create a resource. Create a
        # node type based on the body schema.
        self.process_schema_for_node_type(indent, name, schema)


    def process_schema_for_node_type(self, indent, name, schema):
        
        # Check to see if this schema references another schema (in
        # which case all other properties in this schema object must
        # be ignored according to the JSONSchema spec)
        try:
            ref = schema['$ref']
            schema_ref = self.get_ref(ref)
            try:
                schema = self.data['definitions'][schema_ref]
            except KeyError:
                logger.error("%s not found", schema_ref)
                return
        except KeyError:
            # Not a schema reference
            pass

        # For k8s resources, get the name of the resource from the
        # 'x-kubernetes-group-version-kind' attribute.
        try:
            for group_version_kind in schema['x-kubernetes-group-version-kind']:
                kind = group_version_kind['kind']
                logger.info("%s: %s", name, kind)
        except KeyError:
            logger.info("%s: no version kind", name)
            pass


    def process_definitions(self):
        """Process the Definitions Object which holds data types produced and
        consumed by operations.

        """
        # Make sure this swagger file has definitions
        try:
            definitions = self.data['definitions']
        except KeyError:
            definitions = None
        if not definitions:
            logger.info("No Definitions")
            return

        logger.info("Processing Definitions")
        self.out.write("data_types:\n")
        indent = "  "

        self.tosca = dict()
        for name, value in definitions.items():
            self.process_schema_object(indent, name, value)
            self.out.write("\n")


    def process_schema_object(self, indent, name, value):
        """A Schema Object in Swagger 2 has the following:

        $ref(URI Reference): Resolved against the current URI base, it
          identifies the URI of a schema to use.  All other properties
          in a "$ref" object MUST be ignored.

        title(string): Title of this schema.

        description(string--GFM syntax can be used for rich text
          representation): Provides explanation about the purpose of
          the instance described by this schema.

        default('type'). Supplies a default JSON value associated with
          this schema.  (Unlike with regular JSON Schema, the value
          must conform to the defined type for the Schema Object)

        Validation Keywords for All Types
        ---------------------------------
          type(string): values must be one of the six primitive types
            ("null", "boolean", "object", "array", "number", or
            "string"), or "integer" which matches any number with a
            zero fractional part.

          format(string): Allows schema authors to convey semantic
            information for the values of the given 'type'

          enum(array): An instance validates successfully against this
            keyword if its value is equal to one of the elements in
            this keyword's array value.

        Validation Keywords for Numeric Instances (number and integer)
        --------------------------------------------------------------

          multipleOf(number > 0): A numeric instance is valid only if
            division by this keyword's value results in an integer.

          maximum(number): the instance must be less than or exactly
            equal to "maximum".

          exclusiveMaximum(number): the instance must have a value
            strictly less than (not equal to) "exclusiveMaximum".

          minimum (number): the instance must be greater than or
            exactly equal to "maximum".

          exclusiveMinimum(number): the instance must have a value
            strictly greater than (not equal to) "exclusiveMinimum".

        Validation Keywords for Strings
        -------------------------------

          maxLength(number >= 0): string length must be less than, or
            equal to, the value of this keyword.

          minLength(number >= 0): string length must be greater than,
            or equal to, the value of this keyword.

          pattern(string): the regular expression must match the
            instance successfully.

        Validation Keywords for Arrays
        ------------------------------

          maxItems(number >= 0): the array size must be less than, or
            equal to, the value of this keyword.

          minItems(number >= 0): the array size must be greater than,
            or equal to, the value of this keyword.

          uniqueItems(boolean): If true, the instance validates
            successfully if all of its elements are unique.

        Validation Keywords for Objects
        ------------------------------

          maxProperties(number >= 0): the number of object properties
            is less than, or equal to, the value of this keyword.

          minProperties(number >= 0): the number of object properties
            is greater than, or equal to, the value of this keyword.

          required(string[]): a property value must be defined for
            every property listed in the array

        Keywords for Applying Subschemas In Place
        -----------------------------------------

          allOf(schema[]): An instance validates successfully against
            this keyword if it validates successfully against all
            schemas defined by this keyword's value.

        Keywords for Applying Subschemas to Child Instances
        -------------------------------------------------

          Keywords for Applying Subschemas to Arrays
          ------------------------------------------

            items(schema or schema[]): If "items" is a schema,
              validation succeeds if all elements in the array
              successfully validate against that schema.  If "items"
              is an array of schemas, validation succeeds if each
              element of the instance validates against the schema at
              the same position, if any.

          Keywords for Applying Subschemas to Objects
          -------------------------------------------

            properties(dict of schema): Each value of this object must
              be a valid JSON Schema.

            additionalProperties(schema): schema for child values of
              instance names that do not appear in the annotation
              results of "properties"

        discriminator(string): Adds support for polymorphism. The
          discriminator is the schema property name that is used to
          differentiate between other schema that inherit this
          schema. The property name used MUST be defined at this
          schema and it MUST be in the required property list. When
          used, the value MUST be the name of this schema or any
          schema that inherits it.

        readOnly(boolean): Relevant only for Schema "properties"
          definitions. Declares the property as "read only". This
          means that it MAY be sent as part of a response but MUST NOT
          be sent as part of the request. Properties marked as
          readOnly being true SHOULD NOT be in the required list of
          the defined schema. Default value is false.

        xml(XML Object): This MAY be used only on properties
          schemas. It has no effect on root schemas. Adds Additional
          metadata to describe the XML representation format of this
          property.

        externalDocs(External Documentation Object): Additional
          external documentation for this schema.

        example(any): A free-form property to include an example of an
          instance for this schema
        """

        data = dict()

        self.out.write("%s%s:\n" % (indent, name))
        indent = indent + '  '

        try:
            derived_from = self.get_type(value['type'])
            self.out.write("%sderived_from: %s\n" % (indent, derived_from))
        except KeyError:
            pass
        
        try:
            description = value['description']
            self.emit_description(indent, description)
        except KeyError:
            pass

        try:
            meta = value['x-kubernetes-group-version-kind']
            self.add_meta_data(data, 'x-kubernetes-group-version-kind', meta)
        except KeyError:
            pass
        try:
            meta = value['x-kubernetes-union']
            self.add_meta_data(data, 'x-kubernetes-union', meta)
        except KeyError:
            pass
        try:
            meta = value['format']
            self.add_meta_data(data, 'format', meta)
        except KeyError:
            pass

        try:
            properties = value['properties']
            self.add_properties(data, properties)
            try:
                required = value['required']
                for property_name in required:
                    property = data['properties'][property_name]
                    property['required'] = True
            except KeyError:
                pass
        except KeyError:
            pass

        self.tosca[name] = data

    def add_meta_data(self, data, key, meta):
        try:
            metadata = data['metadata']
        except KeyError:
            data['metadata'] = dict()
            metadata = data['metadata']
        metadata[key] = meta

    def add_properties(self, data, properties):
        data['properties'] = dict()
        for property_name, property_value in properties.items():
            self.add_property(data['properties'], property_name, property_value)
            
    def add_property(self, properties, property_name, value):
        data = dict()
        properties[property_name] = data
        try:
            data['type'] = self.get_type(value['type'])
        except KeyError:
            pass
        try:
            data['entry_schema'] = self.get_entry_schema(value['items'])
        except KeyError:
            pass
        try:
            data['type'] = self.get_ref(value['$ref'])
        except KeyError:
            pass
        try:
            data['description'] = value['description']
        except KeyError:
            pass
        # Everything else is metadata
        for field in ['x-kubernetes-list-map-keys', 'format', 'x-kubernetes-list-type', 'x-kubernetes-patch-strategy', 'x-kubernetes-patch-merge-key']:
            try:
                meta = value[field]
                self.add_meta_data(data, field, meta)
            except KeyError:
                pass


    def get_type(self, type):
        if type == 'array':
            return 'list'
        elif type == 'object':
            return 'tosca.datatypes.Root'
        elif type == 'number':
            return 'float'
        else:
            return type


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
            logger.info("%s: not a ref to a definition", ref)
            return ref

        
    def get_entry_schema(self, value):
        try:
            return self.get_type(value['type'])
        except KeyError:
            pass
        try:
            return self.get_ref(value['$ref'])
        except KeyError:
            pass
        logger.info("%s: no entry schema found", str(value))
        return "not found"


    def process_parameters(self):
        """Process the Parameters Definitions Object which holds parameters
        that can be used across operations. This property does not
        define global parameters for all operations.

        """
        try:
            parameters = self.data['parameters']
        except KeyError:
            logger.info("No Parameters")
            return

        logger.info("Processing Parameters")

    def process_responses(self):
        """Process the Responses Definitions Object which hold responses that
        can be used across operations. This property does not define
        global responses for all operations.

        """
        try:
            responses = self.data['responses']
        except KeyError:
            logger.info("No Responses")
            return

        logger.info("Processing Responses")

    def process_securityDefinitions(self):
        """Process the Security Definitions Object which holds Security scheme
        definitions that can be used across the specification.

        """
        try:
            securityDefinitions = self.data['securityDefinitions']
        except KeyError:
            logger.info("No SecurityDefinitions")
            return

        logger.info("Processing SecurityDefinitions")

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
        except KeyError:
            logger.info("No Security")
            return

        logger.info("Processing Security")

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
        except KeyError:
            tags = None
        if not tags:
            logger.info("No Tags")
            return

        logger.info("Processing Tags")

    def process_externalDocs(self):
        """Process the External Documentation Object which defines additional
        external documentation.

        """
        try:
            externalDocs = self.data['externalDocs']
        except KeyError:
            logger.info("No ExternalDocs")
            return

        logger.info("Processing ExternalDocs")

    def emit_description(self, indent, description):

        # Emit description key
        self.out.write(
            "%sdescription: "
            % (indent)
        )
        # Emit text. Split into multiple lines if necessary
        lines = wrap_text(description)
        self.emit_text_string(indent, lines)


    def emit_text_string(self, indent, lines):
        """Write a text value. We use YAML folded style if the text consists
        of multiple lines or if it includes a colon character (or some
        other character that would violate YAML syntax)
        """
        if len(lines) > 1 or (':' in lines[0]) or ('\'' in lines[0]):
            # Emit folding character
            self.out.write(">-\n")
            # Emit individual lines. Make sure the first line is indented
            # correctly.
            first = True
            for line in lines:
                if first:
                    self.out.write(
                        "%s%s\n"
                        % (indent + '  ', line.lstrip())
                    )
                    first = False
                else:
                    self.out.write(
                        "%s%s\n"
                        % (indent + '  ', line.lstrip())
                    )
        else:
            self.out.write("%s\n"
                     % lines[0]
            )


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


