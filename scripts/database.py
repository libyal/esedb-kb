# -*- coding: utf-8 -*-
"""Classes to read from and write to SQLite databases."""

import re

import sqlite3


class Sqlite3DatabaseFile(object):
  """Class that defines a sqlite3 database file."""

  _HAS_TABLE_QUERY = (
      u'SELECT name FROM sqlite_master '
      u'WHERE type = "table" AND name = "{0:s}"')

  def __init__(self):
    """Initializes the database file object."""
    super(Sqlite3DatabaseFile, self).__init__()
    self._connection = None
    self._cursor = None
    self.filename = None
    self.read_only = None

  def Close(self):
    """Closes the database file.

    Raises:
      RuntimeError: if the database is not opened.
    """
    if not self._connection:
      raise RuntimeError(u'Cannot close database not opened.')

    # We need to run commit or not all data is stored in the database.
    self._connection.commit()
    self._connection.close()

    self._connection = None
    self._cursor = None
    self.filename = None
    self.read_only = None

  def CreateTable(self, table_name, column_definitions):
    """Creates a table.

    Args:
      table_name: the table name.
      column_definitions: list of strings containing column definitions.

    Raises:
      RuntimeError: if the database is not opened or
                    if the database is in read-only mode.
    """
    if not self._connection:
      raise RuntimeError(u'Cannot create table database not opened.')

    if self.read_only:
      raise RuntimeError(u'Cannot create table database in read-only mode.')

    sql_query = u'CREATE TABLE {0:s} ( {1:s} )'.format(
        table_name, u', '.join(column_definitions))

    self._cursor.execute(sql_query)

  def GetValues(self, table_names, column_names, condition):
    """Retrieves values from a table.

    Args:
      table_names: list of table names.
      column_names: list of column names.
      condition: string containing the condition.

    Yields:
      A row object (instance of sqlite3.row).

    Raises:
      RuntimeError: if the database is not opened.
    """
    if not self._connection:
      raise RuntimeError(u'Cannot retrieve values database not opened.')

    if condition:
      condition = u' WHERE {0:s}'.format(condition)

    sql_query = u'SELECT {1:s} FROM {0:s}{2:s}'.format(
        u', '.join(table_names), u', '.join(column_names), condition)

    self._cursor.execute(sql_query)

    for row in self._cursor:
      values = {}
      for column_index in range(0, len(column_names)):
        column_name = column_names[column_index]
        values[column_name] = row[column_index]
      yield values

  def HasTable(self, table_name):
    """Determines if a specific table exists.

    Args:
      table_name: the table name.

    Returns:
      True if the table exists, false otheriwse.

    Raises:
      RuntimeError: if the database is not opened.
    """
    if not self._connection:
      raise RuntimeError(
          u'Cannot determine if table exists database not opened.')

    sql_query = self._HAS_TABLE_QUERY.format(table_name)

    self._cursor.execute(sql_query)
    if self._cursor.fetchone():
      has_table = True
    else:
      has_table = False
    return has_table

  def InsertValues(self, table_name, column_names, values):
    """Inserts values into a table.

    Args:
      table_name: the table name.
      column_names: list of column names.
      values: list of values formatted as a string.

    Raises:
      RuntimeError: if the database is not opened or
                    if the database is in read-only mode or
                    if an unsupported value type is encountered.
    """
    if not self._connection:
      raise RuntimeError(u'Cannot insert values database not opened.')

    if self.read_only:
      raise RuntimeError(u'Cannot insert values database in read-only mode.')

    if not values:
      return

    sql_values = []
    for value in values:
      if isinstance(value, basestring):
        # In sqlite3 the double quote is escaped with a second double quote.
        value = u'"{0:s}"'.format(re.sub('"', '""', value))
      elif isinstance(value, (int, long)):
        value = u'{0:d}'.format(value)
      elif isinstance(value, float):
        value = u'{0:f}'.format(value)
      elif value is None:
        value = u'NULL'
      else:
        raise RuntimeError(u'Unsupported value type: {0:s}.'.format(
            type(value)))
      sql_values.append(value)

    sql_query = u'INSERT INTO {0:s} ( {1:s} ) VALUES ( {2:s} )'.format(
        table_name, u', '.join(column_names), u', '.join(sql_values))

    self._cursor.execute(sql_query)

  def Open(self, filename, read_only=False):
    """Opens the database file.

    Args:
      filename: the filename of the database.
      read_only: optional boolean value to indicate the database should be
                 opened in read-only mode. The default is false. Since sqlite3
                 does not support a real read-only mode we fake it by only
                 permitting SELECT queries.

    Returns:
      A boolean containing True if successful or False if not.

    Raises:
      RuntimeError: if the database is already opened.
    """
    if self._connection:
      raise RuntimeError(u'Cannot open database already opened.')

    self.filename = filename
    self.read_only = read_only

    self._connection = sqlite3.connect(filename)
    if not self._connection:
      return False

    self._cursor = self._connection.cursor()
    if not self._cursor:
      return False

    return True


class Sqlite3DatabaseReader(object):
  """Class to represent a sqlite3 database reader."""

  def __init__(self):
    """Initializes the database reader object."""
    super(Sqlite3DatabaseReader, self).__init__()
    self._database_file = Sqlite3DatabaseFile()

  def Close(self):
    """Closes the database reader object."""
    self._database_file.Close()

  def Open(self, filename):
    """Opens the database reader object.

    Args:
      filename: the filename of the database.

    Returns:
      A boolean containing True if successful or False if not.
    """
    return self._database_file.Open(filename, read_only=True)


class Sqlite3DatabaseWriter(object):
  """Class to represent a sqlite3 database writer."""

  def __init__(self):
    """Initializes the database writer object."""
    super(Sqlite3DatabaseWriter, self).__init__()
    self._database_file = Sqlite3DatabaseFile()

  def Close(self):
    """Closes the database writer object."""
    self._database_file.Close()

  def Open(self, filename):
    """Opens the database writer object.

    Args:
      filename: the filename of the database.

    Returns:
      A boolean containing True if successful or False if not.
    """
    self._database_file.Open(filename)


class EseDbCatalogSqlite3DatabaseWriter(Sqlite3DatabaseWriter):
  """Class to represent an ESE database catolog sqlite3 writer."""

  def _GetDatabaseDefinitionKey(self, ese_database_definition):
    """Retrieves the key of a database definition.

    Args:
      ese_database_definition: the database definition (instance of
                               EseDatabaseDefinition).

    Returns:
      An integer containing the database definition key
      or None if no such value.

    Raises:
      RuntimeError: if more than one value is found in the database.
    """
    table_names = [u'database_definitions']
    column_names = [u'database_definition_key']
    condition = u'type = "{0:s}" AND version = "{1:s}"'.format(
        ese_database_definition.type, ese_database_definition.version)
    values_list = list(self._database_file.GetValues(
        table_names, column_names, condition))

    number_of_values = len(values_list)
    if number_of_values == 0:
      return

    if number_of_values == 1:
      values = values_list[0]
      return values[u'database_definition_key']

    raise RuntimeError(u'More than one value found in database.')

  def GetTableDefinitionKey(self, ese_table_definition):
    """Retrieves the key of a database definition.

    Args:
      ese_table_definition: the database definition (instance of
                            EseTableDefinition).

    Returns:
      An integer containing the database definition key
      or None if no such value.

    Raises:
      RuntimeError: if more than one value is found in the database.
    """
    table_names = [u'table_definitions']
    column_names = [u'table_definition_key']
    condition = u'name = "{0:s}"'.format(ese_table_definition.name)
    values_list = list(self._database_file.GetValues(
        table_names, column_names, condition))

    number_of_values = len(values_list)
    if number_of_values == 0:
      return

    if number_of_values == 1:
      values = values_list[0]
      return values[u'table_definition_key']

    raise RuntimeError(u'More than one value found in database.')

  def WriteColumnDefinition(self, table_definition_key, ese_column_definition):
    """Writes the column definition.

    Args:
      table_definition_key: the table definition key.
      ese_column_definition: the column definition (instance of
                             EseColumnDefinition).
    """
    table_name = u'column_definitions'
    column_names = [u'identifier', u'name', u'type', u'table_definition_key']

    has_table = self._database_file.HasTable(table_name)
    if not has_table:
      column_definitions = [
          u'column_definition_key INTEGER PRIMARY KEY AUTOINCREMENT',
          u'identifier TEXT', u'name TEXT', u'type TEXT',
          u'table_definition_key INTEGER']
      self._database_file.CreateTable(table_name, column_definitions)
      insert_values = True

    else:
      condition = u'name = "{0:s}" AND table_definition_key = {1:d}'.format(
          ese_column_definition.name, table_definition_key)
      values_list = list(self._database_file.GetValues(
          [table_name], column_names, condition))

      number_of_values = len(values_list)
      if number_of_values == 0:
        insert_values = True
      else:
        # TODO: check if more than 1 result.
        insert_values = False

    if insert_values:
      values = [
          ese_column_definition.identifier, ese_column_definition.name,
          ese_column_definition.type, table_definition_key]
      self._database_file.InsertValues(table_name, column_names, values)

  def WriteDatabaseDefinition(self, ese_database_definition):
    """Writes the database definition.

    Args:
      ese_database_definition: the database definition (instance of
                               EseDatabaseDefinition).
    """
    table_name = u'database_definitions'
    column_names = [u'type', u'version']

    has_table = self._database_file.HasTable(table_name)
    if not has_table:
      column_definitions = [
          u'database_definition_key INTEGER PRIMARY KEY AUTOINCREMENT',
          u'type TEXT', u'version TEXT']
      self._database_file.CreateTable(table_name, column_definitions)
      insert_values = True

    else:
      condition = u'type = "{0:s}" AND version = "{1:s}"'.format(
          ese_database_definition.type, ese_database_definition.version)
      values_list = list(self._database_file.GetValues(
          [table_name], column_names, condition))

      number_of_values = len(values_list)
      if number_of_values == 0:
        insert_values = True
      else:
        # TODO: check if more than 1 result.
        insert_values = False

    if insert_values:
      values = [ese_database_definition.type, ese_database_definition.version]
      self._database_file.InsertValues(table_name, column_names, values)

  def WriteTableDefinition(self, ese_table_definition):
    """Writes the table definition.

    Args:
      ese_table_definition: the table definition (instance of
                            EseTableDefinition).
    """
    table_name = u'table_definitions'
    column_names = [u'name']

    has_table = self._database_file.HasTable(table_name)
    if not has_table:
      column_definitions = [
          u'table_definition_key INTEGER PRIMARY KEY AUTOINCREMENT',
          u'name TEXT']
      self._database_file.CreateTable(table_name, column_definitions)
      insert_values = True

    else:
      condition = u'name = "{0:s}"'.format(ese_table_definition.name)
      values_list = list(self._database_file.GetValues(
          [table_name], column_names, condition))

      number_of_values = len(values_list)
      if number_of_values == 0:
        insert_values = True
      else:
        # TODO: check if more than 1 result.
        insert_values = False

    if insert_values:
      values = [ese_table_definition.name]
      self._database_file.InsertValues(table_name, column_names, values)
