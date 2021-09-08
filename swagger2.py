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

class Swagger2(swagger.Swagger):

    def convert(self):
        """ The k8s swagger file has the following sections:
          - definitions
          - info
          - paths
          - security
          - securityDefinitions
          - swagger
        """
        
        # Print which keys we have
        for key in self.data.keys():
            print(key)
            
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


