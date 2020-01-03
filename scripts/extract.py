#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to extract an ESE database catalog."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import logging
import os
import sys

from esedbrc import catalog_extractor
from esedbrc import definitions
from esedbrc import database


class Sqlite3OutputWriter(object):
  """SQLite3 output writer."""

  def __init__(self, databases_path):
    """Initializes an output writer.

    Args:
      databases_path (str): path to the database files.
    """
    super(Sqlite3OutputWriter, self).__init__()
    self._databases_path = databases_path
    self._database_writer = None

  def _WriteTableDefinition(self, table_definition):
    """Writes the table definition.

    Args:
      table_definition (EseTableDefinition): table definition.
    """
    # TODO: detect tables with duplicate names and different definitions.
    self._database_writer.WriteTableDefinition(table_definition)

    table_definition_key = self._database_writer.GetTableDefinitionKey(
        table_definition)

    for column_definition in table_definition.column_definitions:
      self._database_writer.WriteColumnDefinition(
          table_definition_key, column_definition)

  def Close(self):
    """Closes the output writer object."""
    self._database_writer.Close()
    self._database_writer = None

  def Open(self, database_type):
    """Opens the output writer object.

    Args:
      database_type (str): ESE database type.

    Returns:
      bool: True if successful or False if not.
    """
    if not os.path.isdir(self._databases_path):
      return False

    database_filename = '{0:s}.db'.format(database_type)
    self._database_writer = database.EseDbCatalogSqlite3DatabaseWriter()
    self._database_writer.Open(os.path.join(
        self._databases_path, database_filename))

    return True

  def WriteDatabaseDefinition(self, database_definition):
    """Writes the database definition.

    Args:
      database_definition (EseDatabaseDefinition): database definition.
    """
    self._database_writer.WriteDatabaseDefinition(database_definition)

  def WriteTableDefinitions(self, table_definitions):
    """Writes the table definitions.

    Args:
      table_definitions (list[EseTableDefinition]): table definitions.
    """
    for table_definition in table_definitions:
      self._WriteTableDefinition(table_definition)


class StdoutWriter(object):
  """Stdout output writer."""

  def _GetTableLinkName(self, common_table_name):
    """Retrieves the table link name.

    Args:
      common_table_name (str): common table name.

    Returns:
      str: table link name.
    """
    link_name = 'table_{0:s}'.format(common_table_name.lower())
    if link_name.endswith('_#'):
      link_name = link_name[:-2]

    return link_name

  def _WriteColumnDefinition(self, column_definition):
    """Writes the column definition.

    Args:
      column_definition (EseColumnDefinition): column definition.
    """
    column_type = definitions.COLUMN_TYPE_DESCRIPTIONS.get(
        column_definition.type, 'UNKNOWN')
    print('| {0:d} | {1:s} | {2:s}'.format(
        column_definition.identifier, column_definition.name,
        column_type))

  def _WriteTableDefinition(self, table_definition):
    """Writes the table definition.

    Args:
      table_definition (EseTableDefinition): table definition.
    """
    self._WriteTableHeader(table_definition)

    for column_definition in table_definition.column_definitions:
      self._WriteColumnDefinition(column_definition)

    self._WriteTableFooter()

  def _WriteTableFooter(self):
    """Writes the table footer."""
    print('|===')
    print('')

  def _WriteTableHeader(self, table_definition):
    """Writes the table header.

    Args:
      table_definition (EseTableDefinition): table definition.
    """
    common_table_name = table_definition.GetCommonName()
    link_name = self._GetTableLinkName(common_table_name)

    print('=== [[{0:s}]]{1:s}'.format(link_name, common_table_name))

    if table_definition.template_table_name:
      print('Template table: {0:s}'.format(
          table_definition.template_table_name))

    print('')
    print('[cols="1,3,5",options="header"]')
    print('|===')
    print('| Column indentifier | Column name | Column type')

  def Close(self):
    """Closes the output writer object."""
    return

  def Open(self, database_type):  # pylint: disable=unused-argument
    """Opens the output writer object.

    Args:
      database_type (str): ESE database type.

    Returns:
      bool: True if successful or False if not.
    """
    return True

  def WriteDatabaseDefinition(self, database_definition):
    """Writes the database definition.

    Args:
      database_definition (EseDatabaseDefinition): database definition.
    """
    print('== {0:s} {1:s}'.format(
        database_definition.type, database_definition.version))
    print('')

  def WriteTableDefinitions(self, table_definitions):
    """Writes the table definitions.

    Args:
      table_definitions (list[EseTableDefinition]): table definitions.
    """
    print('=== Tables')
    print('')

    for table_definition in table_definitions:
      common_table_name = table_definition.GetCommonName()
      link_name = self._GetTableLinkName(common_table_name)

      print('* <<{0:s},{1:s}>>'.format(link_name, common_table_name))

    print('')

    for table_definition in table_definitions:
      self._WriteTableDefinition(table_definition)


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  args_parser = argparse.ArgumentParser(description=(
      'Extract the catalog from the ESE database file.'))

  args_parser.add_argument(
      'source', action='store', nargs='?', default=None,
      help='path of the ESE database file.', metavar='/mnt/c/')

  args_parser.add_argument(
      'database_type', action='store', nargs='?', default=None,
      help='string that identifies the ESE database type.',
      metavar='search')

  args_parser.add_argument(
      'database_version', action='store', nargs='?', default=None,
      help='string that identifies the ESE database version.',
      metavar='XP')

  args_parser.add_argument(
      '--db', '--database', action='store', default=None,
      help='directory to write the sqlite3 databases to.',
      metavar='./esedb-kb/', dest='database')

  options = args_parser.parse_args()

  if not options.source:
    print('Source value is missing.')
    print('')
    args_parser.print_help()
    print('')
    return False

  if not os.path.exists(options.source):
    print('No such source: {0:s}.'.format(options.source))
    print('')
    return False

  if not options.database_type:
    print('Database type value is missing.')
    print('')
    return False

  if not options.database_version:
    print('Database version value is missing.')
    print('')
    return False

  logging.basicConfig(
      level=logging.INFO, format='[%(levelname)s] %(message)s')

  if options.database:
    if not os.path.exists(options.database):
      os.mkdir(options.database)

    if not os.path.isdir(options.database):
      print('{0:s} must be a directory'.format(options.database))
      print('')
      return False

    output_writer = Sqlite3OutputWriter(options.database)
  else:
    output_writer = StdoutWriter()

  if not output_writer.Open(options.database_type):
    print('Unable to open output writer.')
    print('')
    return False

  # TODO: do something with options.database_type, options.database_version
  # or remove.

  extractor = catalog_extractor.EseDbCatalogExtractor()

  # TODO: read table and index overlays from file.
  # maybe something for an export script.
  # overlays = {}

  # TODO: add support to read multiple files from a directory.

  extractor.ExtractCatalog(options.source, output_writer)
  output_writer.Close()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
