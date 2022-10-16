# -*- coding: utf-8 -*-
"""Classes to read from and write to SQLite databases."""

import re

import sqlite3


class Sqlite3DatabaseFile(object):
  """SQLite3 database file."""

  _HAS_TABLE_QUERY = (
      'SELECT name FROM sqlite_master '
      'WHERE type = "table" AND name = "{0:s}"')

  def __init__(self):
    """Initializes a database file."""
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
      raise RuntimeError('Cannot close database not opened.')

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
      table_name (str): table name.
      column_definitions (list[str]): column definitions.

    Raises:
      RuntimeError: if the database is not opened or
          if the database is in read-only mode.
    """
    if not self._connection:
      raise RuntimeError('Cannot create table database not opened.')

    if self.read_only:
      raise RuntimeError('Cannot create table database in read-only mode.')

    column_definitions = ', '.join(column_definitions)
    self._cursor.execute(
        f'CREATE TABLE {table_name:s} ( {column_definitions:s} )')

  def GetValues(self, table_names, column_names, condition):
    """Retrieves values from a table.

    Args:
      table_names (list[str]): table names.
      column_names (list[str]): column names.
      condition (str): condition.

    Yields:
      sqlite3.row: a row.

    Raises:
      RuntimeError: if the database is not opened.
    """
    if not self._connection:
      raise RuntimeError('Cannot retrieve values database not opened.')

    table_names = ', '.join(table_names)
    column_names_string = ', '.join(column_names)

    sql_query = f'SELECT {column_names_string:s} FROM {table_names:s}'
    if condition:
      sql_query = ''.join([sql_query, f' WHERE {condition:s}'])

    self._cursor.execute(sql_query)

    for row in self._cursor:
      values = {}
      for column_index, column_name in enumerate(column_names):
        values[column_name] = row[column_index]
      yield values

  def HasTable(self, table_name):
    """Determines if a specific table exists.

    Args:
      table_name (str): table name.

    Returns:
      bool: True if the table exists, False otheriwse.

    Raises:
      RuntimeError: if the database is not opened.
    """
    if not self._connection:
      raise RuntimeError(
          'Cannot determine if table exists database not opened.')

    sql_query = self._HAS_TABLE_QUERY.format(table_name)

    self._cursor.execute(sql_query)

    return bool(self._cursor.fetchone())

  def InsertValues(self, table_name, column_names, values):
    """Inserts values into a table.

    Args:
      table_name (str): table name.
      column_names (list[str]): column names.
      values (list[str]): values formatted as a string.

    Raises:
      RuntimeError: if the database is not opened or
          if the database is in read-only mode or
          if an unsupported value type is encountered.
    """
    if not self._connection:
      raise RuntimeError('Cannot insert values database not opened.')

    if self.read_only:
      raise RuntimeError('Cannot insert values database in read-only mode.')

    if not values:
      return

    sql_values = []
    for value in values:
      if isinstance(value, str):
        # In sqlite3 the double quote is escaped with a second double quote.
        value = re.sub('"', '""', value)
        value = f'"{value:s}"'
      elif isinstance(value, int):
        value = f'{value:d}'
      elif isinstance(value, float):
        value = f'{value:f}'
      elif value is None:
        value = 'NULL'
      else:
        value_type = type(value)
        raise RuntimeError(f'Unsupported value type: {value_type!s}.')

      sql_values.append(value)

    column_names = ', '.join(column_names)
    sql_values = ', '.join(sql_values)

    self._cursor.execute(
        f'INSERT INTO {table_name:s} ( {column_names:s} ) '
        f'VALUES ( {sql_values:s} )')

  def Open(self, filename, read_only=False):
    """Opens the database file.

    Args:
      filename (str): filename of the database.
      read_only (Optional[bool]): True if the database should be opened in
          read-only mode. Since sqlite3 does not support a real read-only
          mode we fake it by only permitting SELECT queries.

    Returns:
      bool: True if successful or False if not.

    Raises:
      RuntimeError: if the database is already opened.
    """
    if self._connection:
      raise RuntimeError('Cannot open database already opened.')

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
  """SQLite3 database reader."""

  def __init__(self):
    """Initializes a database reader."""
    super(Sqlite3DatabaseReader, self).__init__()
    self._database_file = Sqlite3DatabaseFile()

  def Close(self):
    """Closes the database reader object."""
    self._database_file.Close()

  def Open(self, filename):
    """Opens the database reader object.

    Args:
      filename (str): filename of the database.

    Returns:
      bool: True if successful or False if not.
    """
    return self._database_file.Open(filename, read_only=True)


class Sqlite3DatabaseWriter(object):
  """SQLite3 database writer."""

  def __init__(self):
    """Initializes a database writer."""
    super(Sqlite3DatabaseWriter, self).__init__()
    self._database_file = Sqlite3DatabaseFile()

  def Close(self):
    """Closes the database writer object."""
    self._database_file.Close()

  def Open(self, filename):
    """Opens the database writer object.

    Args:
      filename (str): filename of the database.

    Returns:
      bool: True if successful or False if not.
    """
    self._database_file.Open(filename)
    return True


class EseDbCatalogSqlite3DatabaseWriter(Sqlite3DatabaseWriter):
  """ESE database catolog SQLite3 writer."""

  def _GetDatabaseDefinitionKey(self, ese_database_definition):
    """Retrieves the key of a database definition.

    Args:
      ese_database_definition (EseDatabaseDefinition): database definition.

    Returns:
      int: database definition key or None if no such value.

    Raises:
      RuntimeError: if more than one value is found in the database.
    """
    table_names = ['database_definitions']
    column_names = ['database_definition_key']
    condition = (
        f'type = "{ese_database_definition.type:s}" AND '
        f'version = "{ese_database_definition.version:s}"')
    values_list = list(self._database_file.GetValues(
        table_names, column_names, condition))

    number_of_values = len(values_list)
    if number_of_values == 0:
      return None

    if number_of_values == 1:
      values = values_list[0]
      return values['database_definition_key']

    raise RuntimeError('More than one value found in database.')

  def GetTableDefinitionKey(self, ese_table_definition):
    """Retrieves the key of a database definition.

    Args:
      ese_table_definition (EseTableDefinition): database definition.

    Returns:
      int: database definition key or None if no such value.

    Raises:
      RuntimeError: if more than one value is found in the database.
    """
    table_names = ['table_definitions']
    column_names = ['table_definition_key']
    condition = f'name = "{ese_table_definition.name:s}"'
    values_list = list(self._database_file.GetValues(
        table_names, column_names, condition))

    number_of_values = len(values_list)
    if number_of_values == 0:
      return None

    if number_of_values == 1:
      values = values_list[0]
      return values['table_definition_key']

    raise RuntimeError('More than one value found in database.')

  def WriteColumnDefinition(self, table_definition_key, ese_column_definition):
    """Writes the column definition.

    Args:
      table_definition_key (int): table definition key.
      ese_column_definition (EseColumnDefinition): column definition.
    """
    table_name = 'column_definitions'
    column_names = ['identifier', 'name', 'type', 'table_definition_key']

    has_table = self._database_file.HasTable(table_name)
    if not has_table:
      column_definitions = [
          'column_definition_key INTEGER PRIMARY KEY AUTOINCREMENT',
          'identifier TEXT', 'name TEXT', 'type TEXT',
          'table_definition_key INTEGER']
      self._database_file.CreateTable(table_name, column_definitions)
      insert_values = True

    else:
      condition = (
          f'name = "{ese_column_definition.name:s}" AND '
          f'table_definition_key = {table_definition_key:d}')
      values_list = list(self._database_file.GetValues(
          [table_name], column_names, condition))

      number_of_values = len(values_list)
      # TODO: check if more than 1 result.
      insert_values = number_of_values == 0

    if insert_values:
      values = [
          ese_column_definition.identifier, ese_column_definition.name,
          ese_column_definition.type, table_definition_key]
      self._database_file.InsertValues(table_name, column_names, values)

  def WriteDatabaseDefinition(self, ese_database_definition):
    """Writes the database definition.

    Args:
      ese_database_definition (EseDatabaseDefinition): database definition.
    """
    table_name = 'database_definitions'
    column_names = ['type', 'version']

    has_table = self._database_file.HasTable(table_name)
    if not has_table:
      column_definitions = [
          'database_definition_key INTEGER PRIMARY KEY AUTOINCREMENT',
          'type TEXT', 'version TEXT']
      self._database_file.CreateTable(table_name, column_definitions)
      insert_values = True

    else:
      condition = (
          f'type = "{ese_database_definition.type:s}" AND '
          f'version = "{ese_database_definition.version:s}"')
      values_list = list(self._database_file.GetValues(
          [table_name], column_names, condition))

      number_of_values = len(values_list)
      # TODO: check if more than 1 result.
      insert_values = number_of_values == 0

    if insert_values:
      values = [ese_database_definition.type, ese_database_definition.version]
      self._database_file.InsertValues(table_name, column_names, values)

  def WriteTableDefinition(self, ese_table_definition):
    """Writes the table definition.

    Args:
      ese_table_definition (EseTableDefinition): table definition.
    """
    table_name = 'table_definitions'
    column_names = ['name']

    has_table = self._database_file.HasTable(table_name)
    if not has_table:
      column_definitions = [
          'table_definition_key INTEGER PRIMARY KEY AUTOINCREMENT',
          'name TEXT']
      self._database_file.CreateTable(table_name, column_definitions)
      insert_values = True

    else:
      condition = f'name = "{ese_table_definition.name:s}"'
      values_list = list(self._database_file.GetValues(
          [table_name], column_names, condition))

      number_of_values = len(values_list)
      # TODO: check if more than 1 result.
      insert_values = number_of_values == 0

    if insert_values:
      values = [ese_table_definition.name]
      self._database_file.InsertValues(table_name, column_names, values)
