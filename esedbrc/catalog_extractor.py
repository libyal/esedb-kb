#!/usr/bin/python
# -*- coding: utf-8 -*-
"""ESE database catalog extractor."""

import pyesedb

from esedbrc import resources


class EseDbCatalogExtractor(object):
  """ESE database catalog extractor."""

  _TABLES_PER_DATABASE_TYPE = {
      'exchange': frozenset([
          'Folders', 'Global', 'Mailbox', 'Msg', 'PerUserRead']),
      'search': frozenset([
          'SystemIndex_0A', 'SystemIndex_Gthr']),
      'security': frozenset([
          'SmTblSection', 'SmTblVersion']),
      'srum': frozenset([
          'SruDbIdMapTable', '{D10CA2FE-6FCF-4F6D-848E-B2E99266FA86}',
          '{D10CA2FE-6FCF-4F6D-848E-B2E99266FA89}',
          '{FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}',
          '{973F5D5C-1D90-4944-BE8E-24B94231A174}',
          '{FEE4E14F-02A9-4550-B5CE-5FA2DA202E37}LT',
          '{DD6636C4-8929-4683-974E-22C046A43763}']),
      'webcache': frozenset([
          'Containers', 'LeakFiles', 'Partitions']),
      'webcache_ex': frozenset([
          'Containers', 'LeakFiles', 'PartitionsEx']),
  }

  def __init__(self):
    """Initializes an ESE database catalog extractor."""
    super(EseDbCatalogExtractor, self).__init__()
    self._database_type = None
    self._database_version = None

  def _DetermineDatabaseType(self, table_names):
    """Determines the database type.

    Args:
      table_names (set[str]): table names.

    Returns:
      str: database type or None if the database type could not be determined.
    """
    for database_type, database_table_names in (
        self._TABLES_PER_DATABASE_TYPE.items()):
      if database_table_names.issubset(table_names):
        return database_type

    return None

  def ExtractCatalog(self, filename, output_writer):
    """Extracts the catalog from the database.

    Args:
      filename (str): name of the file containing the ESE database.
      output_writer (OutputWriter): output writer.
    """
    esedb_file = pyesedb.file()
    esedb_file.open(filename)

    # TODO: write an overview of the table names.
    # TODO: write the table and index names per type and version.

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

    table_names = frozenset([
        table_definition.GetCommonName()
        for table_definition in unique_table_definitions])

    database_type = self._DetermineDatabaseType(table_names)

    ese_database_definition = resources.EseDatabaseDefinition(
        database_type, 'unknown')

    output_writer.WriteDatabaseDefinition(ese_database_definition)

    output_writer.WriteTableDefinitions(unique_table_definitions)

    esedb_file.close()
