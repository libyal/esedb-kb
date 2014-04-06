#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Script to print the ESE database catalog.
#
# Copyright (c) 2014, Joachim Metz <joachim.metz@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import logging
import os
import sys

import pyesedb


if pyesedb.get_version() < '20140406':
  raise ImportWarning('catalog.py requires pyesedb 20140406 or later.')


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
    return 'identifier: {0:s}, name: {1:s}, type: {2:s}'.format(
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
      raise KeyError('Column overlay: {0:s} already set.'.format(
          column_overlay.comparable))

    self._column_overlays[column_overlay.comparable] = column_overlay


class StdoutWriter(object):
  """Class that defines a stdout output writer."""

  def Open(self):
    """Opens the output writer object.

    Returns:
      A boolean containing True if successful or False if not.
    """
    return True

  def Close(self):
    """Closes the output writer object."""
    pass

  def WriteColumn(self, column_identifier, column_name, column_type):
    """Writes the column to stdout.

    Args:
      column_identifier: the column identifier.
      column_name: the column name.
      column_type: the column type.
    """
    print '|| {0:d} || {{{{{{ {1:s} }}}}}} || {2:s} ||'.format(
        column_identifier, column_name, column_type)

  def WritePageHeader(self, page_summary):
    """Writes the page header to stdout.

    Args:
      page_summary: the page summary.
    """
    print '#summary {0:s}'.format(page_summary)
    print ''
    print '<wiki:toc max_depth="3" />'
    print ''

  def WriteTableFooter(self):
    """Writes the table footer to stdout."""
    print ''

  def WriteTableHeader(self, table_name, template_table_name):
    """Writes the table header to stdout.

    Args:
      table_name: the table name.
      template_table_name: the template table name.
    """
    print '== {{{{{{ {0:s} }}}}}} =='.format(table_name)

    if template_table_name:
      print 'Template table: {0:s}'.format(template_table_name)

    print '|| *Column indentifier* || *Column name* || *Column type* ||'


def Main():
  """The main program function.

  Returns:
    A boolean containing True if successful or False if not.
  """
  args_parser = argparse.ArgumentParser(description=(
      'Extract the catalog from the ESE database file.'))

  args_parser.add_argument(
      'source', nargs='?', action='store', metavar='/mnt/c/',
      default=None, help=('path of the ESE database file.'))

  options = args_parser.parse_args()

  if not options.source:
    print u'Source value is missing.'
    print u''
    args_parser.print_help()
    print u''
    return False

  logging.basicConfig(
      level=logging.INFO, format=u'[%(levelname)s] %(message)s')

  output_writer = StdoutWriter()

  ESEDB_COLUMN_TYPE_DESCRIPTIONS = {
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

  ESEDB_COLUMN_TYPE_IDENTIFIERS = {
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

  # TODO: read table and index overlays from file.
  # overlays = {}

  esedb_file = pyesedb.file()

  esedb_file.open(options.source)

  # TODO: determine database type and set page_summary?

  page_summary = 'Test'

  output_writer.WritePageHeader(page_summary)

  for esedb_table in esedb_file.tables:
    output_writer.WriteTableHeader(esedb_table.name, esedb_table.template_name)

    for esedb_column in esedb_table.columns:
      output_writer.WriteColumn(
          esedb_column.identifier, esedb_column.name,
          ESEDB_COLUMN_TYPE_DESCRIPTIONS.get(esedb_column.type, 'UNKNOWN'))

    output_writer.WriteTableFooter()

  esedb_file.close()
  output_writer.Close()

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
