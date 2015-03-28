#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to extract an ESE database catalog."""

import argparse
import logging
import os
import sys

import pyesedb


# pylint: disable=superfluous-parens

if pyesedb.get_version() < u'20140406':
  raise ImportWarning(u'extract.py requires pyesedb 20140406 or later.')

COLUMN_TYPE_DESCRIPTIONS = {
    pyesedb.column_types.NULL: u'Null',
    pyesedb.column_types.BOOLEAN: u'Boolean',
    pyesedb.column_types.INTEGER_8BIT_UNSIGNED: u'Integer 8-bit unsigned',
    pyesedb.column_types.INTEGER_16BIT_SIGNED: u'Integer 16-bit signed',
    pyesedb.column_types.INTEGER_32BIT_SIGNED: u'Integer 32-bit signed',
    pyesedb.column_types.CURRENCY: u'Currency',
    pyesedb.column_types.FLOAT_32BIT: u'Floating point 32-bit',
    pyesedb.column_types.DOUBLE_64BIT: u'Floating point 64-bit',
    pyesedb.column_types.DATE_TIME: u'Filetime',
    pyesedb.column_types.BINARY_DATA: u'Binary data',
    pyesedb.column_types.TEXT: u'Text',
    pyesedb.column_types.LARGE_BINARY_DATA: u'Large binary data',
    pyesedb.column_types.LARGE_TEXT: u'Large text',
    pyesedb.column_types.SUPER_LARGE_VALUE: u'Super large value',
    pyesedb.column_types.INTEGER_32BIT_UNSIGNED: u'Integer 32-bit unsigned',
    pyesedb.column_types.INTEGER_64BIT_SIGNED: u'Integer 64-bit signed',
    pyesedb.column_types.GUID: u'GUID',
    pyesedb.column_types.INTEGER_16BIT_UNSIGNED: u'Integer 16-bit unsigned',
}

COLUMN_TYPE_IDENTIFIERS = {
    pyesedb.column_types.NULL: u'JET_coltypNil',
    pyesedb.column_types.BOOLEAN: u'JET_coltypBit',
    pyesedb.column_types.INTEGER_8BIT_UNSIGNED: u'JET_coltypUnsignedByte',
    pyesedb.column_types.INTEGER_16BIT_SIGNED: u'JET_coltypShort',
    pyesedb.column_types.INTEGER_32BIT_SIGNED: u'JET_coltypLong',
    pyesedb.column_types.CURRENCY: u'JET_coltypCurrency',
    pyesedb.column_types.FLOAT_32BIT: u'JET_coltypIEEESingle',
    pyesedb.column_types.DOUBLE_64BIT: u'JET_coltypIEEEDouble',
    pyesedb.column_types.DATE_TIME: u'JET_coltypDateTime',
    pyesedb.column_types.BINARY_DATA: u'JET_coltypBinary',
    pyesedb.column_types.TEXT: u'JET_coltypText',
    pyesedb.column_types.LARGE_BINARY_DATA: u'JET_coltypLongBinary',
    pyesedb.column_types.LARGE_TEXT: u'JET_coltypLongText',
    pyesedb.column_types.SUPER_LARGE_VALUE: u'JET_coltypSLV',
    pyesedb.column_types.INTEGER_32BIT_UNSIGNED: u'JET_coltypUnsignedLong',
    pyesedb.column_types.INTEGER_64BIT_SIGNED: u'JET_coltypLongLong',
    pyesedb.column_types.GUID: u'JET_coltypGUID',
    pyesedb.column_types.INTEGER_16BIT_UNSIGNED: u'JET_coltypUnsignedShort',
}


class ColumnDefinition(object):
  """Class that defines an ESE database column definition."""

  def __init__(self, column_identifier, column_name, column_type):
    """Initializes the ESE database column definition object.

    Args:
      column_identifier: the column identifier.
      column_name: the column name.
      column_type: the column type.
   """
    super(ColumnDefinition, self).__init__()
    self.identifier = column_identifier
    self.name = column_name
    self.type = column_type


class TableDefinition(object):
  """Class that defines an ESE database table definition."""

  def __init__(self, table_name, template_table_name):
    """Initializes the ESE database table definition object.

    Args:
      table_name: the table name.
      template_table_name: the template table name.
   """
    super(TableDefinition, self).__init__()
    self.column_definitions = []
    self.name = table_name
    self.template_table_name = template_table_name

  def AddColumnDefinition(self, column_identifier, column_name, column_type):
    """Adds a column.

    Args:
      column_identifier: the column identifier.
      column_name: the column name.
      column_type: the column type.
    """
    column_definition = ColumnDefinition(
        column_identifier, column_name, column_type)
    self.column_definitions.append(column_definition)


class ColumnOverlay(object):
  """Class that defines a column overlay."""

  def __init__(self, column_identifier, column_name, column_type):
    """Initializes the column overlay.

    Args:
      column_identifier: the column identifier.
      column_name: the column name.
      column_type: the column type.
    """
    super(ColumnOverlay, self).__init__()
    self.column_identifier = column_identifier
    self.column_name = column_name
    self.column_type = column_type

  @property
  def comparable(self):
    return u'identifier: {0:s}, name: {1:s}, type: {2:s}'.format(
        self.column_identifier, self.column_name, self.column_type)


class TableOverlay(object):
  """Class that defines a table overlay."""

  def __init__(self, table_name):
    """Initializes the table overlay.

    Args:
      table_name: the table name.
    """
    super(TableOverlay, self).__init__()
    self.table_name = table_name
    self._column_overlays = {}

  def AppendColumnOverlay(self, column_overlay):
    """Appends a column overlay.

    Args:
      column_overlay: the column overlay.
    """
    if column_overlay.comparable in self._column_overlays:
      raise KeyError(u'Column overlay: {0:s} already set.'.format(
          column_overlay.comparable))

    self._column_overlays[column_overlay.comparable] = column_overlay


class EseDbCatalogExtractor(object):
  """Class that defines an ESE database catalog extractor."""

  def __init__(self):
    """Initializes the ESE database catalog extractor object."""
    super(EseDbCatalogExtractor, self).__init__()

  def ExtractCatalog(self, filename, output_writer):
    """Extracts the catalog from the database.

    Args:
      filenale: the name of the file containing the ESE database.
      output_writer: the output writer (instance of OutputWriter).
    """
    esedb_file = pyesedb.file()
    esedb_file.open(filename)

    # TODO: write the database type and version.
    # TODO: write the table and index names per type and version.

    for esedb_table in esedb_file.tables:
      table_definition = TableDefinition(
          esedb_table.name, esedb_table.template_name)

      for esedb_column in esedb_table.columns:
        table_definition.AddColumnDefinition(
            esedb_column.identifier, esedb_column.name, esedb_column.type)

      output_writer.WriteTableDefinition(table_definition)

    esedb_file.close()


class Sqlite3OutputWriter(object):
  """Class that defines a sqlite3 output writer."""

  EVENT_PROVIDERS_DATABASE_FILENAME = u'winevt-kb.db'

  def __init__(self, databases_path):
    """Initializes the output writer object.

    Args:
      databases_path: the path to the database files.
    """
    super(Sqlite3OutputWriter, self).__init__()
    self._databases_path = databases_path
    self._database_writer = None

  def Close(self):
    """Closes the output writer object."""
    self._database_writer.Close()
    self._database_writer = None

  def Open(self):
    """Opens the output writer object.

    Returns:
      A boolean containing True if successful or False if not.
    """
    if not os.path.isdir(self._databases_path):
      return False

    # TODO: implement.
    # self._database_writer = database.EseDbCatalogSqlite3DatabaseWriter()
    # self._database_writer.Open(os.path.join(
    #     self._databases_path, self.EVENT_PROVIDERS_DATABASE_FILENAME))

    return True

  def WriteTableDefinition(self, table_definition):
    """Writes the table definition.

    Args:
      table_definition: the table definition (instance of TableDefinition).
    """
    # TODO: implement.
    return


class StdoutWriter(object):
  """Class that defines a stdout output writer."""

  def _WriteColumnDefinition(self, column_definition):
    """Writes the column definition.

    Args:
      column_definition: the column definition (instance of ColumnDefinition).
    """
    column_type = COLUMN_TYPE_DESCRIPTIONS.get(
        column_definition.type, u'UNKNOWN')
    print(u'| {0:d} | {1:s} | {2:s}'.format(
        column_definition.identifier, column_definition.name, column_type))

  def _WriteTableFooter(self):
    """Writes the table footer."""
    print(u'|===')
    print(u'')

  def _WriteTableHeader(self, table_name, template_table_name):
    """Writes the table header.

    Args:
      table_name: the table name.
      template_table_name: the template table name.
    """
    print(u'== {0:s}'.format(table_name))

    if template_table_name:
      print(u'Template table: {0:s}'.format(template_table_name))

    print(u'')
    print(u'[cols="1,3,5",options="header"]')
    print(u'|===')
    print(u'| Column indentifier | Column name | Column type')

  def Close(self):
    """Closes the output writer object."""
    pass

  def Open(self):
    """Opens the output writer object.

    Returns:
      A boolean containing True if successful or False if not.
    """
    return True

  def WriteTableDefinition(self, table_definition):
    """Writes the table definition.

    Args:
      table_definition: the table definition (instance of TableDefinition).
    """
    self._WriteTableHeader(
        table_definition.name, table_definition.template_table_name)

    for column_definition in table_definition.column_definitions:
      self._WriteColumnDefinition(column_definition)

    self._WriteTableFooter()


def Main():
  """The main program function.

  Returns:
    A boolean containing True if successful or False if not.
  """
  args_parser = argparse.ArgumentParser(description=(
      u'Extract the catalog from the ESE database file.'))

  args_parser.add_argument(
      u'source', nargs=u'?', action=u'store', metavar=u'/mnt/c/',
      default=None, help=(u'path of the ESE database file.'))

  args_parser.add_argument(
      u'--db', u'--database', dest=u'database', action=u'store',
      metavar=u'./winevt-db/', default=None, help=(
          u'directory to write the sqlite3 databases to.'))

  args_parser.add_argument(
      u'--type', dest=u'type', action=u'store', metavar=u'search',
      default=None, help=(
          u'string that identifies the ESE database type.'))

  args_parser.add_argument(
      u'--version', dest=u'version', action=u'store', metavar=u'xp',
      default=None, help=(
          u'string that identifies the ESE database version.'))

  options = args_parser.parse_args()

  if not options.source:
    print(u'Source value is missing.')
    print(u'')
    args_parser.print_help()
    print(u'')
    return False

  if not os.path.exists(options.source):
    print(u'No such source: {0:s}.'.format(options.source))
    print(u'')
    return False

  logging.basicConfig(
      level=logging.INFO, format=u'[%(levelname)s] %(message)s')

  if not options.type or not options.version:
    print(u'Missing type or version.')
    print(u'')
    return False

  if options.database:
    if not os.path.exists(options.database):
      os.mkdir(options.database)

    if not os.path.isdir(options.database):
      print(u'{0:s} must be a directory'.format(options.database))
      print(u'')
      return False

    output_writer = Sqlite3OutputWriter(options.database)
  else:
    output_writer = StdoutWriter()

  if not output_writer.Open():
    print(u'Unable to open output writer.')
    print(u'')
    return False

  extractor = EseDbCatalogExtractor()

  # TODO: read table and index overlays from file.
  # overlays = {}

  extractor.ExtractCatalog(options.source, output_writer)
  output_writer.Close()

  return True


if __name__ == u'__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
