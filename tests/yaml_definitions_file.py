#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the YAML-based database definitions file."""

import unittest

from esedbrc import yaml_definitions_file

from tests import test_lib


class YAMLDatabaseDefinitionsFileTest(test_lib.BaseTestCase):
  """Tests for the YAML-based database definitions file."""

  # pylint: disable=protected-access

  _TEST_YAML = {
      'artifact_definition': 'MacOSNotesSQLiteDatabaseFile',
      'database_identifier': 'Notes.storedata'}

  def testReadDatabaseDefinition(self):
    """Tests the _ReadDatabaseDefinition function."""
    test_definitions_file = yaml_definitions_file.YAMLDatabaseDefinitionsFile()

    definitions = test_definitions_file._ReadDatabaseDefinition(self._TEST_YAML)

    self.assertIsNotNone(definitions)
    self.assertEqual(
        definitions.artifact_definition, 'MacOSNotesSQLiteDatabaseFile')
    self.assertEqual(definitions.database_identifier, 'Notes.storedata')

    with self.assertRaises(RuntimeError):
      test_definitions_file._ReadDatabaseDefinition({})

    with self.assertRaises(RuntimeError):
      test_definitions_file._ReadDatabaseDefinition({
          'artifact_definition': 'MacOSNotesSQLiteDatabaseFile'})

    with self.assertRaises(RuntimeError):
      test_definitions_file._ReadDatabaseDefinition({
          'database_identifier': 'Notes.storedata'})

    with self.assertRaises(RuntimeError):
      test_definitions_file._ReadDatabaseDefinition({
          'bogus': 'test'})

  def testReadFromFileObject(self):
    """Tests the _ReadFromFileObject function."""
    test_file_path = self._GetTestFilePath(['known_databases.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_definitions_file = yaml_definitions_file.YAMLDatabaseDefinitionsFile()

    with open(test_file_path, 'r', encoding='utf-8') as file_object:
      definitions = list(test_definitions_file._ReadFromFileObject(file_object))

    self.assertEqual(len(definitions), 1)

  def testReadFromFile(self):
    """Tests the ReadFromFile function."""
    test_file_path = self._GetTestFilePath(['known_databases.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    test_definitions_file = yaml_definitions_file.YAMLDatabaseDefinitionsFile()

    definitions = list(test_definitions_file.ReadFromFile(test_file_path))

    self.assertEqual(len(definitions), 1)

    self.assertEqual(
        definitions[0].artifact_definition, 'WindowsCortanaDatabase')


if __name__ == '__main__':
  unittest.main()
