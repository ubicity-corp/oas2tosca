#
# Module for reading swagger JSON
#
__author__ = "Chris Lauwers"
__copyright__ = "Copyright (c) 2020, Ubicity Corp."
__version__ = "0.0.1"
__email__ = "lauwers@ubicity.com"
__status__ = "Prototype"

# Logging support
import logging
logger = logging.getLogger(__name__)

# YAML support. We'll use a YAML reader to read JSON
from ruamel.yaml import YAML
from ruamel.yaml.reader import ReaderError
from ruamel.yaml.error import MarkedYAMLError
from ruamel.yaml.constructor import DuplicateKeyError

# System support
import sys

class Swagger(object):

    def __init__(self):
        """Constructor """

        # First, call superclass constructor
        super(Swagger, self).__init__()


    def read(self, swagger_file_name):
        """Parse file content as YAML 

        Returns:
          dict containing parsed YAML data
        """

        # Open file
        self.file_name = swagger_file_name
        try:
            swagger_file = open(self.file_name)
        except IOError as e:
            return  {
                'type': 'IO Error',
                'message' : str(e)
            }

        # Read data from the template file
        try:
            swagger_file_data = swagger_file.read()
        except UnicodeDecodeError as e:
            return {
                'file error': str(e)
                }

        # Return parsed file content as YAML. We use the RoundTripLoader
        # (the default) since it stores line numbers in the comments
        # section.
        yaml_errors = {}
        yaml = YAML()
        try:
            self.data = yaml.load(swagger_file_data)

        except ReaderError as e:
            logger.error("%s", e)
            self.data = None
            error = {}
            error['message'] = str(e)
            if e.name:      error['name'] = e.name
            if e.character: error['character'] = e.character.decode(e.encoding, errors='ignore')
            if e.position:  error['position'] = e.position
            if e.encoding:  error['encoding'] = e.encoding
            if e.reason:    error['reason'] = e.reason
            yaml_errors['invalid YAML'] = error

        except MarkedYAMLError as e:
            logger.error("%s", e)
            self.data = None
            yaml_errors['invalid YAML'] = serialize_marked_yaml_error(e)

        except DuplicateKeyError as e:
            # logger.error("%s", e)
            self.data = None
            yaml_errors['duplicate key'] = serialize_marked_yaml_error(e)

        return yaml_errors


    def serialize_marked_yaml_error(e):
        """ Serialize a MarkedYAMLError exception"""

        error = collections.OrderedDict()

        # Top-level attributes
        error['message'] = str(e)
        if e.problem: error['problem'] = e.problem
        if e.context: error['context'] = e.context
    #    if e.note: error['note'] = e.note
    #    if e.warn: error['warn'] = e.warn

        # Problem mark
        if e.problem_mark:
            problem_mark = collections.OrderedDict()
            if e.problem_mark.name:     problem_mark['name'] = e.problem_mark.name
            if e.problem_mark.line:     problem_mark['line'] = e.problem_mark.line
            if e.problem_mark.column:   problem_mark['column'] = e.problem_mark.column
    #        if e.problem_mark.index:    problem_mark['index'] = e.problem_mark.index
    #        if e.problem_mark.pointer:  problem_mark['pointer'] = e.problem_mark.pointer
            if problem_mark:            error['problem_mark'] = problem_mark

        # Context mark
        if e.context_mark:
            context_mark = collections.OrderedDict()
            if e.context_mark.name:     context_mark['name'] = e.context_mark.name
            if e.context_mark.line:     context_mark['line'] = e.context_mark.line
            if e.context_mark.column:   context_mark['column'] = e.context_mark.column
    #        if e.context_mark.index:    context_mark['index'] = e.context_mark.index
    #        if e.context_mark.pointer:  context_mark['pointer'] = e.context_mark.pointer
            if context_mark:            error['context_mark'] = context_mark

        return error


    def convert(self):
        # Convert definitions to TOSCA
        self.tosca = dict()
        self.unhandled = set()
        
        definitions = self.data['definitions']
        for name, value in definitions.items():
            self.convert_definition(name, value)


    def convert_definition(self, name, value):
        data = dict()
        try:
            data['derived_from'] = self.get_type(value['type'])
        except KeyError:
            pass
        try:
            data['description'] = value['description']
        except KeyError:
            pass
        try:
            data['description'] = value['description']
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

        for key in value.keys():
            if not key in ['type', 'description', '$ref', 'items', 'x-kubernetes-list-map-keys', 'format', 'x-kubernetes-list-type', 'x-kubernetes-patch-strategy', 'x-kubernetes-patch-merge-key']: 
                self.unhandled.add(key)


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


    def write(self, output_file_name):
        tosca = dict()
        tosca['tosca_definitions_version'] = 'tosca_simple_yaml_1_3'
        tosca['data_types'] = self.tosca
        
        # Open file if file name given
        if output_file_name:
            try:
                out = open(output_file_name, "w+")
            except IOError as e:
                logger.error("Unable to open file '%s", output_file_name)
                return
        else:
            out = sys.stdout
            
        # Dump YAML
        yaml = YAML()
        try:
            yaml.dump(tosca, out)
        except Exception as e:
            logger.error("Unable to write: '%s", str(e))
            return

        logger.info("Unhandled: %s", str(self.unhandled))
            
