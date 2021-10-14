#
# Module for converting OpenAPI v3 files to TOSCA
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
import oas2tosca.profile as p

# System support
import oas2tosca.swagger

class Swagger3(oas2tosca.swagger.Swagger):
    """An OpenAPI v3 file has the following properties:

      openapi(string): REQUIRED. This string MUST be the semantic
        version number of the OpenAPI Specification version that the
        OpenAPI document uses. The openapi field SHOULD be used by
        tooling specifications and clients to interpret the OpenAPI
        document. This is not related to the API info version string.

      info (Info Object): REQUIRED. Provides metadata about the
        API. The metadata MAY be used by tooling as required.

      servers([Server Object)]: An array of Server Objects, which
        provide connectivity information to a target server. If the
        servers property is not provided, or is an empty array, the
        default value would be a Server Object with a url value of /.

      paths (Paths Object): REQUIRED. The available paths and
        operations for the API.

      components (Components Object): An element to hold various
        schemas for the specification.

      security ([Security Requirement Object)]: A declaration of which
        security mechanisms can be used across the API. The list of
        values includes alternative security requirement objects that
        can be used. Only one of the security requirement objects need
        to be satisfied to authorize a request. Individual operations
        can override this definition. To make security optional, an
        empty security requirement ({}) can be included in the array.

      tags ([Tag Object)]: A list of tags used by the specification
        with additional metadata. The order of the tags can be used to
        reflect on their order by the parsing tools. Not all tags that
        are used by the Operation Object must be declared. The tags
        that are not declared MAY be organized randomly or based on
        the tools' logic. Each tag name in the list MUST be unique.

      externalDocs (External Documentation Object): Additional
        external documentation.

    """

    def get_schemas(self):
        """Get schemas for data type definitions
        """
        # Make sure this swagger file has defines schemas
        try:
            return self.data['components']['schemas']
        except KeyError:
            return dict()


    def process_parameter_object(self, name, value):
        """A Parameter Object in Swagger has the following fixed fields:

        name (string): REQUIRED. The name of the parameter. Parameter
          names are case sensitive.
          - If in is "path", the name field MUST correspond to a
            template expression occurring within the path field in the
            Paths Object. See Path Templating for further information.
          - If in is "header" and the name field is "Accept",
            "Content-Type" or "Authorization", the parameter
            definition SHALL be ignored.
          - For all other cases, the name corresponds to the parameter
            name used by the in property.

        in (string): REQUIRED. The location of the
          parameter. Possible values are "query", "header", "path" or
          "cookie".

        description (string): A brief description of the
          parameter. This could contain examples of use. CommonMark
          syntax MAY be used for rich text representation.

        required (boolean): Determines whether this parameter is
          mandatory. If the parameter location is "path", this
          property is REQUIRED and its value MUST be true. Otherwise,
          the property MAY be included and its default value is false.

        deprecated (boolean): Specifies that a parameter is deprecated
          and SHOULD be transitioned out of usage. Default value is
          false.

        allowEmptyValue(boolean): Sets the ability to pass
          empty-valued parameters. This is valid only for query
          parameters and allows sending a parameter with an empty
          value. Default value is false. If style is used, and if
          behavior is n/a (cannot be serialized), the value of
          allowEmptyValue SHALL be ignored. Use of this property is
          NOT RECOMMENDED, as it is likely to be removed in a later
          revision.

        The rules for serialization of the parameter are specified in
        one of two ways. 

        1. For simpler scenarios, a schema and style keywords can describe the
           structure and syntax of the parameter.

        2. For more complex scenarios, the content property can define
           the media type and schema of the parameter. 

        A parameter MUST contain either a schema property, or a
        content property, but not both.
        """

        # For now, we don't create TOSCA type definitions based on
        # parameters
        pass


    def process_operation_object(self, name, value):
        """An Operation Object in Swagger 3 has the following:

        tags ([string]): A list of tags for API documentation
          control. Tags can be used for logical grouping of operations
          by resources or any other qualifier.

        summary(string): A short summary of what the operation does.

        description (string): A verbose explanation of the operation
          behavior. CommonMark syntax MAY be used for rich text
          representation.

        externalDocs (External Documentation Object): Additional
          external documentation for this operation.

        operationId (string): Unique string used to identify the
          operation. The id MUST be unique among all operations
          described in the API. The operationId value is
          case-sensitive. Tools and libraries MAY use the operationId
          to uniquely identify an operation, therefore, it is
          RECOMMENDED to follow common programming naming conventions.

        parameters ([Parameter Object | Reference Object]): A list of
          parameters that are applicable for this operation. If a
          parameter is already defined at the Path Item, the new
          definition will override it but can never remove it. The
          list MUST NOT include duplicated parameters. A unique
          parameter is defined by a combination of a name and
          location. The list can use the Reference Object to link to
          parameters that are defined at the OpenAPI Object's
          components/parameters.

        requestBody (Request Body Object | Reference Object): The
          request body applicable for this operation. The requestBody
          is only supported in HTTP methods where the HTTP 1.1
          specification RFC7231 has explicitly defined semantics for
          request bodies. In other cases where the HTTP spec is vague,
          requestBody SHALL be ignored by consumers.

        responses (Responses Object): REQUIRED. The list of possible
          responses as they are returned from executing this
          operation.

        callbacks (Map[string, Callback Object | Reference Object]): A
          map of possible out-of band callbacks related to the parent
          operation. The key is a unique identifier for the Callback
          Object. Each value in the map is a Callback Object that
          describes a request that may be initiated by the API
          provider and the expected responses.

        deprecated (boolean): Declares this operation to be
          deprecated. Consumers SHOULD refrain from usage of the
          declared operation. Default value is false.

        security ([Security Requirement Object]): A declaration of
          which security mechanisms can be used for this
          operation. The list of values includes alternative security
          requirement objects that can be used. Only one of the
          security requirement objects need to be satisfied to
          authorize a request. To make security optional, an empty
          security requirement ({}) can be included in the array. This
          definition overrides any declared top-level security. To
          remove a top-level security declaration, an empty array can
          be used.

        servers([Server Object]): An alternative server array to
          service this operation. If an alternative server object is
          specified at the Path Item Object or Root level, it will be
          overridden by this value.
        """
        # We create node types based on the request body in this POST
        # operation
        try:
            body = value['requestBody']
        except KeyError:
            logger.info("%s: no request body", name)
            return

        self.process_request_body(name, body)

        
    def process_request_body(self, name, body):
        """An Request Body Object in Swagger 3 has the following:

        description (string ): A brief description of the request
          body. This could contain examples of use. CommonMark syntax
          MAY be used for rich text representation.

        content(Map[string, Media Type Object] ): REQUIRED. The
          content of the request body. The key is a media type or
          media type range and the value describes it. For requests
          that match multiple keys, only the most specific key is
          applicable. e.g. text/plain overrides text/*

        required (boolean): Determines if the request body is required
          in the request. Defaults to false.

        """
        logger.info("Processing %s", name)
        content = body['content']

        try:
            # We only support JSON content
            json_content = content['application/json']
            self.process_media_type_object(name, json_content)
        except KeyError:
            logger.info("%s: no JSON content", name)
            pass
        

    def process_media_type_object(self, name, media_type):
        """A Media Type Object in Swagger 3 has the following:

        schema (Schema Object | Reference Object ): The schema
          defining the content of the request, response, or parameter.
        example(Any ): Example of the media type. The example object
          SHOULD be in the correct format as specified by the media
          type. The example field is mutually exclusive of the
          examples field. Furthermore, if referencing a schema which
          contains an example, the example value SHALL override the
          example provided by the schema.
        examples (Map[ string, Example Object | Reference Object]):
          Examples of the media type. Each example object SHOULD match
          the media type and specified schema if present. The examples
          field is mutually exclusive of the example
          field. Furthermore, if referencing a schema which contains
          an example, the examples value SHALL override the example
          provided by the schema.
        encoding (Map[string, Encoding Object] ): A map between a
          property name and its encoding information. The key, being
          the property name, MUST exist in the schema as a
          property. The encoding object SHALL only apply to
          requestBody objects when the media type is multipart or
          application/x-www-form-urlencoded.
        """
        # Create a node type based on the media type object. For now,
        # we only handle media type objects with schemas that
        # reference another schema (in which case all other properties
        # in this schema object must be ignored according to the
        # JSONSchema spec)
        schema = media_type['schema']
        self.create_node_type_from_schema_reference(name, schema)
