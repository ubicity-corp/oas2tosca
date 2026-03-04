# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`oas2tosca` converts OpenAPI Specification files (v2 and v3) to TOSCA Simple Profile in YAML v1.3 profiles. It outputs profile *directories* (not single files), since one OAS file can produce multiple TOSCA profiles.

## Commands

### Installation
```bash
python3 -m venv env
source env/bin/activate
pip install -U pip
pip install .
```

### Running the Tool
```bash
oas2tosca --input <OpenAPI file> --output <TOSCA Profile directory>
oas2tosca --input <OpenAPI file> --output <dir> --debug   # verbose logging
oas2tosca --version
```

### Running Directly (without installation)
```bash
python -m oas2tosca --input <OpenAPI file> --output <dir>
```

There are no tests in this codebase currently.

## Architecture

### Module Structure

- **`__main__.py`** — CLI entry point. Reads the OAS file, detects version, and dispatches to the appropriate converter class.
- **`read_oas.py`** — Reads OAS/Swagger files (JSON or YAML) using `ruamel.yaml`'s YAML parser (which handles JSON as a subset).
- **`swagger.py`** — Base `Swagger` class containing version-independent conversion logic. Subclassed for version-specific behavior.
- **`swagger2.py`** — `Swagger2` subclass: handles OAS v2 specifics. Schemas come from `definitions`, body parameters drive node type creation.
- **`swagger3.py`** — `Swagger3` subclass: handles OAS v3 specifics. Schemas come from `components/schemas`, `requestBody` and `200` responses drive node type creation.
- **`profile.py`** — `Profile` class that manages TOSCA output. Writes profile directory structure and TOSCA YAML content.
- **`__init__.py`** — Package version string.

### Conversion Pipeline

`Swagger.convert()` orchestrates four phases:

1. **`get_profiles_from_schemas()`** — Parses all schema names to extract profile name, version, kind, and prefix. Each unique profile name maps to a `Profile` object. Cross-schema `$ref` references determine inter-profile dependencies.

2. **`initialize_profiles(top, info)`** — Creates output directory structure for each profile.

3. **`process_paths()`** — Iterates API paths. For each path with a `POST`, `PUT`, or `GET` operation, creates a TOSCA node type from the operation's body schema (POST/PUT) or success response schema (GET). Schemas with a single array property are treated as containers — the contained item type is used instead.

4. **`process_deferred_schemas()`** — Creates TOSCA data types for all schemas referenced as property types within node type schemas. These are processed after node types to handle forward references.

### Schema Name Parsing

`parse_schema_name()` extracts a 4-tuple `(profile, version, kind, prefix)` from dotted schema names (e.g., `io.k8s.api.core.v1.Pod` → profile=`io.k8s.api.core`, version=`v1`, kind=`Pod`, prefix=`core`). Only `v1` schemas are processed; others are skipped.

### Key Design Constraints

- Only local `$ref` references (starting with `#`) are supported.
- Only `application/json` content type is processed in OAS v3.
- Only schemas with `"type": "object"` can become node types.
- Only `v1` versioned schemas are translated (Kubernetes-centric design).
- `x-swagger-router-model` overrides the schema name if present.
- `x-kubernetes-group-version-kind` is recognized but informational only.

### Dependency: `ruamel.yaml`

The only runtime dependency. Used to parse both JSON and YAML OAS files (YAML is a superset of JSON).
