# -*- coding: utf-8 -*-
"""ESE database resources."""

import difflib


class DatabaseDefinition(object):
  """Database definition.

  Attributes:
    artifact_definition (str): name of the corresponding Digital Forensics
        Artifact definition.
    database_identifier (str): identifier of the database type.
  """

  def __init__(self):
    """Initializes a database definition."""
    super(DatabaseDefinition, self).__init__()
    self.artifact_definition = None
    self.database_identifier = None


class EseColumnDefinition(object):
  """ESE database column definition.

  Attributes:
    identifier (str): column identifier.
    name (str): column name.
    type (str): column type.
  """

  def __init__(self, column_identifier, column_name, column_type):
    """Initializes an ESE database column definition.

    Args:
      column_identifier (int): column identifier.
      column_name (str): column name.
      column_type (int): column type.
    """
    super(EseColumnDefinition, self).__init__()
    self.identifier = column_identifier
    self.name = column_name
    self.type = column_type

  def CopyToDict(self):
    """Copies the ESE database column definition to a dictionary.

    Returns:
      dict[str, object]: dictionary containing the ESE database column
          definition.
    """
    return {
        'identifier': self.identifier,
        'name': self.name,
        'type': self.type}


class EseTableDefinition(object):
  """ESE database table definition.

  Attributes:
    aliases (list[str]): table name aliases.
    column_definitions (list[EseColumnDefinition]): column definitions.
    name (str): table name.
    template_table_name (str): template table name.
  """

  def __init__(self, table_name, template_table_name):
    """Initializes an ESE database table definition.

    Args:
      table_name (str): table name.
      template_table_name (str): template table name.
    """
    super(EseTableDefinition, self).__init__()
    self._common_name = None
    self.aliases = []
    self.column_definitions = []
    self.name = table_name
    self.template_table_name = template_table_name

  def AddColumnDefinition(self, column_identifier, column_name, column_type):
    """Adds a column.

    Args:
      column_identifier (int): column identifier.
      column_name (str): column name.
      column_type (int): column type.
    """
    ese_column_definition = EseColumnDefinition(
        column_identifier, column_name, column_type)
    self.column_definitions.append(ese_column_definition)

  def GetCommonName(self):
    """Determines the common name.

    Returns:
      str: common name or None if no common could be determined.
    """
    if not self._common_name:
      self._common_name = self.name
      for alias in self.aliases:
        sequence_matcher = difflib.SequenceMatcher(
            isjunk=None, a=self._common_name, b=alias)

        match = sequence_matcher.find_longest_match(
            0, len(self._common_name), 0, len(alias))

        if match.size == 0:
          return None

        self._common_name = self._common_name[match.a: match.a + match.size]

      if self.name.index(self._common_name) == 0:
        # If the table name ends with a number replace it with a #
        if self.name[len(self._common_name):].isdigit():
          self._common_name = f'{self._common_name:s}#'

    return self._common_name
