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
import oas2tosca.swagger

# Text formatting
import textwrap


class Swagger2(oas2tosca.swagger.Swagger):
    """A Swagger 2 object has the following properties:

      swagger(string): Required. Specifies the Swagger Specification
        version being used. It can be used by the Swagger UI and other
        clients to interpret the API listing. The value MUST be "2.0".
      info(Info Object): Required. Provides metadata about the
        API. The metadata can be used by the clients if needed.
      host(string): The host (name or ip) serving the API. This MUST
        be the host only and does not include the scheme nor
        sub-paths. It MAY include a port. If the host is not included,
        the host serving the documentation is to be used (including
        the port). The host does not support path templating.
      basePath(string): The base path on which the API is served,
        which is relative to the host. If it is not included, the API
        is served directly under the host. The value MUST start with a
        leading slash (/). The basePath does not support path
        templating.
      schemes([string]): The transfer protocol of the API. Values MUST
        be from the list: "http", "https", "ws", "wss". If the schemes
        is not included, the default scheme to be used is the one used
        to access the Swagger definition itself.
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
        scheme definitions that can be used across the specification.
      security([Security Requirement Object]): A declaration of which
        security schemes are applied for the API as a whole. The list
        of values describes alternative security schemes that can be
        used (that is, there is a logical OR between the security
        requirements). Individual operations can override this
        definition.
      tags([Tag Object]): A list of tags used by the specification
        with additional metadata. The order of the tags can be used to
        reflect on their order by the parsing tools. Not all tags that
        are used by the Operation Object must be declared. The tags
        that are not declared may be organized randomly or based on
        the tools' logic. Each tag name in the list MUST be unique.
      externalDocs(External Documentation Object): Additional external
        documentation.
    """

    def get_schemas(self):
        try:
            return self.data['definitions']
        except KeyError:
            return dict()


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
        self.create_node_type_from_schema_reference(name, schema)
