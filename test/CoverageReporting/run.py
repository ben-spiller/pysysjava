import json, time

import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		self.java.compile('src1', 'classpath1')
		self.java.compile('src2', 'classpath2', classpath=self.output+'/classpath1')
	
		self.copy(self.input, self.output+'/testroot')

		self.pysys.runPySys(['run', '-o', self.output+'/myoutdir', '-XcodeCoverage'], 
			stdouterr='pysys', workingDir=self.output+'/testroot', background=False)

	def validate(self):
		htmldir = 'myoutdir/__coverage_java.myoutdir'

		self.assertPathExists(htmldir+'/jacoco-merged-java-coverage.exec')
		self.assertPathExists(htmldir+'/java-coverage.xml')
		self.assertPathExists(htmldir+'/JavaCoverage.zip')

		# Check we passed the agent params including the space characters correctly
		self.assertGrep(htmldir+'/index.html', 'My amazing report')

		# Check that both invocations of Java were used (and didn't tread on each other)
		self.assertGrep(htmldir+'/jacoco-sessions.html', 'NestedTest.myjava1')
		self.assertGrep(htmldir+'/jacoco-sessions.html', 'NestedTest.myjava2')
		
		# Check we found the source files
		self.assertPathExists(htmldir+'/myorg/DepClass.java.html')
		self.assertPathExists(htmldir+'/myorg/MainClass.java.html')
		
		self.logFileContents('pysys.out', tail=True)
