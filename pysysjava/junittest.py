import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.fileutils import *
from pysys.utils.logutils import BaseLogFormatter

from pysysjava.junitxml import JUnitXMLParser

class JUnitTest(BaseTest):
	"""
	A test class that compiles and runs one or more JUnit test suites. 
	
	Compilation happens in `pysys.basetest.BaseTest.setup` (shared across all JUnit tests that use the same source 
	directory), then execution in `pysys.basetest.BaseTest.execute` and finally reads the resulting XML reports and 
	adds outcomes for each testcase in `pysys.basetest.BaseTest.validate`. 
	"""

	junitArgs = ''
	"""
	Extra command line arguments to pass to junit. This can be overridden on the command line, e.g. ``-XjunitArgs=a b "c d e"``.
	
	This is in addition to any argument specified in the ``userData`` of the test/directory descriptor key 
	named ``java.junitArgs``.
	"""

	_testGenre = 'JUnit'
	
	def setup(self):
		super(JUnitTest, self).setup()
		
		assert self.java, 'This test class requires the JavaTestPlugin test-plugin to be configured with alias=java'
		
		self.junitFrameworkClasspath = self.java.toClasspathList(
			self.project.expandProperties(self.descriptor.userData.get('java.junitFrameworkClasspath','')) or self.project.properties.get('java.junitFrameworkClasspath'))
		if not self.junitFrameworkClasspath or not os.path.exists(self.junitFrameworkClasspath[0]):
			raise Exception('Please set the java.junitFrameworkClasspath project or descriptor property must contain the JUnit framework; cannot find it in: %s', self.junitFrameworkClasspath[0])
		
		# TODO: only compile if no test has already compiled them
		self.compileTestClasses()
	
	def compileTestClasses(self):
		self.java.compile(input=self.input, classpath=self.java.defaultClasspath+self.junitFrameworkClasspath)
	
	def execute(self):
		
		testClasses = self.output+'/javaclasses'
		if not os.listdir(testClasses):
			raise Exception('No classes were found after compiling "%s"'%self.input)
		classpath = self.java.toClasspathList(self.java.defaultClasspath)+[testClasses]
		self.log.debug('Executing JUnit tests with classpath: \n%s', '\n'.join("     cp #%-2d    : %s%s"%(
			i+1, pathelement, '' if os.path.exists(pathelement) else ' (does not exist!)') for i, pathelement in enumerate(classpath)))
		args = [
			'--config', 'junit.platform.output.capture.stdout=true',
			'--config', 'junit.platform.output.capture.stderr=true',
		]	\
			+self.java._splitShellArgs(self.project.expandProperties(self.descriptor.userData.get('java.junitArgs','')))\
			+self.java._splitShellArgs(self.junitArgs)
		
		# TODO: support argument files in case of a long JUnit command line. Maybe do this in the Java executable itself to keep life simple
		
		args = ['--reports-dir', self.output+'/junit-reports', 
			'--disable-ansi-colors',
			'--fail-if-no-tests',
			'--classpath=%s'%os.pathsep.join(classpath),
			]+args
			
		# We want to run all the test classes under this directory; the -d option doesn't seem to work so use the 
		# package option to achieve the same thing. 
		for d in os.listdir(testClasses):
			args.extend(['-p', d])
		
		launcher = [cp for cp in self.junitFrameworkClasspath if 'junit-platform-console-standalone' in os.path.basename(cp)]
		if len(launcher) != 1:
			raise Exception('Cannot find junit-platform-console-standalone .jar file in the junitFrameworkClasspath: %s', self.junitFrameworkClasspath)
		self.java.startJava(launcher[0], 
			args, stdouterr='junit', expectedExitStatus=' in [0, 1]', 
			timeout=int(self.project.expandProperties(self.descriptor.userData.get('java.junitTimeoutSecs')) or TIMEOUTS['WaitForProcess'])) # TODO: document timeout configuration parameter
		self.assertThatGrep('junit.out', '([0-9]+) tests found', 'int(value) > 0', abortOnError=True)

	def validate(self):
		outcomeCounts = {
			PASSED: 0,
			SKIPPED: 0,
			FAILED: 0,
			BLOCKED: 0,
			TIMEDOUT: 0,
		}
		
		logSeparator = False
		alreadyseen = set() # JUnit 5 doesn't do this, but Ant can sometimes generate duplicates for nested test classes
		for f in sorted(os.listdir(toLongPathSafe(self.output+'/junit-reports'))):
			if f.endswith('.xml'):
				if logSeparator:
					self.log.info('')
					self.log.info('~'*63)
				logSeparator = True

				suite, tests = JUnitXMLParser(toLongPathSafe(self.output+'/junit-reports/'+f)).parse()
				if suite['tests']+suite.get('skipped',0) == 0:
					self.log.debug('Ignoring suite "%s" which contains no tests', suite['tests'])
					continue
					
				self.log.info('Results for %d testcases from suite "%s":', suite['tests'], suite['name'])
				self.log.info('')
				
				for t in tests:
					key = t['classname']+'.'+t['name']
					if key in alreadyseen:
						self.log.info('Ignoring duplicate results for %s', key)
						continue
					alreadyseen.add(key)
					
					outcome = self.validateTestcaseResult(t)
					outcomeCounts[outcome] += 1
				
				# some JUnit formats (but not JUnit5) provide stdout/err at the suite level rather than per test 
				if suite.get('stdout') or suite.get('stderr'):
					self.log.info('This testsuite produced some stdout/err, see it at: %s', f)

		self.log.info('~'*63)
		if outcomeCounts[SKIPPED] == sum(outcomeCounts.values()):
			self.addOutcome(SKIPPED, 'All %d %s tests are skipped: %s'%(outcomeCounts[SKIPPED], self._testGenre, t['outomeReason'] or '<no reason>'))
		else:
			self.log.info('Summary of %s testcase outcomes for %s:', self._testGenre, self.descriptor.id)
			for o,c in outcomeCounts.items():
				if c > 0:
					self.log.info('% 3d testcases %s', c, o, extra=BaseLogFormatter.tag(str(o).lower()))
	
	def validateTestcaseResult(self, t):
		outcome = {
			'passed': PASSED,
			'failure': FAILED,
			'error': BLOCKED,
			'skipped': SKIPPED,
		}.get(t['outcome'], BLOCKED)
		if outcome in [BLOCKED,FAILED] and 'Timeout' in t.get('outcomeType',''): outcome = TIMEDOUT
		
		maintag = BaseLogFormatter.tag(str(outcome).lower())
		self.log.info('-- %s %s: %s (%0.1fs)', t['classname'], t['name'], t['outcome'], t['durationSecs'], 
			extra=maintag)
		
		# Don't log most details at run unless in debug mode
		detailLogger = self.log.debug if outcome == PASSED else self.log.info
				
		if 'displayName' in t and t['displayName'] != t['name']:
			detailLogger('   Display name: %s', t['displayName'], extra=maintag)

		testFile = os.path.normpath(self.descriptor.input+'/'+t['classname'].replace('.', '/').split('$')[0]+'.java')
		if getattr(self, '_cachedPathExists', None) != testFile: # cache the file system lookup
			self._cachedPathExists, self._cachedPathExistsResult = testFile, os.path.isfile(toLongPathSafe(testFile))
		if not self._cachedPathExistsResult: 
			testFile = t['classname'] # this is a reasonable fallback for giving location information
		else:
			detailLogger('   Test file: %s', testFile, extra=maintag)
		
		# It's much more useful to set the callRecord to the Java source file rather than this generic .py file
		callRecord = ['%s:%s'%(testFile, t.get('testFileLine') or '0')]
		
		if outcome == PASSED:
			pass
		elif 'comparisonActual' in t and outcome == FAILED:
			# Using assertThat gives us more user-friendly messages when there's a diff failure
			shouldfail = self.assertThat('expected == actual', expected=t['comparisonExpected'], actual=t['comparisonActual'], 
				testcaseName=t['classname']+'.'+t['name']) # TODO: callRecord=callRecord)
			assert not shouldfail, 'assertThat did not fail as expected' # should not happen
		elif outcome == SKIPPED: 
			# don't want to append a skipped outcome since that would override all other outcomes
			self.log.info('   Skipped because: %s', t['outcomeReason'] or '<unknown reason>', extra=BaseLogFormatter.tag(str(SKIPPED).lower()))
		else:
			self.addOutcome(outcome, '%s %s: %s [in %s.%s]'%(self._testGenre, t['outcome'], 
				t['outcomeReason'] or '<unknown reason>', t['classname'], t['name']), callRecord=callRecord)
		
		prefix = '\n  '
		if 'stdout' in t: 
			detailLogger('Testcase stdout from %s: %s', t['name'], prefix+t['stdout'].replace('\n', prefix), 
				extra=BaseLogFormatter.tag(LOG_DEBUG))
		if 'stderr' in t: 
			detailLogger('Testcase stderr from %s: %s', t['name'], prefix+t['stderr'].replace('\n', prefix), 
				extra=BaseLogFormatter.tag(LOG_DEBUG))
		if 'outcomeDetails' in t: 
			detailLogger('Failure details from %s: %s', t['name'], prefix+t['outcomeDetails'].replace('\n', prefix), 
				extra=BaseLogFormatter.tag(LOG_DEBUG))
			
		detailLogger('')
		return outcome