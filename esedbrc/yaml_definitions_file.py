# -*- coding: utf-8 -*-
"""YAML-based database definitions file."""

import yaml

from esedbrc import resources


class YAMLDatabaseDefinitionsFile(object):
  """YAML-based database definitions file.

  A YAML-based database definitions file contains one or more database
  definitions. A database definition consists of:

  artifact_definition: SafariCacheSQLiteDatabaseFile
  database_identifier: safari:cache.db

  Where:
  * artifact_definition, name of the corresponding Digital Forensics Artifact
      definition.
  * database_identifier, identifier of the database type.
  """

  _SUPPORTED_KEYS = frozenset([
      'artifact_definition',
      'database_identifier'])

  def _ReadDatabaseDefinition(self, yaml_database_definition):
    """Reads a database definition from a dictionary.

    Args:
      yaml_database_definition (dict[str, object]): YAML database definition
           values.

    Returns:
      DatabaseDefinition: database definition.

    Raises:
      RuntimeError: if the format of the formatter definition is not set
          or incorrect.
    """
    if not yaml_database_definition:
      raise RuntimeError('Missing database definition values.')

    different_keys = set(yaml_database_definition) - self._SUPPORTED_KEYS
    if different_keys:
      different_keys = ', '.join(different_keys)
      raise RuntimeError('Undefined keys: {0:s}'.format(different_keys))

    artifact_definition = yaml_database_definition.get(
        'artifact_definition', None)
    if not artifact_definition:
      raise RuntimeError(
          'Invalid database definition missing format identifier.')

    database_identifier = yaml_database_definition.get(
        'database_identifier', None)
    if not database_identifier:
      raise RuntimeError(
          'Invalid database definition missing database identifier.')

    database_definition = resources.DatabaseDefinition()
    database_definition.artifact_definition = artifact_definition
    database_definition.database_identifier = database_identifier

    return database_definition

  def _ReadFromFileObject(self, file_object):
    """Reads the event formatters from a file-like object.

    Args:
      file_object (file): formatters file-like object.

    Yields:
      DatabaseDefinition: database definition.
    """
    yaml_generator = yaml.safe_load_all(file_object)

    for yaml_database_definition in yaml_generator:
      yield self._ReadDatabaseDefinition(yaml_database_definition)

  def ReadFromFile(self, path):
    """Reads the event formatters from a YAML file.

    Args:
      path (str): path to a formatters file.

    Yields:
      DatabaseDefinition: database definition.
    """
    with open(path, 'r', encoding='utf-8') as file_object:
      yield from self._ReadFromFileObject(file_object)
