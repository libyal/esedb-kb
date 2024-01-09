#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ESE database schema extractor."""

import logging
import os

import pyesedb

from artifacts import definitions as artifacts_definitions
from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from dfimagetools import definitions as dfimagetools_definitions
from dfimagetools import file_entry_lister

from esedbrc import resources
from esedbrc import yaml_definitions_file


class EseDbSchemaExtractor(object):
  """ESE database schema extractor."""

  _DATABASE_DEFINITIONS_FILE = (
      os.path.join(os.path.dirname(__file__), 'data', 'known_databases.yaml'))

  _MINIMUM_FILE_SIZE = 16

  def __init__(self, artifact_definitions, mediator=None):
    """Initializes a ESE database file schema extractor.

    Args:
      artifact_definitions (str): path to a single artifact definitions
          YAML file or a directory of definitions YAML files.
      mediator (Optional[dfvfs.VolumeScannerMediator]): a volume scanner
          mediator.
    """
    super(EseDbSchemaExtractor, self).__init__()
    self._artifacts_registry = artifacts_registry.ArtifactDefinitionsRegistry()
    self._known_database_definitions = {}
    self._mediator = mediator

    if artifact_definitions:
      reader = artifacts_reader.YamlArtifactsReader()
      if os.path.isdir(artifact_definitions):
        self._artifacts_registry.ReadFromDirectory(reader, artifact_definitions)
      elif os.path.isfile(artifact_definitions):
        self._artifacts_registry.ReadFromFile(reader, artifact_definitions)

    definitions_file = yaml_definitions_file.YAMLDatabaseDefinitionsFile()
    for database_definition in definitions_file.ReadFromFile(
        self._DATABASE_DEFINITIONS_FILE):
      artifact_definition = self._artifacts_registry.GetDefinitionByName(
          database_definition.artifact_definition)
      if not artifact_definition:
        logging.warning((f'Unknown artifact definition: '
                         f'{database_definition.artifact_definition:s}'))
      else:
        self._known_database_definitions[
            database_definition.database_identifier] = artifact_definition

  def _CheckSignature(self, file_object):
    """Checks the signature of a given database file-like object.

    Args:
      file_object (dfvfs.FileIO): file-like object of the database.

    Returns:
      bool: True if the signature matches that of a ESE database, False
          otherwise.
    """
    if not file_object:
      return False

    file_object.seek(4, os.SEEK_SET)
    file_data = file_object.read(4)
    return file_data == b'\xef\xcd\xab\x89'

  def _FormatSchemaAsYAML(self, schema):
    """Formats a schema into YAML.

    Args:
      schema (list[EseTableDefinition]): schema as unique table definitions or
          None if the schema could not be retrieved.

    Returns:
      str: schema formatted as YAML.

    Raises:
      RuntimeError: if a query could not be parsed.
    """
    lines = ['# esedb-kb database schema.']

    for table_definition in sorted(
        schema, key=lambda table_definition: table_definition.name):
      lines.extend([
          '---',
          f'table: {table_definition.name:s}',
          'columns:'])

      for column_definition in table_definition.column_definitions:
        # TODO: convert type to human readable string.
        lines.extend([
            f'- name: {column_definition.name:s}',
            f'  value_type: {column_definition.type:d}'])

    lines.append('')
    return '\n'.join(lines)

  def _GetDatabaseIdentifier(self, path_segments):
    """Determines the database identifier.

    Args:
      path_segments (list[str]): path segments.

    Returns:
      str: database identifier or None if the type could not be determined.
    """
    # TODO: make comparison more efficient.
    for database_identifier, artifact_definition in (
        self._known_database_definitions.items()):
      for source in artifact_definition.sources:
        if source.type_indicator in (
            artifacts_definitions.TYPE_INDICATOR_DIRECTORY,
            artifacts_definitions.TYPE_INDICATOR_FILE,
            artifacts_definitions.TYPE_INDICATOR_PATH):
          for source_path in set(source.paths):
            source_path_segments = source_path.split(source.separator)

            if not source_path_segments[0]:
              source_path_segments = source_path_segments[1:]

            # TODO: add support for parameters.
            last_index = len(source_path_segments)
            for index in range(1, last_index + 1):
              source_path_segment = source_path_segments[-index]
              if not source_path_segment or len(source_path_segment) < 2:
                continue

              if (source_path_segment[0] == '%' and
                  source_path_segment[-1] == '%'):
                source_path_segments = source_path_segments[-index + 1:]
                break

            if len(source_path_segments) > len(path_segments):
              continue

            is_match = True
            last_index = min(len(source_path_segments), len(path_segments))
            for index in range(1, last_index + 1):
              source_path_segment = source_path_segments[-index]
              # TODO: improve handling of *
              if '*' in source_path_segment:
                continue

              path_segment = path_segments[-index].lower()
              source_path_segment = source_path_segment.lower()

              is_match = path_segment == source_path_segment
              if not is_match:
                break

            if is_match:
              return database_identifier

    return None

  def _GetDatabaseSchema(self, database_path):
    """Retrieves schema from given database.

    Args:
      database_path (str): file path to database.

    Returns:
      list[EseTableDefinition]: schema as unique table definitions or None if
          the schema could not be retrieved.
    """
    with open(database_path, 'rb') as file_object:
      return self._GetDatabaseSchemaFromFileObject(file_object)

  def _GetDatabaseSchemaFromFileObject(self, file_object):
    """Retrieves schema from given database file-like object.

    Args:
      file_object (dfvfs.FileIO): file-like object of the database.

    Returns:
      list[EseTableDefinition]: schema as unique table definitions or None if
          the schema could not be retrieved.
    """
    esedb_file = pyesedb.file()
    esedb_file.open_file_object(file_object)

    try:
      table_definitions = []
      for esedb_table in iter(esedb_file.tables):
        table_definition = resources.EseTableDefinition(
            esedb_table.name, esedb_table.template_name)

        for esedb_column in esedb_table.columns:
          table_definition.AddColumnDefinition(
              esedb_column.identifier, esedb_column.name, esedb_column.type)

        table_definitions.append(table_definition)

      unique_table_definitions = []
      for table_definition in table_definitions:
        table_columns = [
            definition.CopyToDict()
            for definition in table_definition.column_definitions]

        is_unique_table = True
        for compare_table_definition in unique_table_definitions:
          compare_table_columns = [
              definition.CopyToDict()
              for definition in compare_table_definition.column_definitions]

          if table_columns == compare_table_columns:
            compare_table_definition.aliases.append(table_definition.name)
            is_unique_table = False

        if is_unique_table:
          unique_table_definitions.append(table_definition)

    finally:
      esedb_file.close()

    # TODO: move schema into object.
    return unique_table_definitions

  def GetDisplayPath(self, path_segments, data_stream_name=None):
    """Retrieves a path to display.

    Args:
      path_segments (list[str]): path segments of the full path of the file
          entry.
      data_stream_name (Optional[str]): name of the data stream.

    Returns:
      str: path to display.
    """
    display_path = ''

    path_segments = [
        segment.translate(
            dfimagetools_definitions.NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE)
        for segment in path_segments]
    display_path = ''.join([display_path, '/'.join(path_segments)])

    if data_stream_name:
      data_stream_name = data_stream_name.translate(
          dfimagetools_definitions.NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE)
      display_path = ':'.join([display_path, data_stream_name])

    return display_path or '/'

  def ExtractSchemas(self, path, options=None):
    """Extracts database schemas from the path.

    Args:
      path (str): path of a ESE database file or storage media image containing
          ESE database files.
      options (Optional[dfvfs.VolumeScannerOptions]): volume scanner options. If
          None the default volume scanner options are used, which are defined in
          the dfVFS VolumeScannerOptions class.

    Yields:
      tuple[str, dict[str, str]]: known database type identifier or the name of
          the ESE database file if not known and schema.
    """
    entry_lister = file_entry_lister.FileEntryLister(mediator=self._mediator)

    base_path_specs = entry_lister.GetBasePathSpecs(path, options=options)
    if not base_path_specs:
      logging.warning(
          f'Unable to determine base path specifications from: {path:s}')

    else:
      for file_entry, path_segments in entry_lister.ListFileEntries(
          base_path_specs):
        if not file_entry.IsFile() or file_entry.size < self._MINIMUM_FILE_SIZE:
          continue

        file_object = file_entry.GetFileObject()
        if not self._CheckSignature(file_object):
          continue

        display_path = self.GetDisplayPath(path_segments)
        # logging.info(
        #   f'Extracting schema from database file: {display_path:s}')

        database_schema = self._GetDatabaseSchemaFromFileObject(file_object)
        if database_schema is None:
          logging.warning((
              f'Unable to determine schema from database file: '
              f'{display_path:s}'))
          continue

        # TODO: improve support to determine identifier for single database
        # file.
        database_identifier = self._GetDatabaseIdentifier(path_segments)
        if not database_identifier:
          logging.warning((
              f'Unable to determine known database identifier of file: '
              f'{display_path:s}'))

          database_identifier = path_segments[-1]

        yield database_identifier, database_schema

  def FormatSchema(self, schema, output_format):
    """Formats a schema into a word-wrapped string.

    Args:
      schema (dict[str, str]): schema as an SQL query per table name.
      output_format (str): output format.

    Returns:
      str: formatted schema.

    Raises:
      RuntimeError: if a query could not be parsed.
    """
    if output_format == 'yaml':
      return self._FormatSchemaAsYAML(schema)

    raise RuntimeError(f'Unsupported output format: {output_format:s}')
