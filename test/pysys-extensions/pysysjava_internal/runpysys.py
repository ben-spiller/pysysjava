import sys
import os
import logging

import pysys
import pysysjava

class RunPySysPlugin(object):
	"""
	This is a simple test plugin that allows running PySys from a PySys test. 
	"""

	def setup(self, testObj):
		self.owner = testObj
		self.project = self.owner.project
		self.log = logging.getLogger('pysys.runpysys')

	def runPySys(self, args, stdouterr, background=True, workingDir=None, environs={}, **kwargs):
		"""
		Run PySys with the specified arguments. 
		
		By default it runs in the background with the test Input/ as the working directory containing the tests, but with an 
		outdir argument that ensures output is written to this test's output directory (unless the workingDir is 
		already under the output dir). 
		
		The main environment variables needed by this project are passed through. 
		
		"""
		env = {
			'JAVA_HOME': self.project.javaHome,
			'JUNIT_CLASSPATH': self.project.junitFrameworkClasspath,
			'JACOCO_DIR': self.project.jacocoDir,
			'PYTHONPATH': os.pathsep.join(sys.path), # Coverage can get confused if this is different than the parent process
			
			'PYSYSJAVA_TARGET_DIR': os.path.normpath(self.project.appHome+'/target'),
			'PYSYSJAVA_DIR': os.path.dirname(pysysjava.__file__), # TODO: just needed temporarily until PySys supports loading test modules from pythonpath
		}
		env.update(environs)

		env = self.owner.createEnvirons(command=pysys.constants.PYTHON_EXE, overrides=env)
		workingDir = workingDir or self.owner.input
		if args[0] == 'run' and not workingDir.startswith(self.owner.output): args = args+['--outdir', self.owner.output+'/'+stdouterr]
		
		return self.owner.startPython(['-m', 'pysys']+args, 
			environs=env, 
			workingDir=workingDir, 
			stdouterr=stdouterr, 
			background=background, 
			**kwargs)
