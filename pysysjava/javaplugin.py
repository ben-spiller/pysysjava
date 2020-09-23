"""
Support for compiling and running Java applications from the ``run.py`` of your PySys tests. 
"""
import sys
import os
import json
import logging
import fnmatch
import shlex
import glob

import pysys
from pysys.constants import *
from pysys.utils.pycompat import isstring
from pysys.utils.fileutils import *

log = logging.getLogger('pysys.pysysjava.javaplugin')

def walkDirTree(dir, dirIgnores=None, followlinks=False):
	"""
	:meta private: Not public API.
	
	Walks the specified directory tree, yielding an item for each directory in the tree 
	(similar to ``os.walk`` but better). 
	
	Compared to ``os.walk`` this method is more efficient and easier to use, correctly handles nested paths that 
	exceed the windows MAX_PATH limit, and has a simpler mechanism for skipping directories from the search tree. 
	Entries are sorted before being returned to ensure deterministic results. 
	
	For example::
	
		for dirpath, entries in walkDirTree(i, dirIgnores=pysys.constants.OSWALK_IGNORES):
			for entry in entries:
				if entry.is_file() and entry.name.endswith('.java'):
					inputfiles.append(entry.path)

	
	:param list[str], callable(DirEntry)->bool dirIgnores: Either a callable that returns True if the specified 
		directory should be skipped from traversal and from being returned, or a string or list of strings which are 
		glob patterns to be evaluated against the basename, e.g. ``dirIgnores=['.svn', '.git*']``. 
	:param bool followlinks: If True, directory symbolic links will be traversed as directories. Be careful of loops 
		when using this option. 
	:return (str,list[DirEntry]): Returns a generator that yields a tuple ``(dirpath: str, contents: list[DirEntry])`` 
		for each (non-ignored) directory in the tree. If running on Windows, the returned paths will have the long path 
		prefix ``\\?\`` which can be removed using `pysys.utils.fileutils.fromLongPathSafe` if needed. 
		
	"""
	
	if not callable(dirIgnores): 
		if dirIgnores is None:
			dirIgnores = lambda e: False
		else:
			if isstring(dirIgnores): dirIgnores = [dirIgnores]
			dirIgnores = lambda e, dirIgnores=dirIgnores: any(fnmatch.fnmatch(e.name, ignore) for ignore in dirIgnores)
	
	dir = pysys.utils.fileutils.toLongPathSafe(dir)
	with os.scandir(dir) as it:
		contents = []

		sortedEntries = list(it)
		sortedEntries.sort(key=lambda entry: entry.name)
		for entry in sortedEntries:
			if not entry.is_dir(follow_symlinks=followlinks):
				contents.append(entry)
				continue
			
			if dirIgnores(entry): 
				continue
			contents.append(entry)
			yield from walkDirTree(entry.path, dirIgnores=dirIgnores, followlinks=followlinks)
		yield dir, contents		

# TODO: or is it better to return (entry, contentsentries), which is simpler? or create a wrapper for this that returns that?

def walkDirTreeContents(dir, dirIgnores=None, followlinks=False):	
	"""
	:meta private: Not public API.

	Walks the specified directory tree, yielding an entry for file/symlink/directory (excluding the root directory 
	itself). 
	
	Compared to ``os.walk`` this method is more efficient and easier to use, correctly handles nested paths that 
	exceed the windows MAX_PATH limit, and has a simpler mechanism for skipping directories from the search tree. 
	Entries are sorted before being returned to ensure deterministic results. 
	
	For example::
	
		for entry in walkDirTreeContents(i, dirIgnores=pysys.constants.OSWALK_IGNORES):
			if entry.is_file() and entry.name.endswith('.java'):
				inputfiles.append(entry.path)
	
	:param list[str], callable(DirEntry)->bool dirIgnores: Either a callable that returns True if the specified 
		directory should be skipped from traversal and from being returned, or a string or list of strings which are 
		glob patterns to be evaluated against the basename, e.g. ``dirIgnores=['.svn', '.git*']``. 
	:param bool followlinks: If True, directory symbolic links will be traversed as directories. Be careful of loops 
		when using this option. 
	:return (str,list[DirEntry]): Returns a generator that yields a tuple ``(dirpath: str, contents: list[DirEntry])`` 
		for each (non-ignored) directory in the tree. If running on Windows, the returned paths will have the long path 
		prefix ``\\?\`` which can be removed using `pysys.utils.fileutils.fromLongPathSafe` if needed. 
		
	"""

	for dirpath, contents in walkDirTree(dir, dirIgnores=dirIgnores, followlinks=followlinks):
		for c in contents:
			yield c

class JavaPlugin(object):
	"""
	This is a PySys test plugin that for compiling and running Java applications from a PySys testcase (or from 
	the runner). 
	
	You can access the methods of this class from any test using ``self.java.XXX``. To enable this, just add it to your 
	project configuration with an alias such as ``java``::
	
		<test-plugin classname="pysysjava.javaplugin.JavaPlugin" alias="java"/>
	
	For advanced cases (compiling or starting Java from a runner class or plugin) you can also use this class as a 
	runner plugin::

		<runner-plugin classname="pysysjava.javaplugin.JavaPlugin" alias="java"/>
	
	This plugin assumes the existence of a project property named ``javaHome`` that contains the path to the JDK, 
	with a ``bin/`` subdirectory containing executables such as ``java`` and ``javac``. 
	
	Since you often want the same JVM arguments (e.g. max heap size etc), compiler arguments and classpath for 
	many of your tests, defaults for these can be configured via properties on the plugin (and in some cases also 
	on a per-test/per-directory basis by adding ``<user-data name="..." value="...">`` to your ``pysystest.xml`` 
	or ``pysysdirconfig.xml`` file. For example::
	
		<test-plugin classname="pysysjava.javaplugin.JavaPlugin" alias="java">
			<property name="defaultJVMArgs" value="-Xmx256m -XX:+HeapDumpOnOutOfMemoryError"/>
		</test-plugin>
		
	Or::
	
		<pysysdirconfig>
			<data>
				<user-data name="javaClasspath" value="${appHome}/target/logging-jars/*.jar"/>
				<user-data name="jvmArgs" value="-Xmx256M"/>
			</data>
		</pysysdirconfig>

	See below for more details about these properties. 
	
	"""

	# Class (static) variables for default plugin property values:
	defaultCompilerArgs = '-g'
	"""
	A space-delimited string of ``javac`` arguments. By default we enable full debugging information. 
	
	You may also want to add other options such as ``-source`` and ``-target`` release version. 
	"""
	
	defaultJVMArgs = '-Xmx512m -XX:+HeapDumpOnOutOfMemoryError -XX:-UsePerfData'
	"""
	A space-delimited string of JVM arguments to use by default when running ``java`` processes, unless overridden 
	by a per-test/dirconfig ``jvmArgs`` or a ``jvmArgs=`` keyword argument.
	
	By default the maximum heap size is limited to 512MB, but you may wish to set a larger heap limit if you are 
	starting processes that require more memory - but be careful that the test machine has sufficient resources to 
	cope with multiple tests running concurrently without risking out of memory conditions. 
	Also by default the ``-XX:-UsePerfData`` option is used to avoid creation of ``hsperfdata_XXX`` files 
	in the temp directory (typically the test output directory) which aren't useful and can prevent test cleanup. 
	
	This is converted to a ``list[str]`` when the plugin is setup ready for use by the test. 
	If a key named ``jvmArgs`` exists in the test or directory descriptor's ``user-data`` that value takes 
	precedence over the plugin property. 
	"""

	defaultClasspath = ''
	"""
	A default classpath that will be used for Java compilation and execution, unless overridden by a per-test/dirconfig 
	``javaClasspath`` user-data or a ``classpath=`` keyword argument. 
	
	For details of how this plugin handles delimiters in the classpath string see `toClasspathList()`.

	This is converted to a ``list[str]`` when the plugin is setup ready for use by the test. 
	If a key named ``javaClasspath`` exists in the test or directory descriptor's ``user-data`` that value takes 
	precedence over the plugin property. 
	
	"""

	def setup(self, owner):
		self.owner = owner # Usually a BaseTest, but since this is a dual-purpose plugin could also be a runner
		self.runner = getattr(owner, 'runner', owner)

		self.project = self.owner.project
		
		# This message isn't useful for debugging errors so suppress it
		self.owner.logFileContentsDefaultExcludes.append('Picked up JAVA_TOOL_OPTIONS:')
		
		self.log = log
		self.javaHome = self.owner.project.javaHome
		assert os.path.isdir(self.javaHome+'/bin'), 'Cannot find javaHome bin directory: "%s"'%self.javaHome+os.sep+'bin'
		
		exeSuffix = '.exe' if IS_WINDOWS else ''
		
		self.compilerExecutable = os.path.normpath(self.javaHome+'/bin/javac'+exeSuffix) # TODO: make configurable
		"""The full path of the javac compiler executable. """

		self.javaExecutable = os.path.normpath(self.javaHome+'/bin/java'+exeSuffix)
		"""The full path of the java console executable. """
		
		# Assume both of these methods make a copy of the static value (which makes it safe for tests to mutate the 
		# lists)
		descriptorUserData = owner.descriptor.userData if hasattr(owner, 'descriptor') else {} # Also support using it from a runner
		self.defaultClasspath = self.toClasspathList(self.project.expandProperties(
			descriptorUserData.get('javaClasspath', self.defaultClasspath)))
		self.defaultJVMArgs = self._splitShellArgs(self.project.expandProperties(
			descriptorUserData.get('jvmArgs', self.defaultJVMArgs)))

		self.owner.addCleanupFunction(lambda: [deletedir(self.owner.output+'/'+d) for d in os.listdir(self.owner.output)
			if d.startswith('hsperfdata_')] if os.path.exists(self.owner.output) else None, ignoreErrors=True)
		
	def compile(self, input=None, output='javaclasses', classpath=None, arguments=None, **kwargs):
		"""Compile Java source files into classes. By default we compile Java files from the test's input directory to 
		``self.output/javaclasses``. 
		
		For example::
		
			self.java.compile(self.input, arguments=['--Werror'])
		
		:param input: Typically a directory (relative to the test Input dir) in which to search for 
			classpaths; alternatively a list of Java source files. By default we compile source files under the 
			test Input directory. 
		:type input: str or list[str]
		:param str output: The path (relative to the test Output directory) where the output will be written. 
		:param classpath: The classpath to use, or None if the ``self.defaultClasspath`` should 
			be used (which by default is empty). The classpath can be specified as a list or a single string delimited 
			by ``;``, newline or ``os.pathsep``; see `toClasspathList()` for details. 
		:type classpath: str or list[str]
		:param list[str] arguments: List of compiler arguments such as ``--Werror`` or ``-nowarn`` (to control warn 
			behaviour). If not specified, the ``defaultCompilerArgs`` plugin property is used. 
		:param kwargs: Additional keyword arguments such as ``timeout=`` will be passed to 
			`pysys.basetest.BaseTest.startProcess`. 
			
		:return: The process object, with the full path to the output dir in the ``info`` dictionary.
		:rtype: pysys.process.Process
		"""
		# need to escape windows \ else it gets removed; do this the same on all platforms for consistency)
		if arguments is None: arguments = self._splitShellArgs(self.defaultCompilerArgs)
		if input is None: input = self.owner.input
		
		if isstring(input): input = [input]
		assert input, 'At least one input must be specified'
		
		inputfiles = []
		for i in input:	
			i = os.path.join(self.owner.input, i)
			if os.path.isfile(i):
				inputfiles.append(i)
			elif os.path.isdir(i):
				for entry in walkDirTreeContents(i, dirIgnores=OSWALK_IGNORES):
					if entry.is_file() and entry.name.endswith('.java'):
						inputfiles.append(fromLongPathSafe(entry.path) if len(entry.path) < 256 else entry.path)
			else: 
				assert False, 'Compilation input path does not exist: %s'%i
		assert inputfiles, 'No .java files found to compile in %s'%input		
		displayName = kwargs.pop('displayName', 'javac<%s => %s>'%(os.path.basename(input[0]), os.path.basename(output)))
		
		classpath = self.toClasspathList(classpath)

		args = list(arguments)
		
		output = mkdir(os.path.join(self.owner.output, output))
		if os.listdir(output): self.log.warn('Compiling Java to an output directory that already contains some files: %s', output)
		args.extend(['-d', output])
		args.extend(inputfiles)
		
		self.log.debug('Javac compiler classpath is: \n%s' % '\n'.join("     cp #%-2d    : %s%s"%(
			i+1, pathelement, '' if os.path.exists(pathelement) else ' (does not exist!)') for i, pathelement in enumerate(classpath)) 
			or '(none)')
		if classpath: args = ['-classpath', os.pathsep.join(classpath)]+args
		
		stdouterr = kwargs.pop('stdouterr', self.owner.allocateUniqueStdOutErr('javac.%s'%os.path.basename(output)))
		
		process = self.owner.startProcess(self.compilerExecutable, self._argsOrArgsFile(args, stdouterr), stdouterr=stdouterr, displayName=displayName, 
			onError=lambda process: [
				self.owner.logFileContents(process.stderr, maxLines=0, 
					logFunction=lambda line: # colouring the main lines in red makes this a lot easier to read
						self.log.info(u'  %s', line, extra=pysys.utils.logutils.BaseLogFormatter.tag(
							LOG_ERROR if ': error:' in line else 
							LOG_WARN if ': warning:' in line else 
							LOG_FILE_CONTENTS))
				),
				self.owner.getExprFromFile(process.stderr, '(.*(error|invalid).*)')
			][-1], info={'output':output}, **kwargs)
		
		# log stderr even when it works so we see warnings
		self.owner.logFileContents(process.stderr, maxLines=0)
		return process

	def _argsOrArgsFile(self, args, stdouterr):
		# If the length of the command line looks to be on the long side, put it into a separate @args file
		# Windows allows approx 32,000 chars; POSIX limit can be as low as 4096. 3000 seems safe.
		if len(' '.join(args)) <= 3000: return args
		
		# Create a file using the default encoding for the java arguments
		
		argsFilename = stdouterr if isstring(stdouterr) else stdouterr[0][:-4]
		argsFilename = os.path.join(self.owner.output, argsFilename+'.args.txt')
		with openfile(argsFilename, 'w') as f:
			for a in args:
				f.write('"%s"'%a.replace('\\','\\\\')+'\n')
		return ['@'+argsFilename]

	def startJava(self, classOrJar, arguments=[], classpath=None, jvmArgs=None, jvmProps={}, disableCoverage=False, stdouterr=None, **kwargs):
		"""
		Start a Java process to execute the specified class or .jar file. 
		
		For example::

			myserver = self.java.startJava(self.project.appHome+'/my_server*.jar', ['127.0.0.1', self.getNextAvailableTCPPort()], 
				stdouterr='my_server', background=True)
		
			self.java.defaultClasspath = [self.project.appHome+'/mydeps.jar']
			self.java.compile(self.input, output=self.output+'/javaclasses', arguments=['--Werror'])
			self.java.startJava('myorg.MyHttpTestClient', ['127.0.0.1', port], stdouterr='httpclient', 
				classpath=self.java.defaultClasspath+[self.output+'/javaclasses'], timeout=60)
		
		If the project includes a writer with alias "javaCoverageWriter" then that writer is requested to add some 
		JVM arguments to control code coverage (unless disableCoverage=True). 
		
		:param str classOrJar: Either a class (from the classpath) to execute, or the path to a ``.jar`` file 
			(an absolute path or relative to the output directory) whose manifest indicates the main class.
			Since some jar names contain a version number, a ``*`` glob expression can be used in the .jar file 
			provided it matches exactly one jar and still ends with the ``.jar`` suffix.
			
		:param list[str] arguments: Command line arguments for the specified class. 
		
		:param classpath: The classpath to use, or None if the ``self.defaultClasspath`` should 
			be used (which by default is empty). The classpath can be specified as a list or a single string delimited 
			by ``;``, newline or ``os.pathsep``; see `toClasspathList()` for details. 
		:type classpath: str or list[str]
			
		:param list[str] jvmArgs: List of JVM arguments to pass before the class/jar name, such as ``-Xmx512m``. 
			If None is specified, the ``defaultJVMArgs`` plugin property is used. 
		
		:param dict[str,str] jvmProps: System properties to be added to the jvmArgs (each entry results in a 
			``-Dkey=value`` jvmArg).
		
		:param bool disableCoverage: Set to True to ensure Java code coverage is not captured for this process. 
			Code coverage can also be disabled on a per-test/directory basis by setting ``self.disableCoverage`` or 
			adding the ``disableCoverage`` group to the ``pysystest.xml``.
		
		:param str stdouterr: The filename prefix to use for the stdout and stderr of the process 
			(out/err will be appended), or a tuple of (stdout,stderr) as returned from 
			`pysys.basetest.BaseTest.allocateUniqueStdOutErr`. 
			The filenames can be accessed from the returned process object using .stdout/err from the returned process 
			object.

		:param kwargs: Additional keyword arguments such as ``stdouterr=``, ``timeout=``, ``onError=`` and 
			``background=`` will be passed to `pysys.basetest.BaseTest.startProcess`. It is strongly recommended to 
			always include at ``stdouterr=`` since otherwise any error messages from the process will not be captured. 

		:return: The process object.
		:rtype: pysys.process.Process
		"""
		if jvmArgs is None: jvmArgs = self.defaultJVMArgs

		jvmArgs = list(jvmArgs) # copy it so we can mutate it below
		if (not disableCoverage) and (not self.owner.disableCoverage) and hasattr(self.runner, 'javaCoverageWriter'):
			jvmArgs = self.runner.javaCoverageWriter.getCoverageJVMArgs(
				owner=self.owner, stdouterr=stdouterr)+jvmArgs
		for k,v in jvmProps.items():
			jvmArgs.append('-D%s=%s'%(k, v))
		originalClasspath = classpath

		shortName = os.path.basename(stdouterr[0] if isinstance(stdouterr, tuple) else (stdouterr or classOrJar))

		displayName = kwargs.pop('displayName', 'java %s'%shortName)

		if classOrJar.endswith('.jar'):
			assert not originalClasspath, 'Java does not accept any classpath options when executing a .jar'
			
			jvmArgs.append('-jar')
			classOrJar = os.path.join(self.owner.output, classOrJar)
			if '*' in classOrJar: 
				resolvedJars = glob.glob(classOrJar)
				if len(resolvedJars) != 1: raise FileNotFoundError('Jar glob expression must resolve to exactly one jar but %d matches found for: %s'%(len(resolvedJars), classOrJar))
				classOrJar = resolvedJars[0]
			if not os.path.exists(classOrJar): raise FileNotFoundError('Cannot find file: "%s"'%classOrJar)
			jvmArgs.append(os.path.join(self.owner.output, classOrJar))
		else:
			classpath = self.toClasspathList(classpath)
			self.log.debug('Starting Java process %s with classpath: \n%s', displayName, '\n'.join("     cp #%-2d    : %s%s"%(
				i+1, pathelement, '' if os.path.exists(pathelement) else ' (does not exist!)') for i, pathelement in enumerate(classpath)))
			jvmArgs = ['-classpath', os.pathsep.join(classpath)] + jvmArgs
			jvmArgs.append(classOrJar)

		return self.owner.startProcess(self.javaExecutable, self._argsOrArgsFile(jvmArgs+arguments, shortName), stdouterr=stdouterr, **kwargs)

	def toClasspathList(self, classpath):
		"""
		Converts the specified classpath string to a list of classpath entries (or just returns the input if it's 
		already a list). Glob expressions such as ``*.jar`` will be expanded if the parent directory exists and there 
		is at least one match. 
		
		If None is specified, the `defaultClasspath` is used (either from the test/dir descriptor's ``classpath`` 
		user-data or the ``defaultClasspath`` plugin property). 
		
		In this PySys plugin classpath strings can be delimited with the usual OS separator ``os.pathsep`` 
		(e.g. ``:`` or ``;``), but to allow for platform-independence (given Windows uses ``:`` for drive letters), 
		if the string contains ``;`` or a newline separator those will be used for splitting instead. Any whitespace or empty 
		elements will be deleted. 
		
		It is recommended to use absolute not relative paths for classpath entries. 
		
		>>> plugin = JavaPlugin()

		>>> plugin.toClasspathList(['a.jar', 'b.jar'])
		['a.jar', 'b.jar']

		>>> plugin.toClasspathList('  a.jar  ; b.jar ; c:/foo  '])
		['a.jar', 'b.jar', 'c:/foo']

		>>> plugin.toClasspathList(os.pathsep.join(['a.jar', 'b.jar'])
		['a.jar', 'b.jar']

		>>> plugin.toClasspathList(None) is None
		True
		
		"""
		if classpath is None: 
			assert self.defaultClasspath is not None
			return self.toClasspathList(self.defaultClasspath) # call it again in case user has messed with it
		
		if isstring(classpath): # assume it's already split unless it's a string
			if ';' in classpath:
				classpath = classpath.replace('\n',';').split(';')
			else:
				classpath = classpath.replace('\n',os.pathsep).split(os.pathsep)
			classpath = [c.strip() for c in classpath if len(c.strip())>0]
			
		# glob expansion
		if '*' not in ''.join(classpath): return classpath
		
		expanded = []
		for c in classpath:
			if '*' not in c:
				expanded.append(c)
				continue
				
			globbed = sorted(glob.glob(c))
			if len(globbed)==0: # Fail in an obvious way in this case
				raise Exception('Classpath glob entry has no matches: "%s"', c)
			else:
				expanded.extend(globbed)
		return expanded

	@staticmethod
	def _splitShellArgs(commandstring):
		# Internal, not part of the API
		# Need to escape windows \ else it gets removed; do this the same on all platforms for consistency)
		return shlex.split(commandstring.replace(u'\\',u'\\\\'))
