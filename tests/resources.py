#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the ESE database resources."""

import unittest

from esedbrc import resources

from tests import test_lib


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


class EseDatabaseDefinitionTest(test_lib.BaseTestCase):
  """Tests for the ESE database definition."""

  def testInitialize(self):
    """Tests the __init__ function."""
    database_definition = resources.EseDatabaseDefinition('type', 'version')
    self.assertIsNotNone(database_definition)


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


class ColumnOverlayTest(test_lib.BaseTestCase):
  """Tests for the column overlay."""

  def testInitialize(self):
    """Tests the __init__ function."""
    column_overlay = resources.ColumnOverlay('identifier', 'name', 'type')
    self.assertIsNotNone(column_overlay)

  def testComparable(self):
    """Tests the comparable property."""
    column_overlay = resources.ColumnOverlay('identifier', 'name', 'type')

    expected_comparable = 'identifier: identifier, name: name, type: type'
    self.assertEqual(column_overlay.comparable, expected_comparable)


class TableOverlayTest(test_lib.BaseTestCase):
  """Tests for the table overlay."""

  def testInitialize(self):
    """Tests the __init__ function."""
    table_overlay = resources.TableOverlay('name')
    self.assertIsNotNone(table_overlay)

  def testAddColumnOverlay(self):
    """Tests the AddColumnOverlay function."""
    table_overlay = resources.TableOverlay('name')
    column_overlay = resources.ColumnOverlay('identifier', 'name', 'type')

    table_overlay.AddColumnOverlay(column_overlay)

    with self.assertRaises(KeyError):
      table_overlay.AddColumnOverlay(column_overlay)


if __name__ == '__main__':
  unittest.main()
