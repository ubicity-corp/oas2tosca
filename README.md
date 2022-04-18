Convert OpenAPI Specifications to TOSCA Profiles
===

``oas2tosca`` converts OpenAPI Specification files to one or more
TOSCA Profiles. It supports OpenAPI v2 as well as OpenAPI v3, and
generates TOSCA Simple Profile in YAML v1.3 profiles.

## Installation Instructions

### Setting up the virtual environment

``aos2tosca`` is written in Python3.  We recommend that you run the
``oas2tosca`` software in its own virtual environment. Create and activate 
your virtual environment as follows:

    python3 -m venv env
    source env/bin/activate
    
``oas2tosca`` uses
[PEP-517](https://www.python.org/dev/peps/pep-0517/) and
[PEP-518](https://www.python.org/dev/peps/pep-0518/) based
installation systems that require the latest version of ``pip``. To
upgrade ``pip`` to the latest version, run the following command in
your virtual environment:

    pip install -U pip 

### Installing the ``oas2tosca`` software

The software can be installed directly from the git repository by
running the following command in your virtual environment:

    pip install git+https://github.com/lauwers/oas2tosca
    
Alternatively, you can also clone the git repo first and then run the
installer in your local copy as follows:

    git clone https://github.com/lauwers/oas2tosca
    cd oas2tosca
    pip install . 
    
You can verify that the ``oas2tosca`` software has been installed by
running the following command in your virtual environment:

    oas2tosca --version

This will display the version of the installed software. Please
include the version number when reporting issues.

## Using ``oas2tosca``

To convert an OpenAPI file, run the following command in your virtual
environment:

    oas2tosca --input <OpenAPI file> --output <TOSCA Profile directory>
    
Note that ``oas2tosca`` outputs profile *directories* rather than
profile *CSAR files*, since it is possible that a single OpenAPI file
can result in the creation of multiple TOSCA profiles.

### Using ``oas2tosca`` to create Kubernetes profiles

You can use ``oas2tosca`` to automatically create TOSCA Kubernetes
profiles from the k8s ``swagger.json`` file. Please note:

- ``oas2tosca`` will create multiple TOSCA profiles from the k8s
  swagger.json file, one for each API group.

- ``oas2tosca`` creates TOSCA profiles, which are a TOSCA v2.0
  concept. However, ``oas2tosca`` back-ports v2.0 profiles to
  v1.x. Whereas v2.0 profiles advertizes their profile name using the
  ``profile`` keyword, ``oas2tosca`` uses the ``namespace`` keyword
  instead to advertize the profile name. This profile name is then
  used in ``import`` statements to allow importing by other profiles.

- Because of limited profile version support in TOSCA, ``oas2tosca``
  currently only translates schemas marked as v1.


