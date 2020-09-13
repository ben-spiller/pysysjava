import json, time

import pysys
from pysys.constants import *

import pysysjava.junittest
import pysysjava.junitxml

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		def runPySys(args, stdouterr, **kwargs):
			env = self.createEnvirons(command='java', overrides={
				'PYSYS_APP_HOME': self.project.testRootDir+'/..',
				'JAVA_HOME': self.project.javaHome,
				'JUNIT_CLASSPATH': self.project.junitFrameworkClasspath,
			})
			
			return self.startPython(['-m', 'pysys']+args+['--outdir', self.output+'/'+stdouterr], environs=env, 
				workingDir=self.input, stdouterr=stdouterr, background=True, **kwargs)
			
		self.waitForBackgroundProcesses([
			runPySys(['run'], stdouterr='pysys-default-args'),
			runPySys(['run', '-XjunitArgs=-tmy-tag1'], stdouterr='pysys-includetag1'),
			runPySys(['run', '-XjunitArgs=-exclude-tag="my-tag1"'], stdouterr='pysys-excludetag1'),
			runPySys(['run', '-XjunitArgs=-t my-tag-disabled'], stdouterr='pysys-all-skipped'),
			runPySys(['run', '-XjunitArgs=--select-method=myorg.mytest1.TestSuite1#shouldPass()'], stdouterr='pysys-select-method1'),
			runPySys(['run', '-XjunitArgs=-invalidargument'], stdouterr='pysys-invalid-arg', expectedExitStatus='!= 0'),
		])

	def validate(self):
		def getTestcases(name): return self.getExprFromFile(name+'.out', 'INFO +-- ([^:]+)', returnAll=True)
		
		self.assertThat('len(testcases) == 4', testcases__eval="getTestcases('pysys-default-args')")
		
		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-includetag1')", 
			expected=['myorg.mytest1.TestSuite1 shouldBeSkipped()', 'myorg.mytest1.TestSuite1 shouldPass()'])
		
		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-excludetag1')", 
			expected=['myorg.mytest2.TestSuite2 shouldBeSkipped2()', 'myorg.mytest2.TestSuite2 shouldPass2()'])
			
		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-all-skipped')", 
			expected=['myorg.mytest1.TestSuite1 shouldBeSkipped()', 'myorg.mytest2.TestSuite2 shouldBeSkipped2()'])
		self.assertThatGrep('pysys-all-skipped.out', 'Test final outcome: +(.+)', expected='SKIPPED')
		self.assertThatGrep('pysys-all-skipped.out', 'Test outcome reason: +(.+)', 
			expected='All 2 JUnit tests are skipped: Reason test is disabled goes here')

		# since select is additive, this will just include everything
		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-select-method1')", 
			expected=['myorg.mytest1.TestSuite1 shouldBeSkipped()', 'myorg.mytest1.TestSuite1 shouldPass()', 
				'myorg.mytest2.TestSuite2 shouldBeSkipped2()', 'myorg.mytest2.TestSuite2 shouldPass2()'])
