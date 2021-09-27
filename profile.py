#
# Module for tracking TOSCA Profiles generated from k8s swagger file
#
__author__ = "Chris Lauwers"
__copyright__ = "Copyright (c) 2021, Ubicity Corp."
__version__ = "0.0.1"
__email__ = "lauwers@ubicity.com"
__status__ = "Prototype"

# Logging support
import logging
logger = logging.getLogger(__name__)

# Directory support
import os
import os.path

# Text formatting
import textwrap

class Profile(object):

    def __init__(self, name, version, prefix):
        """Constructor """

        # First, call superclass constructor
        super(Profile, self).__init__()

        # Initialize
        self.name = name
        self.version = version
        self.prefix = prefix
        self.dependencies = dict()
        self.already_has_node_types = False
        self.already_has_data_types = False
        

    def add_dependency(self, dependency_profile, dependency_prefix):
        """Add a profile on which this profile depends, and the namespace
        prefix to use when importing that profile. This method can be
        called multiple times, but we check for conflicting
        prefixes
        """
        try:
            if dependency_prefix != self.dependencies[dependency_profile]:
                logger.error("%s: prefix %s conflicts with previously configured %s",
                             dependency_profile, dependency_prefix,
                             self.dependencies[dependency_profile])
        except KeyError:
            self.dependencies[dependency_profile] = dependency_prefix


    def initialize(self, top, swagger_info):
        """Initialize a skeleton structure for this profile
        """

        # Create profile directory if it doesn't exist.
        self.create_profile_directory(top)

        # Create TOSCA.meta file
        self.create_tosca_meta()

        # Prepare 'profile.yaml' file
        self.prepare_yaml_file(swagger_info)


    def finalize(self):
        self.out.close()


    def create_profile_directory(self, top):
        # Create a path to the directory for this profile
        path = self.name.split('.')
        self.directory = os.path.join(top, *path)
        try:
            logger.debug("%s: create directory %s", self.name, self.directory)
            os.makedirs(self.directory, exist_ok=True)
        except Exception as e:
            logger.error("%s: %s", self.directory, str(e))
            return


    def create_tosca_meta(self):
        # Open a TOSCA meta file
        tosca_meta = os.path.join(self.directory, 'TOSCA.meta')
        out = open(tosca_meta, "w")
        out.write("TOSCA-Meta-File-Version: 1.0\n")
        out.write("CSAR-Version: 1.1\n")
        out.write("Created-By: swagger2tosca\n")
        out.write("Entry-Definitions: profile.yaml\n")
        out.close()


    def prepare_yaml_file(self, swagger_info):
        """Create a 'profile.yaml' file in this profile's directory and
        initialize it."""
        
        # Open a profile.yaml file
        self.yaml_file = os.path.join(self.directory, 'profile.yaml')
        self.out = open(self.yaml_file, "w")

        # Emit tosca header
        self.out.write("tosca_definitions_version: tosca_simple_yaml_1_3\n\n")

        # Add comment
        self.out.write(
            "# This template was auto-generated by swagger2tosca\n\n"
        )
    
        # Write profile name
        self.out.write("namespace: %s\n\n" % self.name)

        # Write out swagger swagger_info
        self.emit_swagger_info(swagger_info)

        # Write out 'imports'
        self.emit_imports()
        

    def emit_swagger_info(self, swagger_info):
        """Write out information from the (required) Swagger Info Object. This
        object provides metadata about the API. The metadata can be
        used by the clients if needed. A swagger 2 Info Object has the
        following properties:

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
        indent = ""
        self.emit_metadata(indent, swagger_info)
        self.out.write("\n")
        

    def emit_imports(self):
        """Write out import statements for all of the other profiles on which
        this profile depends
        """
        if not self.dependencies:
            return
        
        self.out.write("imports:\n")
        for name, prefix in self.dependencies.items():
            self.out.write("  - file: %s\n" % name)
            self.out.write("    namespace_prefix: %s\n" % prefix)
        self.out.write("\n")


    def emit_metadata(self, indent, data):
        self.out.write(
            "%smetadata:\n"
            % indent
        )
        indent = indent + '  '
        self.emit_key_value_data(indent, data)


    def emit_node_type(self, kind, schema):
        """Emit a node type definition for a JSON Schema object. A JSON Schema
        Object in Swagger has the following:

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

        type(string): values must be one of the six primitive types
          ("null", "boolean", "object", "array", "number", or
          "string"), or "integer" which matches any number with a zero
          fractional part.

        In addition, there are a number of type-specific keywords that
        will be handled separately for each type.
        """

        # Do we have to write the header first?
        if not self.already_has_node_types:
            self.out.write("node_types:\n\n")
            self.already_has_node_types = True
            
        # Write 'name' and 'description'
        indent = '  '
        self.out.write("%s%s:\n" % (indent, kind))
        indent = indent + '  '
        try:
            description = schema['description']
            self.emit_description(indent, description)
        except KeyError:
            pass

        # Node type definitions do not support 'default'
        try:
            default = schema['default']
            logger.error("%s: 'default' not supported", kind)
        except KeyError:
            pass
        # Node type definitions do not support 'enum'
        try:
            enum = schema['enum']
            logger.error("%s: 'enum' not supported", kind)
        except KeyError:
            pass
        
        # For now, we always derive node types from Root
        self.out.write("%sderived_from: tosca.nodes.Root\n" % indent)

        # Process remaining keywords
        self.process_keywords_for_object(indent, kind, schema)


    def emit_data_type(self, kind, schema):
        """Emit a data type definitions for a JSON Schema object.  A JSON
        Schema Object in Swagger has the following:

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

        type(string): values must be one of the six primitive types
          ("null", "boolean", "object", "array", "number", or
          "string"), or "integer" which matches any number with a zero
          fractional part.

        In addition, there are a number of type-specific keywords that
        will be handled separately for each type.
        """

        # Do we have to write the header first?
        if not self.already_has_data_types:
            self.out.write("data_types:\n\n")
            self.already_has_data_types = True
            
        # Write 'name' and 'description'
        indent = '  '
        self.out.write("%s%s:\n" % (indent, kind))
        indent = indent + '  '
        try:
            description = schema['description']
            self.emit_description(indent, description)
        except KeyError:
            pass

        # Data type definitions do not support 'default'.
        try:
            default = schema['default']
            logger.error("%s: 'default' not supported", kind)
        except KeyError:
            pass

        # Remaining definitions depend on the schema type
        try:
            schema_type = schema['type']
            if schema_type == 'object':
                # Don't need 'derived_from'.
                self.process_keywords_for_object(indent, kind, schema)
            elif schema_type == "string":
                # This type is derived from string
                self.out.write("%sderived_from: string\n" % indent )
                self.process_keywords_for_string(indent, kind, schema)
            elif schema_type == "array":
                # This type is derived from list
                self.out.write("%sderived_from: list\n" % indent )
                self.process_keywords_for_array(indent, kind, schema)
            elif schema_type == "integer":
                # This type is derived from integer
                self.out.write("%sderived_from: integer\n" % indent )
                self.process_keywords_for_integer(indent, kind, schema)
            elif schema_type == "number":
                # This type is derived from float
                self.out.write("%sderived_from: float\n" % indent )
                self.process_keywords_for_number(indent, kind, schema)
            elif schema_type == "boolean":
                # This type is derived from boolean
                self.out.write("%sderived_from: boolean\n" % indent )
                self.process_keywords_for_boolean(indent, kind, schema)
            elif schema_type == "null":
                # This type is derived from null
                self.out.write("%sderived_from: null\n" % indent )
                self.process_keywords_for_null(indent, kind, schema)
            else:
                logger.error("%s: unknown type '%s'", kind, schema_type)
                return
        except KeyError:
            # No 'type', which means that this data type can have any
            # type. Given the lack of 'any' in TOSCA, we'll just use
            # 'string'
            self.out.write("%sderived_from: string\n" % indent )
            self.process_keywords_for_any(indent, kind, schema)


    def process_keywords_for_string(self, indent, name, schema):
        """Process JSON Schema keywords for strings. 

        The following validation Keywords apply to all types:
        ----------------------------------------------------
          format(string): Allows schema authors to convey semantic
            information for the values of the given 'type'. However,
            swagger does not support 'format' for strings.

          enum(array): An instance validates successfully against this
            keyword if its value is equal to one of the elements in
            this keyword's array value.

        Validation Keywords for Strings
        -------------------------------

          maxLength(number >= 0): string length must be less than, or
            equal to, the value of this keyword.

          minLength(number >= 0): string length must be greater than,
            or equal to, the value of this keyword.

          pattern(string): the regular expression must match the
            instance successfully.

        """
        # Swagger does not support 'format' in strings
        try:
            fmt = schema['format']
            logger.error("%s: format '%s' not supported for strings", name, fmt)
        except KeyError:
            pass

        # Turn remaining keywords into constraints
        try:
            enum = schema['enum']
        except KeyError:
            enum = None
        try:
            maxLength = schema['maxLength']
        except KeyError:
            maxLength = None
        try:
            minLength = schema['minLength']
        except KeyError:
            minLength = None
        try:
            pattern = schema['pattern']
        except KeyError:
            pattern = None
        if enum or maxLength or minLength or pattern:
            self.out.write("%sconstraints:\n" % (indent))
            indent = indent + '  '
            if enum: self.emit_valid_values(indent, enum)
            if maxLength: self.emit_max_length(indent, maxLength)
            if minLength: self.emit_min_length(indent, minLength)
            if enum: self.emit_pattern_values(indent, pattern)


    def process_keywords_for_array(self, indent, name, schema):
        # Write entry schema
        try:
            entry_schema = self.get_entry_schema(schema['items'])
            group, version, kind, prefix = parse_schema_name(entry_schema)
            if prefix and prefix != self.prefix:
                type_name = prefix + ':' + kind
            else:
                type_name = kind
            self.out.write(
                "%sentry_schema: %s\n"
                % (indent, type_name)
            )
        except KeyError:
            pass

        # Write list metadata
        meta = dict()
        for field in ['x-kubernetes-list-map-keys', 'x-kubernetes-list-type' ]:
            try:
                meta[field] = schema[field]
            except KeyError:
                pass
        if meta: self.emit_metadata(indent, meta)
        logger.info("%s: array not fully implemented", name)


    def process_keywords_for_number(self, indent, name, schema):
        """Create a TOSCA data type from a JSON Schema number"""
        logger.info("%s: number not implemented", name)


    def process_keywords_for_integer(self, indent, name, schema):
        """Create a TOSCA data type from a JSON Schema integer"""
        logger.info("%s: integer not implemented", name)


    def process_keywords_for_boolean(self, indent, name, schema):
        """Create a TOSCA data type from a JSON Schema boolean"""
        logger.info("%s: boolean not implemented", name)


    def process_keywords_for_null(self, indent, name, schema):
        """Create a TOSCA data type from a JSON Schema null"""
        logger.info("%s: null not implemented", name)


    def process_keywords_for_any(self, indent, name, schema):
        """Create a TOSCA data type from a JSON Schema any type"""
        logger.info("%s: any not implemented", name)


    def process_keywords_for_object(self, indent, name, schema):
        """A JSON Schema Object in Swagger has the following:

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

        # Emit 'x-kubernetes-group-kind' as metadata
        metadata = dict()
        try:
            # x-kubernetes-group-version-kind is a list for some reason
            metadata['x-kubernetes-group-version-kind'] = schema['x-kubernetes-group-version-kind'][0]
            self.emit_metadata(indent, metadata)
        except KeyError:
            pass

        # Add property definitions. Pass the list of required
        # properties.
        try:
            properties = schema['properties']
            try:
                required = schema['required']
            except KeyError:
                required = set()
            self.add_properties(indent, properties, required)
        except KeyError:
            # No properties
            pass

        self.out.write("\n")


    def add_properties(self, indent, properties, required):
        """Write out the property definitions for this type"""
        
        self.out.write(
            "%sproperties:\n"
            % indent
        )
        indent = indent + '  '
        for property_name, property_schema in properties.items():
            self.add_property(indent, property_name, property_schema, required)
            

    def add_property(self, indent, property_name, schema, required):
        """Add a property definition based on the provided JSON schema. A
        JSON Schema Object in Swagger has the following:

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

        """

        # Write out property name and description
        self.out.write("%s%s:\n" % (indent, property_name))
        indent = indent + '  '
        try:
            description = schema['description']
            self.emit_description(indent, description)
        except KeyError:
            pass

        # Is property required?
        if property_name in required:
            self.out.write("%srequired: true\n" % (indent))
        else:
            self.out.write("%srequired: false\n" % (indent))
            
        # Write default value
        try:
            default = schema['default']
            self.out.write("%sdefault: %s\n" % (indent, default))
        except KeyError:
            pass

        # Remaining property definitions depend on the property type
        try:
            property_type = schema['type']
            if property_type == 'object':
                # Not sure yet what to do here. For now, use
                # 'tosca.datatypes.Root' as a "generic" type.
                self.out.write("%stype: tosca.datatypes.Root\n" % indent )
                logger.info("UNEXPECTED property '%s' of type 'object' with schema %s",
                            property_name, str(schema))
            elif property_type == "string":
                # This property is of type string
                self.out.write("%stype: string\n" % indent )
                self.process_keywords_for_string(indent, property_name, schema)
            elif property_type == "array":
                # This property is of type list
                self.out.write("%stype: list\n" % indent )
                self.process_keywords_for_array(indent, property_name, schema)
            elif property_type == "integer":
                # This property is of type integer
                self.out.write("%stype: integer\n" % indent )
                self.process_keywords_for_integer(indent, property_name, schema)
            elif property_type == "number":
                # This property is of type float
                self.out.write("%stype: float\n" % indent )
                self.process_keywords_for_number(indent, property_name, schema)
            elif property_type == "boolean":
                # This property is of type boolean
                self.out.write("%stype: boolean\n" % indent )
                self.process_keywords_for_boolean(indent, property_name, schema)
            elif property_type == "null":
                # This property is of type null
                self.out.write("%stype: null\n" % indent )
                self.process_keywords_for_null(indent, property_name, schema)
            else:
                logger.error("%s: unknown type '%s'", property_name, property_type)
                return
        except KeyError:
            # No type specified. Do we have a 'ref'?
            try:
                schema_name = self.get_ref(schema['$ref'])
                # Parse the schema name to get 'prefix' and 'kind' so
                # we can create a type name.
                group, version, kind, prefix = parse_schema_name(schema_name)
                if prefix and prefix != self.prefix:
                    type_name = prefix + ':' + kind
                else:
                    type_name = kind
                self.out.write("%stype: %s\n" % (indent, type_name))
                # All other keywords must be ignored
            except KeyError:
                # Not a ref either.  This property can be of any
                # type. Given the lack of 'any' in TOSCA, we'll just
                # use 'string'
                self.out.write("%stype: string\n" % indent )
                self.process_keywords_for_any(indent, property_name, schema)


    def get_entry_schema(self, value):
        try:
            return self.get_type(value['type'])
        except KeyError:
            pass
        try:
            return self.get_ref(value['$ref'])
        except KeyError:
            pass
        logger.error("%s: no entry schema found", str(value))
        return "not found"


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
        if len(lines) > 1 or (':' in lines[0]) or ('\'' in lines[0]) or ('\'' in lines[0]) or ('`' in lines[0]):
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


    def emit_key_value_data(self, indent, data):
        for key, value in data.items():
            if isinstance(value, (str, list)):
                self.out.write("%s%s: %s\n" %
                               (indent, key, value))
            else:
                self.out.write("%s%s:\n" %
                               (indent, key))
                self.emit_key_value_data(indent+"  ", value)


    def emit_valid_values(self, indent, enum):
        self.out.write("%s- valid_values:\n" % indent)
        indent = indent + '  '
        for value in enum:
            self.out.write("%s- %s" % (indent, value))


    def emit_max_length(self, indent, maxLength):
        self.out.write("%s- max_length: %s\n" % (indent, maxLength))

    def emit_min_length(indent, minLength):
        self.out.write("%s- min_length: %s\n" % (indent, minLength))

    def emit_pattern_values(self, indent, pattern):
        self.out.write("%s- pattern: '%s'\n" % (indent, pattern))

    def get_type(self, type):
        if type == 'array':
            return 'list'
        elif type == 'object':
            return 'tosca.datatypes.Root'
        elif type == 'number':
            return 'float'
        else:
            return type


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


