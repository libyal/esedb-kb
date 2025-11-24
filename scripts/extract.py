#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to extract an ESE database catalog."""

import argparse
import logging
import os
import sys

import artifacts

from dfvfs.helpers import command_line as dfvfs_command_line
from dfvfs.helpers import volume_scanner as dfvfs_volume_scanner
from dfvfs.lib import errors as dfvfs_errors

from dfimagetools import helpers

from esedbrc import schema_extractor


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Extract the catalog from the ESE database file.'))

  # TODO: add data group.
  argument_parser.add_argument(
      '--artifact_definitions', '--artifact-definitions',
      dest='artifact_definitions', type=str, metavar='PATH', action='store',
      help=('Path to a directory or file containing the artifact definition '
            '.yaml files.'))

  argument_parser.add_argument(
      '--output', dest='output', action='store', metavar='./sqlite-kb/',
      default=None, help='Directory to write the output to.')

  # TODO: add source group.
  argument_parser.add_argument(
      '--back_end', '--back-end', dest='back_end', action='store',
      metavar='NTFS', default=None, help='preferred dfVFS back-end.')

  argument_parser.add_argument(
      '--partitions', '--partition', dest='partitions', action='store',
      type=str, default=None, help=(
          'Define partitions to be processed. A range of partitions can be '
          'defined as: "3..5". Multiple partitions can be defined as: "1,3,5" '
          '(a list of comma separated values). Ranges and lists can also be '
          'combined as: "1,3..5". The first partition is 1. All partitions '
          'can be specified with: "all".'))

  argument_parser.add_argument(
      '--snapshots', '--snapshot', dest='snapshots', action='store', type=str,
      default=None, help=(
          'Define snapshots to be processed. A range of snapshots can be '
          'defined as: "3..5". Multiple snapshots can be defined as: "1,3,5" '
          '(a list of comma separated values). Ranges and lists can also be '
          'combined as: "1,3..5". The first snapshot is 1. All snapshots can '
          'be specified with: "all".'))

  argument_parser.add_argument(
      '--volumes', '--volume', dest='volumes', action='store', type=str,
      default=None, help=(
          'Define volumes to be processed. A range of volumes can be defined '
          'as: "3..5". Multiple volumes can be defined as: "1,3,5" (a list '
          'of comma separated values). Ranges and lists can also be combined '
          'as: "1,3..5". The first volume is 1. All volumes can be specified '
          'with: "all".'))

  argument_parser.add_argument(
      'source', nargs='?', action='store', metavar='PATH', default=None,
      help='path of a storage media image or ESE database file.')

  options = argument_parser.parse_args()

  if not options.source:
    print('Source value is missing.')
    print('')
    argument_parser.print_help()
    print('')
    return False

  artifact_definitions = options.artifact_definitions
  if not artifact_definitions:
    artifact_definitions = os.path.join(
        os.path.dirname(artifacts.__file__), 'data')
    if not os.path.exists(artifact_definitions):
      artifact_definitions = os.path.join('/', 'usr', 'share', 'artifacts')
    if not os.path.exists(artifact_definitions):
      artifact_definitions = None

  if not artifact_definitions:
    print('Path to artifact definitions is missing.')
    print('')
    argument_parser.print_help()
    print('')
    return False

  if options.output:
    if not os.path.exists(options.output):
      os.mkdir(options.output)

    if not os.path.isdir(options.output):
      print(f'{options.output:s} must be a directory')
      print('')
      return False

  helpers.SetDFVFSBackEnd(options.back_end)

  logging.basicConfig(
      level=logging.INFO, format='[%(levelname)s] %(message)s')

  mediator = dfvfs_command_line.CLIVolumeScannerMediator()

  volume_scanner_options = dfvfs_volume_scanner.VolumeScannerOptions()
  volume_scanner_options.partitions = mediator.ParseVolumeIdentifiersString(
      options.partitions)

  if options.snapshots == 'none':
    volume_scanner_options.snapshots = ['none']
  else:
    volume_scanner_options.snapshots = mediator.ParseVolumeIdentifiersString(
        options.snapshots)

  volume_scanner_options.volumes = mediator.ParseVolumeIdentifiersString(
      options.volumes)

  extractor = schema_extractor.EseDbSchemaExtractor(
      artifact_definitions, mediator=mediator)

  try:
    for database_identifier, database_schema in extractor.ExtractSchemas(
        options.source, options=volume_scanner_options):
      if not database_schema:
        continue

      output_text = extractor.FormatSchema(database_schema, 'yaml')
      if not options.output:
        print(output_text)
      else:
        file_exists = False
        output_file = None
        for number in range(1, 99):
          filename = f'{database_identifier:s}.{number:d}.yaml'
          output_file = os.path.join(options.output, filename)
          if not os.path.exists(output_file):
            break

          with open(output_file, 'r', encoding='utf-8') as existing_file_object:
            existing_output_text = existing_file_object.read()
            if output_text == existing_output_text:
              file_exists = True
              break

        if not file_exists:
          with open(output_file, 'w', encoding='utf-8') as output_file_object:
            output_file_object.write(output_text)

  except dfvfs_errors.ScannerError as exception:
    print(f'[ERROR] {exception!s}', file=sys.stderr)
    print('')
    return False

  except KeyboardInterrupt:
    print('Aborted by user.', file=sys.stderr)
    print('')
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
