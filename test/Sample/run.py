import json, time

import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		self.copy(self.project.testRootDir+'/../sample', self.output+'/sample')

		self.pysys.runPySys(['run', '-o', 'myoutdir', '-XcodeCoverage', '-j0', '--mode=ALL', '--record'], 
			stdouterr='pysys', workingDir=self.output+'/sample/src/test', background=False)

	def validate(self):
		self.logFileContents('pysys.out', maxLines=0)
		s = self.output+'/sample'
		
		# Check we executed the JUnit tests, and that the output went to the right place
		self.assertGrep('pysys.out', 'Id: +JUnitTests_myserver.MyArgsParserTests')
		self.assertGrep('pysys.out', 'Id: +JUnitTests_myserver.MyServerJUnit4Tests')
		self.assertPathExists(s+'/src/test/java/__pysys_output/myorg.myserver.MyArgsParserTests/myoutdir/run.log')
		
		# Check the coverage found the source files
		self.assertPathExists(s+'/target/pysys/__coverage_java.myoutdir/myorg.myserver/MyArgsParser.java.html')

		self.assertGrep(s+'/target/pysys/__coverage_java.myoutdir/jacoco-sessions.html', 'MyServer_002.my_server1', encoding='utf-8')
		self.assertGrep(s+'/target/pysys/__coverage_java.myoutdir/jacoco-sessions.html', 'JUnitTests_myserver.MyServerTests.junit', encoding='utf-8')

		# Coverage should not include unit tests as source classes
		self.assertThat('len(coverageFiles)>0 and "Test" not in ",".join(coverageFiles)', coverageFiles=os.listdir(s+'/target/pysys/__coverage_java.myoutdir/myorg.myserver'))
		