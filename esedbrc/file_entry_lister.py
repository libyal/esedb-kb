# -*- coding: utf-8 -*-
"""Volume scanner for ESE databases."""

import os

from dfimagetools import file_entry_lister as dfimagetools_file_entry_lister

from dtfabric import errors as dtfabric_errors
from dtfabric.runtime import fabric as dtfabric_fabric


class ESEDatabaseFileEntryLister(
    dfimagetools_file_entry_lister.FileEntryLister):
  """ESE database file entry lister."""

  # Preserve the absolute path value of __file__ in case it is changed
  # at run-time.
  _DEFINITION_FILES_PATH = os.path.dirname(__file__)

  def __init__(self, mediator=None):
    """Initializes an ESE database file entry lister.

    Args:
      mediator (Optional[dfvfs.VolumeScannerMediator]): a volume scanner
          mediator.
    """
    super(ESEDatabaseFileEntryLister, self).__init__(mediator=mediator)
    self._data_type_fabric = self._ReadDataTypeFabricDefinitionFile(
        'format.yaml')
    self._data_type_maps = {}

  def _DetermineDataFormat(self, file_object):
    """Determines the data format.

    Args:
      file_object (file): file-like object.

    Returns:
      str: format version or None if not an ESE database.
    """
    format_data_type_map = self._GetDataTypeMap('esedb')

    layout = getattr(format_data_type_map, 'layout', None)
    if not layout:
      return None

    layout_element_definition = layout[0]
    if layout_element_definition.offset is None:
      return None

    data_type_map = self._GetDataTypeMap(
        layout_element_definition.data_type)

    structure_values = self._ReadStructureFromFileObject(
        file_object, layout_element_definition.offset, data_type_map)
    if not structure_values:
      return None

    return '0x{format_version:x}'.format(**structure_values.__dict__)

  def _GetDataTypeMap(self, name):
    """Retrieves a data type map defined by the definition file.

    The data type maps are cached for reuse.

    Args:
      name (str): name of the data type as defined by the definition file.

    Returns:
      dtfabric.DataTypeMap: data type map which contains a data type definition,
          such as a structure, that can be mapped onto binary data.
    """
    data_type_map = self._data_type_maps.get(name, None)
    if not data_type_map:
      data_type_map = self._data_type_fabric.CreateDataTypeMap(name)
      self._data_type_maps[name] = data_type_map

    return data_type_map

  def _ReadDataTypeFabricDefinitionFile(self, filename):
    """Reads a dtFabric definition file.

    Args:
      filename (str): name of the dtFabric definition file.

    Returns:
      dtfabric.DataTypeFabric: data type fabric which contains the data format
          data type maps of the data type definition, such as a structure, that
          can be mapped onto binary data or None if no filename is provided.
    """
    if not filename:
      return None

    path = os.path.join(self._DEFINITION_FILES_PATH, filename)
    with open(path, 'rb') as file_object:
      definition = file_object.read()

    return dtfabric_fabric.DataTypeFabric(yaml_definition=definition)

  def _ReadStructureFromFileObject(
      self, file_object, file_offset, data_type_map):
    """Reads a structure from a file-like object.

    This method currently only supports fixed-size structures.

    Args:
      file_object (file): a file-like object to parse.
      file_offset (int): offset of the structure data relative to the start
          of the file-like object.
      data_type_map (dtfabric.DataTypeMap): data type map of the structure.

    Returns:
      object: structure values object or None if the structure cannot be read.
    """
    structure_values = None

    data_size = data_type_map.GetSizeHint()
    if data_size:
      file_object.seek(file_offset, os.SEEK_SET)
      try:
        data = file_object.read(data_size)
        structure_values = data_type_map.MapByteStream(data)
      except (dtfabric_errors.ByteStreamTooSmallError,
              dtfabric_errors.MappingError):
        pass

    return structure_values

  def ListDatabaseFileEntries(self, base_path_specs):
    """Lists file entries that contain an ESE database.

    Args:
      base_path_specs (list[dfvfs.PathSpec]): source path specifications.

    Yields:
      tuple[dfvfs.FileEntry, list[str]]: file entry and path segments.
    """
    for file_entry, path_segments in self.ListFileEntries(base_path_specs):
      if file_entry.size == 0:
        continue

      file_object = file_entry.GetFileObject()
      if not file_object:
        continue

      data_format = self._DetermineDataFormat(file_object)
      if not data_format:
        continue

      yield file_entry, path_segments
