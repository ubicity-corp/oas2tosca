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


class Swagger(object):

    def __init__(self, swagger_file_name):
        """Constructor """

        # First, call superclass constructor
        super(Swagger, self).__init__()

        self.file_name = swagger_file_name
        
        
    def read(self):
        """Parse file content as YAML 

        Returns:
          dict containing parsed YAML data
        """

        # Open file
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


    def convert(self, output_file_name):
        # Convert definitions to TOSCA
        definitions = self.data['definitions']
        for name, value in definitions.items():
            logger.info("%s", name)
