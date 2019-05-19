#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to extract an ESE database catalog."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import logging
import os
import sys

import pyesedb

import database


if pyesedb.get_version() < '20140406':
  raise ImportWarning('extract.py requires pyesedb 20140406 or later.')


COLUMN_TYPE_DESCRIPTIONS = {
    pyesedb.column_types.NULL: 'Null',
    pyesedb.column_types.BOOLEAN: 'Boolean',
    pyesedb.column_types.INTEGER_8BIT_UNSIGNED: 'Integer 8-bit unsigned',
    pyesedb.column_types.INTEGER_16BIT_SIGNED: 'Integer 16-bit signed',
    pyesedb.column_types.INTEGER_32BIT_SIGNED: 'Integer 32-bit signed',
    pyesedb.column_types.CURRENCY: 'Currency',
    pyesedb.column_types.FLOAT_32BIT: 'Floating point 32-bit',
    pyesedb.column_types.DOUBLE_64BIT: 'Floating point 64-bit',
    pyesedb.column_types.DATE_TIME: 'Filetime',
    pyesedb.column_types.BINARY_DATA: 'Binary data',
    pyesedb.column_types.TEXT: 'Text',
    pyesedb.column_types.LARGE_BINARY_DATA: 'Large binary data',
    pyesedb.column_types.LARGE_TEXT: 'Large text',
    pyesedb.column_types.SUPER_LARGE_VALUE: 'Super large value',
    pyesedb.column_types.INTEGER_32BIT_UNSIGNED: 'Integer 32-bit unsigned',
    pyesedb.column_types.INTEGER_64BIT_SIGNED: 'Integer 64-bit signed',
    pyesedb.column_types.GUID: 'GUID',
    pyesedb.column_types.INTEGER_16BIT_UNSIGNED: 'Integer 16-bit unsigned',
}

COLUMN_TYPE_IDENTIFIERS = {
    pyesedb.column_types.NULL: 'JET_coltypNil',
    pyesedb.column_types.BOOLEAN: 'JET_coltypBit',
    pyesedb.column_types.INTEGER_8BIT_UNSIGNED: 'JET_coltypUnsignedByte',
    pyesedb.column_types.INTEGER_16BIT_SIGNED: 'JET_coltypShort',
    pyesedb.column_types.INTEGER_32BIT_SIGNED: 'JET_coltypLong',
    pyesedb.column_types.CURRENCY: 'JET_coltypCurrency',
    pyesedb.column_types.FLOAT_32BIT: 'JET_coltypIEEESingle',
    pyesedb.column_types.DOUBLE_64BIT: 'JET_coltypIEEEDouble',
    pyesedb.column_types.DATE_TIME: 'JET_coltypDateTime',
    pyesedb.column_types.BINARY_DATA: 'JET_coltypBinary',
    pyesedb.column_types.TEXT: 'JET_coltypText',
    pyesedb.column_types.LARGE_BINARY_DATA: 'JET_coltypLongBinary',
    pyesedb.column_types.LARGE_TEXT: 'JET_coltypLongText',
    pyesedb.column_types.SUPER_LARGE_VALUE: 'JET_coltypSLV',
    pyesedb.column_types.INTEGER_32BIT_UNSIGNED: 'JET_coltypUnsignedLong',
    pyesedb.column_types.INTEGER_64BIT_SIGNED: 'JET_coltypLongLong',
    pyesedb.column_types.GUID: 'JET_coltypGUID',
    pyesedb.column_types.INTEGER_16BIT_UNSIGNED: 'JET_coltypUnsignedShort',
}


class EseColumnDefinition(object):
  """ESE database column definition."""

  def __init__(self, column_identifier, column_name, column_type):
    """Initializes an ESE database column definition.

    Args:
      column_identifier (str): column identifier.
      column_name (str): column name.
      column_type (str): column type.
   """
    super(EseColumnDefinition, self).__init__()
    self.identifier = column_identifier
    self.name = column_name
    self.type = column_type


class EseDatabaseDefinition(object):
  """ESE database definition."""

  def __init__(self, database_type, database_version):
    """Initializes an ESE database database definition.

    Args:
      database_type (str): ESE database type.
      database_version (str): ESE database version.
   """
    super(EseDatabaseDefinition, self).__init__()
    self.type = database_type
    self.version = database_version


class EseTableDefinition(object):
  """ESE database table definition."""

  def __init__(self, table_name, template_table_name):
    """Initializes an ESE database table definition.

    Args:
      table_name (str): table name.
      template_table_name (str): template table name.
   """
    super(EseTableDefinition, self).__init__()
    self.column_definitions = []
    self.name = table_name
    self.template_table_name = template_table_name

  def AddColumnDefinition(self, column_identifier, column_name, column_type):
    """Adds a column.

    Args:
      column_identifier (str): column identifier.
      column_name (str): column name.
      column_type (str): column type.
    """
    ese_column_definition = EseColumnDefinition(
        column_identifier, column_name, column_type)
    self.column_definitions.append(ese_column_definition)


class ColumnOverlay(object):
  """Column overlay."""

  def __init__(self, column_identifier, column_name, column_type):
    """Initializes a column overlay.

    Args:
      column_identifier (str): column identifier.
      column_name (str): column name.
      column_type (str): column type.
    """
    super(ColumnOverlay, self).__init__()
    self.column_identifier = column_identifier
    self.column_name = column_name
    self.column_type = column_type

  @property
  def comparable(self):
    """str: comparable identifier."""
    return 'identifier: {0:s}, name: {1:s}, type: {2:s}'.format(
        self.column_identifier, self.column_name, self.column_type)


class TableOverlay(object):
  """Table overlay."""

  def __init__(self, table_name):
    """Initializes a table overlay.

    Args:
      table_name (str): table name.
    """
    super(TableOverlay, self).__init__()
    self.table_name = table_name
    self._column_overlays = {}

  def AppendColumnOverlay(self, column_overlay):
    """Appends a column overlay.

    Args:
      column_overlay (ColumnOverlay): column overlay.

    Raises:
      KeyError: if the column overlay is already set.
    """
    if column_overlay.comparable in self._column_overlays:
      raise KeyError('Column overlay: {0:s} already set.'.format(
          column_overlay.comparable))

    self._column_overlays[column_overlay.comparable] = column_overlay


class EseDbCatalogExtractor(object):
  """ESE database catalog extractor."""

  def __init__(self, database_type, database_version):
    """Initializes an ESE database catalog extractor.

    Args:
      database_type (str): ESE database type.
      database_version (str): ESE database version.
    """
    super(EseDbCatalogExtractor, self).__init__()
    self._database_type = database_type
    self._database_version = database_version

  def ExtractCatalog(self, filename, output_writer):
    """Extracts the catalog from the database.

    Args:
      filename (str): name of the file containing the ESE database.
      output_writer (OutputWriter): output writer.
    """
    esedb_file = pyesedb.file()
    esedb_file.open(filename)

    ese_database_definition = EseDatabaseDefinition(
        self._database_type, self._database_version)

    output_writer.WriteDatabaseDefinition(ese_database_definition)

    # TODO: write an overview of the table names.
    # TODO: write the table and index names per type and version.

    for esedb_table in iter(esedb_file.tables):
      ese_table_definition = EseTableDefinition(
          esedb_table.name, esedb_table.template_name)

      for esedb_column in esedb_table.columns:
        ese_table_definition.AddColumnDefinition(
            esedb_column.identifier, esedb_column.name, esedb_column.type)

      output_writer.WriteTableDefinition(ese_table_definition)

    esedb_file.close()


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

  def WriteDatabaseDefinition(self, ese_database_definition):
    """Writes the database definition.

    Args:
      ese_database_definition (EseDatabaseDefinition): database definition.
    """
    self._database_writer.WriteDatabaseDefinition(ese_database_definition)

  def WriteTableDefinition(self, ese_table_definition):
    """Writes the table definition.

    Args:
      ese_table_definition (EseTableDefinition): table definition.
    """
    # TODO: detect tables with duplicate names and different definitions.
    self._database_writer.WriteTableDefinition(ese_table_definition)

    table_definition_key = self._database_writer.GetTableDefinitionKey(
        ese_table_definition)

    for ese_column_definition in ese_table_definition.column_definitions:
      self._database_writer.WriteColumnDefinition(
          table_definition_key, ese_column_definition)


class StdoutWriter(object):
  """Stdout output writer."""

  def _WriteColumnDefinition(self, ese_column_definition):
    """Writes the column definition.

    Args:
      ese_column_definition (EseColumnDefinition): column definition.
    """
    column_type = COLUMN_TYPE_DESCRIPTIONS.get(
        ese_column_definition.type, 'UNKNOWN')
    print('| {0:d} | {1:s} | {2:s}'.format(
        ese_column_definition.identifier, ese_column_definition.name,
        column_type))

  def _WriteTableFooter(self):
    """Writes the table footer."""
    print('|===')
    print('')

  def _WriteTableHeader(self, table_name, template_table_name):
    """Writes the table header.

    Args:
      table_name (str): table name.
      template_table_name (str): template table name.
    """
    print('=== [[{0:s}]]{1:s}'.format(
        table_name.lower(), table_name))

    if template_table_name:
      print('Template table: {0:s}'.format(template_table_name))

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

  def WriteDatabaseDefinition(self, ese_database_definition):
    """Writes the database definition.

    Args:
      ese_database_definition (EseDatabaseDefinition): database definition.
    """
    print('== {0:s} {1:s}'.format(
        ese_database_definition.type, ese_database_definition.version))
    print('')

  def WriteTableDefinition(self, ese_table_definition):
    """Writes the table definition.

    Args:
      ese_table_definition (EseTableDefinition): table definition.
    """
    self._WriteTableHeader(
        ese_table_definition.name, ese_table_definition.template_table_name)

    for ese_column_definition in ese_table_definition.column_definitions:
      self._WriteColumnDefinition(ese_column_definition)

    self._WriteTableFooter()


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

  extractor = EseDbCatalogExtractor(
      options.database_type, options.database_version)

  # TODO: read table and index overlays from file.
  # maybe something for an export script.
  # overlays = {}

  extractor.ExtractCatalog(options.source, output_writer)
  output_writer.Close()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
