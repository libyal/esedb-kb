#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the ESE database schema extractor."""

import io
import os
import unittest

import artifacts

from esedbrc import resources
from esedbrc import schema_extractor

from tests import test_lib


class EseDbSchemaExtractorTest(test_lib.BaseTestCase):
  """Tests for the ESE database schema extractor."""

  # pylint: disable=protected-access

  _ARTIFACT_DEFINITIONS_PATH = os.path.join(
        os.path.dirname(artifacts.__file__), 'data')
  if not os.path.isdir(_ARTIFACT_DEFINITIONS_PATH):
    _ARTIFACT_DEFINITIONS_PATH = os.path.join(
        '/', 'usr', 'share', 'artifacts')

  def testInitialize(self):
    """Tests the __init__ function."""
    test_extractor = schema_extractor.EseDbSchemaExtractor(
        self._ARTIFACT_DEFINITIONS_PATH)
    self.assertIsNotNone(test_extractor)

  def testCheckSignature(self):
    """Tests the _CheckSignature function."""
    test_extractor = schema_extractor.EseDbSchemaExtractor(
        self._ARTIFACT_DEFINITIONS_PATH)

    file_object = io.BytesIO(b'\x00\x00\x00\x00\xef\xcd\xab\x89')
    result = test_extractor._CheckSignature(file_object)
    self.assertTrue(result)

    file_object = io.BytesIO(b'\x00\x00\x00\x00\xff\xff\xff\xff')
    result = test_extractor._CheckSignature(file_object)
    self.assertFalse(result)

  def testFormatSchemaAsYAML(self):
    """Tests the _FormatSchemaAsYAML function."""
    test_extractor = schema_extractor.EseDbSchemaExtractor(
        self._ARTIFACT_DEFINITIONS_PATH)

    table_definition = resources.EseTableDefinition('MyTable', None)

    table_definition.AddColumnDefinition(1, 'MyColumn', 4)

    yaml_data = test_extractor._FormatSchemaAsYAML([table_definition])

    expected_yaml_data = '\n'.join([
        '# esedb-kb database schema.',
        '---',
        'table: MyTable',
        'columns:',
        '- name: MyColumn',
        '  value_type: 4',
        ''])

    self.assertEqual(yaml_data, expected_yaml_data)

  # TODO: add tests for _GetDatabaseIdentifier

  def testGetDatabaseSchema(self):
    """Tests the _GetDatabaseSchema function."""
    test_extractor = schema_extractor.EseDbSchemaExtractor(
        self._ARTIFACT_DEFINITIONS_PATH)

    database_path = self._GetTestFilePath(['WebCacheV01.dat'])
    schema = test_extractor._GetDatabaseSchema(database_path)

    self.assertIsNotNone(schema)
    self.assertEqual(len(schema), 10)

    table_definition = schema[0]
    self.assertIsNotNone(table_definition)
    self.assertEqual(len(table_definition.aliases), 1)
    self.assertEqual(len(table_definition.column_definitions), 27)
    self.assertEqual(table_definition.name, 'MSysObjects')
    self.assertIsNone(table_definition.template_table_name)

  def testGetDatabaseSchemaFromFileObject(self):
    """Tests the _GetDatabaseSchemaFromFileObject function."""
    test_extractor = schema_extractor.EseDbSchemaExtractor(
        self._ARTIFACT_DEFINITIONS_PATH)

    database_path = self._GetTestFilePath(['WebCacheV01.dat'])
    with open(database_path, 'rb') as file_object:
      schema = test_extractor._GetDatabaseSchemaFromFileObject(file_object)

    self.assertIsNotNone(schema)
    self.assertEqual(len(schema), 10)

    table_definition = schema[0]
    self.assertIsNotNone(table_definition)
    self.assertEqual(len(table_definition.aliases), 1)
    self.assertEqual(len(table_definition.column_definitions), 27)
    self.assertEqual(table_definition.name, 'MSysObjects')
    self.assertIsNone(table_definition.template_table_name)

  # TODO: add tests for GetDisplayPath
  # TODO: add tests for ExtractSchemas
  # TODO: add tests for FormatSchema


if __name__ == '__main__':
  unittest.main()
