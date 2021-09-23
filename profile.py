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


    def initialize(self, top):
        """Initialize a skeleton structure for this profile
        """
        
        # Create a path to the directory for this profile
        path = self.name.split('.')
        self.profile_dir = os.path.join(top, *path)
        try:
            logger.info("%s: create directory %s", self.name, self.profile_dir)
            os.makedirs(self.profile_dir, exist_ok=True)
        except Exception as e:
            logger.error("%s: %s", self.profile_dir, str(e))
            return

        # Open a profile.yaml file
        self.profile_yaml = os.path.join(self.profile_dir, 'profile.yaml')
        fd = open(self.profile_yaml, "w")
            
