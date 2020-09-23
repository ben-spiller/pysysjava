"""
Support for compiling/running/validating JUnit test classes from PySys.

If you want to run a whole directory of JUnit tests as a single PySys test, create a PySys test which uses the 
`JUnitTest` class in place of ``run.py``. 

For large or long-running JUnit suites it's better to use the `JUnitDescriptorLoader` (configured with a 
``pysysdirconfig.xml`` file). This descriptor loader creates in-memory PySys test descriptors for each JUnit test 
class found under the input directory (each of which is run using `JUnitTest`). This allows each test class to run 
in its own PySys worker thread (with its own JVM process, and its own separate output directory), and provides an 
easier way to re-run failed JUnit classes just as you would for a normal PySys test. It means there is no need to 
create separate ``pysystest.xml`` files on disk for each test class, yet you can interact with them using the 
full power of PySys. 

Both approaches allow the stdout/err (for example log output) to be captured from each testcase, and reporting of 
the (``.java``) location and nature of any test failures, with colour coding (if coloured output is enabled), and 
highlighting of actual vs expected comparison failure, to make it as easy as possible to read the output. 
"""

import pysys
import logging
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.fileutils import *
from pysys.utils.logutils import BaseLogFormatter
from pysys.xml.descriptor import DescriptorLoader, TestDescriptor

from pysysjava.junitxml import JUnitXMLParser
from pysysjava.javaplugin import JavaPlugin, walkDirTreeContents

class JUnitTest(BaseTest):
	"""
	A test class that compiles and runs one or more JUnit test suites. 
	
	This class requires the JUnit 5 console launcher, which itself supports running older JUnit 4 testcases - so 
	whichever version you need, you should be covered. 
	
	To run a set of JUnit tests from a single PySys test, put the unit test .java files in the Input directory, and 
	specify this class in the ``pysystest.xml``::
	
		<data>
			<class name="JUnitTest" module="${appHome}/pysysjava/junittest"/>
			...
		</data>

	
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
		
		- ``junitArgs`` exists to provide a way to add one-off arguments runs on the PySys 
		  command line (*in addition* to the above arguments), e.g. ``pysys run "-XjunitArgs=-t MYTAG"``. 
	
	Any classpath requirements or runtime JVM arguments should be customized using the properties described 
	in `pysysjava.javaplugin` such as ``javaClasspath`` and ``jvmArgs``. 
	
	The JUnit process is given Java system properties for the PySys testcase Input/ directory (``pysys.input``), 
	the test project root directory (``pysys.project.testRootDir``), and if this PySys test has any modes defined, the current 
	mode (``pysys.mode``). 
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
	``junit-platform-console-standalone`` launcher jar. 
	"""
	
	junitTimeoutSecs = float(TIMEOUTS['WaitForProcess'])
	"""
	The time allowed in total for execution of all JUnit tests. 
	"""

	# Undocumented properties that could be overridden by a subclass if needed
	javaclassesDir = 'javaclasses'
	junitReportsDir = 'junit-reports'
	_testGenre = 'JUnit'
	
	def setup(self):
		super(JUnitTest, self).setup()
		
		# Don't assume that the alias "java" has been used; instead locate it based on class
		self.java = next((plugin for plugin in self.testPlugins if isinstance(plugin, JavaPlugin)), None)
		assert self.java, 'This test class requires JavaPlugin to be configured as a <test-plugin> in pysysproject.xml'
		
		self.junitFrameworkClasspath = self.java.toClasspathList(
			self.junitFrameworkClasspath or self.project.getProperty('junitFrameworkClasspath', ''))
		if not self.junitFrameworkClasspath or not os.path.exists(self.junitFrameworkClasspath[0]):
			raise Exception('The junitFrameworkClasspath project (or descriptor) property must be set to a valid list of jars containing the JUnit framework and launcher: %s'%self.junitFrameworkClasspath)
		
		# TODO: only compile if no test has already compiled them
		self.compileTestClasses()

	def execute(self):
		self.java.startJava(**self.getJUnitKwArgs()) 

	def validate(self):
		self.validateJUnitReports(os.path.join(self.output, self.junitReportsDir))

	# The methods above override the standard test class; following are where they are implemented

	def compileTestClasses(self):
		self.java.compile(input=self.input, classpath=self.java.defaultClasspath+self.junitFrameworkClasspath, output=self.javaclassesDir)
	
	def getJUnitKwArgs(self):
		# This is a flexible way to defining the arguments that allows a subclass to make changes if needed
	
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
		if len(selectionArgs)==0: # If not overridden in the descriptor, use default of "everything"
			# We want to run all the test classes under this directory; the -d option doesn't seem to work so use the 
			# package option to achieve the same thing. This should be more efficient than scanning the entire 
			# classpath especially if there are a lot of dependencies.
			with os.scandir(testClasses) as it:
				for entry in it:
					if entry.is_dir():
						selectionArgs.append('-p')
						selectionArgs.append(entry.name)
			
			if len(selectionArgs)==0: 
				# Fall back to classpath scan (e.g. maybe all the classes are in the default package)
				selectionArgs.append('--scan-classpath')
				
		args.extend(selectionArgs)
		
		customArgs = self.java._splitShellArgs(self.junitArgs)
		if customArgs:
			args.extend(customArgs)
			self.log.info('Running with additional JUnit args: \n%s', '\n'.join("    arg #%-2d    : %s"%(
				i+1, a) for i, a in enumerate(customArgs)))
		
		args = ['--reports-dir', os.path.join(self.output, self.junitReportsDir), 
			'--disable-ansi-colors',
			'--classpath=%s'%os.pathsep.join(classpath),
			]+args

		launcher = [cp for cp in self.junitFrameworkClasspath if 'junit-platform-console-standalone' in os.path.basename(cp)]
		if len(launcher) != 1:
			raise Exception('Cannot find junit-platform-console-standalone .jar file in the junitFrameworkClasspath: %s', self.junitFrameworkClasspath)
		
		kwargs = {
			'classOrJar': launcher[0],
			'arguments': args,
			'expectedExitStatus': 'in [0, 1]', # allow failing tests to be dealt with later, but not complete failure to execure the launcher
			'onError': lambda process: [self.logFileContents(process.stderr), self.getExprFromFile(process.stderr, '.+')][-1],
			'displayName': 'JUnit %s'%' '.join(a for a in selectionArgs if a not in ['-p', '-c']),
			'timeout':self.junitTimeoutSecs,
			'stdouterr': 'junit',
		}
		if self.mode: 
			kwargs['jvmProps'] = {
				'pysys.mode': self.mode,
				'pysys.input': self.input,
				'pysys.project.testRootDir': self.project.testRootDir,
				}
		return kwargs
		
	def validateJUnitReports(self, reportsDir):
		outcomeCounts = {
			PASSED: 0,
			SKIPPED: 0,
			FAILED: 0,
			BLOCKED: 0,
			TIMEDOUT: 0,
		}
		
		t = {} # just in case no tests were found at all
		
		self.addOutcome(PASSED) # if no failures, pass	
	
		logSeparator = False
		alreadyseen = set() # JUnit 5 doesn't do this, but Ant can sometimes generate duplicates for nested test classes
		for f in sorted(os.listdir(toLongPathSafe(reportsDir))):
			if f.endswith('.xml'):
				suite, tests = JUnitXMLParser(toLongPathSafe(reportsDir+'/'+f)).parse()
				if suite['tests']+suite.get('skipped',0) == 0:
					self.log.debug('Ignoring suite "%s" which contains no tests', suite['name'])
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
					
					outcome = self.validateJUnitTestcaseResult(t)
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
				self.addOutcome(BLOCKED, 'No tests were found')
		elif outcomeCounts[SKIPPED] == totalTestcases:
			self.addOutcome(SKIPPED, 'All %d %s tests are skipped: %s'%(outcomeCounts[SKIPPED], self._testGenre, t.get('outcomeReason') or '<no reason>'))
		else:
			self.log.info('Summary of all testcase outcomes for %s: %s', self.descriptor.id,
				', '.join('%d %s'%(c,o)for o, c in outcomeCounts.items() if c>0))
	
	def validateJUnitTestcaseResult(self, t):
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

		testFile = os.path.normpath(self.input+'/'+t['classname'].replace('.', '/').split('$')[0]+'.java')
		if getattr(self, '_cachedPathExists', None) != testFile: # cache the file system lookup
			self._cachedPathExists, self._cachedPathExistsResult = testFile, os.path.isfile(toLongPathSafe(testFile))
		if not self._cachedPathExistsResult: 
			testFile = t['classname'] # this is a reasonable fallback for giving location information
		else:
			detailLogger('   Test file: %s', os.path.normpath(fromLongPathSafe(testFile)), extra=maintag)
		
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

log = logging.getLogger('pysys.pysysjava.junittest')

class JUnitDescriptorLoader(DescriptorLoader):
	"""
	A `pysys.xml.descriptor.DescriptorLoader` that dynamically creates a separate PySys test descriptor for each .java 
	JUnit test class found under the ``Input/`` directory. 
	
	To use this, create a ``pysysdirconfig.xml`` with a user-data element ``junitTestDescriptorForEach``. 
	
	You may also wish to add a ``junitStripPrefixes`` user-data to strip off long common package names from your 
	test classes and/or an ``id-prefix`` to add a common testId prefix indicating these are JUnit tests. 
	
	You can also use the ``junit*`` user-data options described in `JUnitTest` and the 
	``javaClasspath`` and ``jvmArgs`` described in `pysysjava.javaplugin.JavaPlugin`. 
	
	For example::
	
		<pysysdirconfig>
		
			<id-prefix>MyJUnitTests_</id-prefix>

			<data>
				<user-data name="junitTestDescriptorForEach" value="class"/>

				<user-data name="junitStripPrefixes" value="myorg.mytestpackage, myorg2"/>

				<user-data name="javaClasspath" value="${appHome}/target/logging-jars/*.jar"/>
				<user-data name="jvmArgs" value="-Xmx256M"/>

				<user-data name="junitTimeoutSecs" value="600"/>
				<user-data name="junitConfigArgs" value=""/>
			</data>
		
		</pysysdirconfig>
		
	"""


	def _handleSubDirectory(self, dir, subdirs, files, descriptors, parentDirDefaults, **kwargs):
		if parentDirDefaults is None: return False
		thing = parentDirDefaults.userData.get('junitTestDescriptorForEach', None)
		if not thing: return False
		
		# we could support other granularity such as per directory, per test method etc
		assert thing in ['class', ]
	
		stripPrefixes = [x.strip() for x in parentDirDefaults.userData.get('junitStripPrefixes', '').split(',') if x.strip()]
		
		# default regex is from the JUnit 5 console launcher
		includeClassnameRegex = re.compile(parentDirDefaults.userData.get('junitIncludeClassnameRegex', '^(Test.*|.+[.$]Test.*|.*Tests?)$')) 
		includeClassnameRegexCompiled = re.compile(includeClassnameRegex) 
		
		inputdir = toLongPathSafe(os.path.normpath(fromLongPathSafe(os.path.join(os.path.dirname(parentDirDefaults.file), parentDirDefaults.input))))
	
		found = 0
		for entry in walkDirTreeContents(inputdir, dirIgnores=OSWALK_IGNORES):
			if entry.is_file() and entry.name.endswith('.java'):
				classname = entry.path[len(inputdir):-5].strip(os.sep).replace(os.sep, '.')

				if not includeClassnameRegexCompiled.match(classname):
					log.debug('Ignoring JUnit class as name does not match regex for tests: "%s"', classname)
					continue
				
				found += 1
				userData = dict(parentDirDefaults.userData)
				userData['junitSelectionArgs'] = '--select-class %s'%classname
				
				id = classname
				for p in stripPrefixes:
					if id.startswith(p):
						id = id[len(p):].lstrip('.')
						break
				
				descriptors.append(TestDescriptor(
					file=fromLongPathSafe(parentDirDefaults.file), 
					id=parentDirDefaults.id+id, 
					title='JUnit %s - %s'%(thing, classname),
					groups=[u'junit']+parentDirDefaults.groups, 
					modes=parentDirDefaults.modes,
					classname="JUnitTest", # pysysjava.junittest.JUnitTest
					module=os.path.abspath(os.path.splitext(__file__)[0]),
					purpose = fromLongPathSafe(entry.path),
					userData = userData,
					
					# must ensure output dirs are unique even though lots of classes share the same testDir
					output=((parentDirDefaults.output+os.sep) if parentDirDefaults.output else '')+classname, 

					# copy everything else across from the defaults
					input=parentDirDefaults.input,
					traceability=parentDirDefaults.traceability,
					executionOrderHint=parentDirDefaults.executionOrderHint,
					skippedReason=parentDirDefaults.skippedReason,
					))
		if found == 0: raise Exception('No JUnit test .java files found matching "%s" in %s', includeClassnameRegex, fromLongPathSafe(inputdir))
		
		return True # means this directory has been fully handled so don't continue looking for PySys tests under this tree
