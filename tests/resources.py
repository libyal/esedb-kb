#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the ESE database resources."""

import unittest

from esedbrc import resources

from tests import test_lib


class DatabaseDefinitionTest(test_lib.BaseTestCase):
  """Tests for the database definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    database_definition = resources.DatabaseDefinition()
    self.assertIsNotNone(database_definition)


class EseColumnDefinitionTest(test_lib.BaseTestCase):
  """Tests for the ESE database column definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    column_definition = resources.EseColumnDefinition(
        'identifier', 'name', 'type')
    self.assertIsNotNone(column_definition)

  def testCopyToDict(self):
    """Tests the CopyToDict function."""
    column_definition = resources.EseColumnDefinition(
        'identifier', 'name', 'type')

    expected_dict = {
        'identifier': 'identifier',
        'name': 'name',
        'type': 'type'}
    self.assertEqual(column_definition.CopyToDict(), expected_dict)


class EseTableDefinitionTest(test_lib.BaseTestCase):
  """Tests for the ESE table definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    table_definition = resources.EseTableDefinition('name', 'template_name')
    self.assertIsNotNone(table_definition)

  def testAddColumnDefinition(self):
    """Tests the AddColumnDefinition function."""
    table_definition = resources.EseTableDefinition('name', 'template_name')
    table_definition.AddColumnDefinition('identifier', 'name', 'type')


if __name__ == '__main__':
  unittest.main()
