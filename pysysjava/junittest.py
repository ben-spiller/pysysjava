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
	
	There are 3 options for customizing the arguments that will be passed to the JUnit console launcher:
	
		- ``junitConfigArgs`` should be used for configuration options (e.g. ``--config=``) that should always be 
		  used for these tests, typically configured in the ``user-data`` of the test or directory descriptor. 
		- ``junitSelectionArgs`` should be used for ``--select-*`` arguments that identify which tests are covered by 
		  this PySys tess, typically a descriptor's ``user-data``. 
		  If not specified, selection arguments are automatically added for every package in the compiled classes 
		  directory. 
		-  ``junitArgs`` exists to provide a way to add one-off arguments runs on the PySys 
		  command line (_in addition_ to the above arguments), e.g. ``pysys run "-XjunitArgs=-t MYTAG"``. 
	
	Any classpath requirements or runtime JVM arguments should be customized using the properties described 
	in `pysysjava.javatestplugin` such as ``javaClasspath`` and ``jvmArgs``. 
	"""

	# NB: although these variables will end up as list[str] we define the defaults as a simple string not [] because we 
	# want to use shell or classpath string-splitting rather than the usual comma-separated splitting algorithm. 

	junitConfigArgs = ''
	"""
	JUnit console launcher command line arguments needed to configure the JUnit tests, e.g. ``--config key=value``. 
	
	If needed, this should be set in the test descriptor ``user-data``. 
	
	See JUnit documentation for more information about the console launcher command line arguments. 
	"""

	junitSelectionArgs = ''
	"""
	JUnit console launcher command line arguments needed to select which JUnit tests are part of this PySys test, 
	e.g. ``--select-package=myorg.myserver``. 
	
	If needed, this should be set in the test descriptor ``user-data``. If not specified, selection arguments are 
	automatically added for every package in the compiled classes directory. 
	
	See JUnit documentation for more information about the console launcher command line arguments. 
	"""
	
	junitArgs = ''
	"""
	Extra JUnit console launcher command line arguments, which will be used in addition to any `junitConfigArgs` 
	and `junitSelectionArgs`.
	
	This is usually not set in a test descriptor ``user-data`` but instead on the PySys command line with ``-X``.
	
	For example: ``pysys run -XjunitArgs=a b "--config=foo=bar baz" c d e"``, or more realistically: 
	``-XjunitArgs=-tMY-TAG`` (to run just the testcases with the specified JUnit tag).

	See JUnit documentation for more information about the console launcher command line arguments. 
	"""

	junitFrameworkClasspath = ''
	"""
	Must be set as either a project property or in the as test/directory descriptor ``user-data``. 
	
	The value is a list of jars (delimited by semicolon, os.pathsep, or newline), making up the JUnit framework and the 
	`junit-platform-console-standalone`` launcher jar. 
	"""
	
	junitTimeoutSecs = TIMEOUTS['WaitForProcess']
	"""
	The time allowed in total for execution of all JUnit tests. 
	"""

	# Properties that could be overridden by a subclass if needed
	_testGenre = 'JUnit'
	
	javaclassesDir = 'javaclasses'
	
	def setup(self):
		super(JUnitTest, self).setup()
		
		assert self.java, 'This test class requires the JavaTestPlugin test-plugin to be configured with alias=java'
		
		self.junitFrameworkClasspath = self.java.toClasspathList(
			self.junitFrameworkClasspath or self.project.getProperty('junitFrameworkClasspath', ''))
		if not self.junitFrameworkClasspath or not os.path.exists(self.junitFrameworkClasspath[0]):
			raise Exception('The junitFrameworkClasspath project (or descriptor) property must be set to a valid list of jars containing the JUnit framework and launcher: %s'%self.junitFrameworkClasspath)
		
		# TODO: only compile if no test has already compiled them
		self.compileTestClasses()
	
	def compileTestClasses(self):
		self.java.compile(input=self.input, classpath=self.java.defaultClasspath+self.junitFrameworkClasspath, output=self.javaclassesDir)
	
	def execute(self):
		
		testClasses = os.path.join(self.output, self.javaclassesDir)
		if not os.listdir(testClasses):
			raise Exception('No classes were found after compiling "%s"'%self.input)
		classpath = self.java.toClasspathList(self.java.defaultClasspath)+[testClasses]
		self.log.debug('Executing JUnit tests with classpath: \n%s', '\n'.join("     cp #%-2d    : %s%s"%(
			i+1, pathelement, '' if os.path.exists(pathelement) else ' (does not exist!)') for i, pathelement in enumerate(classpath)))
		
		# NB: any items in the descriptor's user-data get automatically assigned as instance variables (unless 
		# overridden with a -X option).
		
		argOverrides = self.java._splitShellArgs(self.junitArgs)
		args = [
			'--config', 'junit.platform.output.capture.stdout=true',
			'--config', 'junit.platform.output.capture.stderr=true',
		]
		args.extend(self.java._splitShellArgs(self.junitConfigArgs))
		
		selectionArgs = self.java._splitShellArgs(self.junitSelectionArgs)
		if selectionArgs: # allow overriding in the descriptor
			args.extend(selectionArgs)
		else:
			# We want to run all the test classes under this directory; the -d option doesn't seem to work so use the 
			# package option to achieve the same thing. This should be more efficient than scanning the entire 
			# classpath especially if there are a lot of dependencies.
			packages = []
			with os.scandir(testClasses) as it:
				for entry in it:
					if entry.is_dir():
						packages.append(entry.name)
			if packages: 
				for p in packages: args.extend(['-p', p])
			else:
				# Fall back to classpath scan (e.g. maybe all the classes are in the default package)
				args.append('--scan-classpath')
		
		customArgs = self.java._splitShellArgs(self.junitArgs)
		if customArgs:
			args.extend(customArgs)
			self.log.info('Running with additional JUnit args: \n%s', '\n'.join("    arg #%-2d    : %s"%(
				i+1, a) for i, a in enumerate(customArgs)))
		
		args = ['--reports-dir', self.output+'/junit-reports', 
			'--disable-ansi-colors',
			'--classpath=%s'%os.pathsep.join(classpath),
			]+args
			
		
		launcher = [cp for cp in self.junitFrameworkClasspath if 'junit-platform-console-standalone' in os.path.basename(cp)]
		if len(launcher) != 1:
			raise Exception('Cannot find junit-platform-console-standalone .jar file in the junitFrameworkClasspath: %s', self.junitFrameworkClasspath)
		self.java.startJava(launcher[0], 
			args, stdouterr='junit', expectedExitStatus=' in [0, 1]', 
			onError=lambda process: [self.logFileContents(process.stderr), self.getExprFromFile(process.stderr, '.+')][-1],
			timeout=self.junitTimeoutSecs) 
			
		# NB: the above does not give an error if no tests were selected; we rely on validation for that

	def validate(self):
		outcomeCounts = {
			PASSED: 0,
			SKIPPED: 0,
			FAILED: 0,
			BLOCKED: 0,
			TIMEDOUT: 0,
		}
		
		t = {} # just in case no tests were found at all
		
		logSeparator = False
		alreadyseen = set() # JUnit 5 doesn't do this, but Ant can sometimes generate duplicates for nested test classes
		for f in sorted(os.listdir(toLongPathSafe(self.output+'/junit-reports'))):
			if f.endswith('.xml'):
				suite, tests = JUnitXMLParser(toLongPathSafe(self.output+'/junit-reports/'+f)).parse()
				if suite['tests']+suite.get('skipped',0) == 0:
					self.log.debug('Ignoring suite "%s" which contains no tests', suite['tests'])
					continue

				if logSeparator:
					self.log.info('')
					self.log.info('~'*63)
				logSeparator = True
					
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

		totalTestcases = sum(outcomeCounts.values())
		self.log.info('~'*63)
		if totalTestcases == 0:
			if self.junitArgs:
				# Allow it if args are customized, they're probably trying to deliberate run a subset
				self.addOutcome(SKIPPED, 'No tests were found (likely the result of the specified junitArgs)')
			else:
				# But otherwise, make it an error, as it's probably a mistake
				self.addOutcome(BLOCKED, 'No tests were found (using the specified junitArgs)')
		elif outcomeCounts[SKIPPED] == totalTestcases:
			self.addOutcome(SKIPPED, 'All %d %s tests are skipped: %s'%(outcomeCounts[SKIPPED], self._testGenre, t.get('outcomeReason') or '<no reason>'))
		else:
			self.log.info('Summary of all testcase outcomes for %s: %s', self.descriptor.id,
				', '.join('%d %s'%(c,o)for o, c in outcomeCounts.items() if c>0))
	
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