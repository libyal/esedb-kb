#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the ESE database catalog extractor."""

import unittest

from esedbrc import catalog_extractor

from tests import test_lib


class TestOutputWriter(object):
  """Test output writer."""

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

  def WriteDatabaseDefinition(self, database_definition):  # pylint: disable=unused-argument
    """Writes the database definition.

    Args:
      database_definition (EseDatabaseDefinition): database definition.
    """
    return

  def WriteTableDefinitions(self, table_definitions):  # pylint: disable=unused-argument
    """Writes the table definitions.

    Args:
      table_definitions (list[EseTableDefinition]): table definitions.
    """
    return


class EseDbCatalogExtractorTest(test_lib.BaseTestCase):
  """Tests for the ESE database catalog extractor."""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests the __init__ function."""
    test_extractor = catalog_extractor.EseDbCatalogExtractor()
    self.assertIsNotNone(test_extractor)

  def testDetermineDatabaseType(self):
    """Tests the _DetermineDatabaseType function."""
    test_extractor = catalog_extractor.EseDbCatalogExtractor()

    database_type = test_extractor._DetermineDatabaseType([
        'SystemIndex_0A', 'SystemIndex_Gthr'])
    self.assertEqual(database_type, 'search')

  def testExtractCatalog(self):
    """Tests the ExtractCatalog function."""
    test_file_path = self._GetTestFilePath(['WebCacheV01.dat'])
    self._SkipIfPathNotExists(test_file_path)

    test_extractor = catalog_extractor.EseDbCatalogExtractor()
    test_output_writer = TestOutputWriter()
    test_extractor.ExtractCatalog(test_file_path, test_output_writer)


if __name__ == '__main__':
  unittest.main()
