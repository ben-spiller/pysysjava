#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA



"""
A writer that causes code coverage information for this PySys process to be produced. 
"""


import logging, sys, io, os, shlex

from pysys.constants import *
from pysys.writer.api import *
from pysys.writer.testoutput import PythonCoverageWriter
from pysys.utils.fileutils import mkdir, deletedir, toLongPathSafe, fromLongPathSafe, pathexists

log = logging.getLogger('pysys.writer')

class PythonSelfCoverageWriter(PythonCoverageWriter):

	includeThisPySysProcess = False
	"""
	Set this option to True if you will be invoking the Python classes you wish to test directly from this process. 
	
	This should only be used when writing a test suite for a PySys plugin. Requires ``pythonCoverageConfigFile`` to be 
	set. 
	"""
	
	pythonCoverageConfigFile = u''
	"""
	The coverage.py configuration file that defines how coverage information will be gathered. 
	"""

	pythonCoverageArgs = u''
	"""
	(deprecated - use pythonCoverageConfigFile instead)
	
	A string of command line arguments used to customize the ``coverage run`` and ``coverage html`` commands. 
	Use "..." double quotes around any arguments that contain spaces. 
	
	For example::
	
		<property name="pythonCoverageArgs" value="--rcfile=${testRootDir}/python_coveragerc"/>
	"""

	def getCoverageArgsList(self): # also used by startPython()
		args = shlex.split(self.pythonCoverageArgs.replace(u'\\',u'\\\\')) # need to escape windows \ else it gets removed; do this the same on all platforms for consistency
		if self.pythonCoverageConfigFile: args.append('--rcfile=%s'%self.pythonCoverageConfigFile)
		return args
	
	def setup(self, *args, **kwargs):
		super(PythonSelfCoverageWriter, self).setup(*args, **kwargs)
		if self.includeThisPySysProcess:
			assert self.pythonCoverageConfigFile, 'pythonCoverageConfigFile must be set when using includeThisPySysProcess'
			import coverage
			# This mirrors the logic in coverage.process_startup()
			self.__selfCoverage = coverage.Coverage(config_file=self.pythonCoverageConfigFile, 
				data_file=mkdir(self.destDir)+os.sep+'.coverage.python.pysys-process')
			self.__selfCoverage.start()

	def cleanup(self, **kwargs):
		if self.includeThisPySysProcess:
			self.__selfCoverage.stop()
			self.__selfCoverage.save()
		super(PythonSelfCoverageWriter, self).cleanup(**kwargs)
