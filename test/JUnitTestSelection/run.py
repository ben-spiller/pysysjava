import json, time

import pysys
from pysys.constants import *

import pysysjava.junittest
import pysysjava.junitxml

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		def runPySys(args, stdouterr, **kwargs):
			env = self.createEnvirons(command=PYTHON_EXE, overrides={
				'PYSYS_APP_HOME': self.project.testRootDir+'/..',
				'JAVA_HOME': self.project.javaHome,
				'JUNIT_CLASSPATH': self.project.junitFrameworkClasspath,
			})
			
			return self.startPython(['-m', 'pysys']+args+['--outdir', self.output+'/'+stdouterr], environs=env, 
				workingDir=kwargs.pop('workingDir', self.input), stdouterr=stdouterr, background=True, **kwargs)

		self.copy(self.input, self.output+'/no-junit-tests')
		self.deleteDir(self.output+'/no-junit-tests/NestedTest/Input')
		self.mkdir(self.output+'/no-junit-tests/NestedTest/Input')
		self.write_text(self.output+'/no-junit-tests/NestedTest/Input/Foo.java', 'class Foo {}') # not a test
		
		self.waitForBackgroundProcesses([
			runPySys(['run'], stdouterr='pysys-default-args'),
			runPySys(['run', '-XjunitArgs=-tmy-tag1'], stdouterr='pysys-includetag1'),
			runPySys(['run', '-XjunitArgs=-exclude-tag="my-tag1"'], stdouterr='pysys-excludetag1'),
			runPySys(['run', '-XjunitArgs=-t my-tag-disabled'], stdouterr='pysys-all-skipped'),
			runPySys(['run', '-XjunitArgs=-t nonexistent-tag'], stdouterr='pysys-include-nonexistent-tag'),
			runPySys(['run', '-XjunitArgs=-invalidargument'], stdouterr='pysys-invalid-arg', expectedExitStatus='!= 0'),
			runPySys(['run', '-XjunitSelectionArgs=--select-class=myorg.mytest1.TestSuite1'], stdouterr='pysys-select-class'),
			runPySys(['run', '-XjunitSelectionArgs=--select-method=myorg.mytest1.TestSuite1#shouldPass()'], stdouterr='pysys-select-method'),
			runPySys(['run'], stdouterr='pysys-no-tests', workingDir=self.output+'/no-junit-tests', expectedExitStatus='!= 0'),
		])

	def validate(self):
		def getTestcases(name): return self.getExprFromFile(name+'.out', 'INFO +-- ([^:]+)', returnAll=True)
		
		self.assertThat('len(testcases) == 4', testcases__eval="getTestcases('pysys-default-args')")
		
		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-includetag1')", 
			expected=['myorg.mytest1.TestSuite1 shouldBeSkipped()', 'myorg.mytest1.TestSuite1 shouldPass()'])
		
		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-excludetag1')", 
			expected=['myorg.mytest2.TestSuite2 shouldBeSkipped2()', 'myorg.mytest2.TestSuite2 shouldPass2()'])

		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-include-nonexistent-tag')", 
			expected=[])
		self.assertThatGrep('pysys-include-nonexistent-tag.out', 'Test final outcome: +(.+)', expected='SKIPPED')
		self.assertThatGrep('pysys-include-nonexistent-tag.out', 'Test outcome reason: +(.+)', 
			expected='No tests were found (likely the result of the specified junitArgs)')

		self.assertThatGrep('pysys-no-tests.out', 'Test final outcome: +(.+)', expected='BLOCKED')
		self.assertThatGrep('pysys-no-tests.out', 'Test outcome reason: +(.+)', 
			expected='No tests were found')

		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-all-skipped')", 
			expected=['myorg.mytest1.TestSuite1 shouldBeSkipped()', 'myorg.mytest2.TestSuite2 shouldBeSkipped2()'])
		self.assertThatGrep('pysys-all-skipped.out', 'Test final outcome: +(.+)', expected='SKIPPED')
		self.assertThatGrep('pysys-all-skipped.out', 'Test outcome reason: +(.+)', 
			expected='All 2 JUnit tests are skipped: Reason test is disabled goes here')

		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-excludetag1')", 
			expected=['myorg.mytest2.TestSuite2 shouldBeSkipped2()', 'myorg.mytest2.TestSuite2 shouldPass2()'])

		# select is NOT additive (unlike junitArgs) so this replaces the default selection behaviour
		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-select-class')", 
			expected=['myorg.mytest1.TestSuite1 shouldBeSkipped()', 'myorg.mytest1.TestSuite1 shouldPass()'])
		self.assertThat('testcases == expected', testcases__eval="getTestcases('pysys-select-method')", 
			expected=['myorg.mytest1.TestSuite1 shouldPass()'])
