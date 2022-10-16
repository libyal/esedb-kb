#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Installation and deployment script."""

import glob
import os
import pkg_resources
import sys

try:
  from setuptools import find_packages, setup
except ImportError:
  from distutils.core import find_packages, setup

try:
  from distutils.command.bdist_msi import bdist_msi
except ImportError:
  bdist_msi = None

try:
  from distutils.command.bdist_rpm import bdist_rpm
except ImportError:
  bdist_rpm = None

version_tuple = (sys.version_info[0], sys.version_info[1])
if version_tuple < (3, 7):
  print(f'Unsupported Python version: {sys.version:s}, version 3.7 or higher '
        f'required.')
  sys.exit(1)

# Change PYTHONPATH to include esedbrc so that we can get the version.
sys.path.insert(0, '.')

import esedbrc  # pylint: disable=wrong-import-position


if not bdist_msi:
  BdistMSICommand = None
else:
  class BdistMSICommand(bdist_msi):
    """Custom handler for the bdist_msi command."""

    # pylint: disable=invalid-name
    def run(self):
      """Builds an MSI."""
      # Command bdist_msi does not support the library version, neither a date
      # as a version but if we suffix it with .1 everything is fine.
      self.distribution.metadata.version += '.1'

      bdist_msi.run(self)


if not bdist_rpm:
  BdistRPMCommand = None
else:
  class BdistRPMCommand(bdist_rpm):
    """Custom handler for the bdist_rpm command."""

    # pylint: disable=invalid-name
    def _make_spec_file(self):
      """Generates the text of an RPM spec file.

      Returns:
        list[str]: lines of the RPM spec file.
      """
      # Note that bdist_rpm can be an old style class.
      if issubclass(BdistRPMCommand, object):
        spec_file = super(BdistRPMCommand, self)._make_spec_file()
      else:
        spec_file = bdist_rpm._make_spec_file(self)

      python_package = 'python3'

      description = []
      requires = ''
      summary = ''
      in_description = False

      python_spec_file = []
      for line in iter(spec_file):
        if line.startswith('Summary: '):
          summary = line[9:]

        elif line.startswith('BuildRequires: '):
          line = (f'BuildRequires: {python_package:s}-setuptools, '
                  f'{python_package:s}-devel')

        elif line.startswith('Requires: '):
          requires = line[10:]
          continue

        elif line.startswith('%description'):
          in_description = True

        elif line.startswith('python setup.py build'):
          if python_package == 'python3':
            line = '%py3_build'
          else:
            line = '%py2_build'

        elif line.startswith('python setup.py install'):
          if python_package == 'python3':
            line = '%py3_install'
          else:
            line = '%py2_install'

        elif line.startswith('%files'):
          lines = [
              f'%files -n {python_package:s}-%{{name}}',
              '%defattr(644,root,root,755)',
              '%license LICENSE',
              '%doc ACKNOWLEDGEMENTS AUTHORS README']

          lines.extend([
              '%{python3_sitelib}/esedbrc/*.py',
              '%{python3_sitelib}/esedbrc/*.yaml',
              '%{python3_sitelib}/esedbrc*.egg-info/*',
              '',
              '%exclude %{_prefix}/share/doc/*',
              '%exclude %{python3_sitelib}/esedbrc/__pycache__/*',
              '%exclude %{_bindir}/*.py'])

          python_spec_file.extend(lines)
          break

        elif line.startswith('%prep'):
          in_description = False

          python_spec_file.append(f'%package -n {python_package:s}-%{{name}}')
          python_summary = f'Python 3 module of {summary:s}'

          python_spec_file.extend([
              f'Requires: {requires:s}',
              f'Summary: {python_summary:s}',
              '',
              f'%description -n {python_package:s}-%{{name}}'])

          python_spec_file.extend(description)

          python_spec_file.extend([
              '%package -n %{name}-tools',
              f'Requires: {python_package:s}-esedb-kb >= %{{version}}',
              f'Summary: Tools for {summary:s}',
              '',
              '%description -n %{name}-tools'])

          python_spec_file.extend(description)

        elif in_description:
          # Ignore leading white lines in the description.
          if not description and not line:
            continue

          description.append(line)

        python_spec_file.append(line)

      python_spec_file.extend([
          '',
          '%files -n %{name}-tools',
          '%{_bindir}/*.py'])

      return python_spec_file


def parse_requirements_from_file(path):
  """Parses requirements from a requirements file.

  Args:
    path (str): path to the requirements file.

  Returns:
    list[str]: name and optional version information of the required packages.
  """
  requirements = []
  if os.path.isfile(path):
    with open(path, 'r') as file_object:
      file_contents = file_object.read()

    for requirement in pkg_resources.parse_requirements(file_contents):
      try:
        name = str(requirement.req)
      except AttributeError:
        name = str(requirement)

      if not name.startswith('pip '):
        requirements.append(name)

  return requirements


esedbrc_description = (
    'Extensible Storage Engine (ESE) database resources (esedbrc)')

esedbrc_long_description = (
    'esedbrc is a Python module part of esedb-kb to allow reuse of Extensible '
    'Storage Engine (ESE) database resources.')

command_classes = {}
if BdistMSICommand:
  command_classes['bdist_msi'] = BdistMSICommand
if BdistRPMCommand:
  command_classes['bdist_rpm'] = BdistRPMCommand

setup(
    name='esedbrc',
    version=esedbrc.__version__,
    description=esedbrc_description,
    long_description=esedbrc_long_description,
    long_description_content_type='text/plain',
    license='Apache License, Version 2.0',
    url='https://github.com/libyal/esedb-kb',
    maintainer='Joachim Metz',
    maintainer_email='joachim.metz@gmail.com',
    cmdclass=command_classes,
    classifiers=[
        '',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages=find_packages('.', exclude=[
        'docs', 'scripts', 'tests', 'tests.*', 'utils']),
    package_dir={
        'esedbrc': 'esedbrc'
    },
    include_package_data=True,
    package_data={
        'esedbrc': ['*.yaml']
    },
    zip_safe=False,
    scripts=glob.glob(os.path.join('scripts', '[a-z]*.py')),
    data_files=[
        ('share/doc/esedb-kb', [
            'ACKNOWLEDGEMENTS', 'AUTHORS', 'LICENSE', 'README']),
    ],
    install_requires=parse_requirements_from_file('requirements.txt'),
    tests_require=parse_requirements_from_file('test_requirements.txt'),
)
