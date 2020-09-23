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
		
		# Check the coverage found the source files
		self.assertPathExists(s+'/target/pysys/__coverage_java.myoutdir/myorg.myserver/MyArgsParser.java.html')
		self.assertGrep(s+'/target/pysys/__coverage_java.myoutdir/jacoco-sessions.html', 'MyServer_002.my_server1', encoding='utf-8')
		# Coverage should not include unit tests
		self.assertThat('len(coverageFiles)>0 and "Test" not in ",".join(coverageFiles)', coverageFiles=os.listdir(s+'/target/pysys/__coverage_java.myoutdir/myorg.myserver'))
		