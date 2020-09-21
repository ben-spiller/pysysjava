import json, time

import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		self.copy(self.input, self.output+'/testroot')

		self.waitForBackgroundProcesses([
			self.pysys.runPySys(['run', '-j0', '--outdir', 'myoutputdir'], stdouterr='pysys-run', workingDir=self.output+'/testroot'),
			self.pysys.runPySys(['print', '--json'], stdouterr='pysys-print', workingDir=self.output+'/testroot'),
		])

	def validate(self):
		self.logFileContents('testroot/NestedTest/Output/myorg.mytest1.TestSuite1/myoutputdir~MyMode/run.log', maxLines=0)
		def getTestcases(name): return self.getExprFromFile('testroot/NestedTest/Output/'+name+'/run.log', 'INFO +-- ([^:]+)', returnAll=True)
		self.assertThat('testcases == expected', testcases__eval="getTestcases('myorg.mytest1.TestSuite1/myoutputdir~MyMode')", expected=[
			'myorg.mytest1.TestSuite1 shouldBeSkipped()', 
			'myorg.mytest1.TestSuite1 shouldPass()'])
		self.assertThat('testcases == expected', testcases__eval="getTestcases('myorg.mytest2.TestSuite2/myoutputdir~MyMode')", expected=[
			'myorg.mytest2.TestSuite2 shouldPass2()', 
			'myorg.mytest2.TestSuite2$NestedClass shouldPassNested()'])
		
		# Extract the bits that are worth diff-ing (and make it cross machine/platform)
		self.assertDiff(self.write_text('pysys-print.json', json.dumps([
			{
				'id':t['id'],
				'title':t['title'],
				'testDir':'.../'+os.path.basename(t['testDir']),
				'purpose':'.../'+os.path.basename(t['purpose']),
				'groups':t['groups'],
				'modes':t['modes'],
				'executionOrderHint':t['executionOrderHint'],
				'input':t['input'],
				'output':t['output'].replace('\\','/'),
				'reference':t['reference'],
				'userData':{k:('.../'+os.path.basename(v) if k=='javaClasspath' else v) for k,v in t['userData'].items()},
			} for t in pysys.utils.fileutils.loadJSON(self.output+'/pysys-print.out')], 
				indent='  ')))