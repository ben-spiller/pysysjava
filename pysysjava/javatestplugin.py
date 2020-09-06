"""
About the module. Yeehaw!
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

log = logging.getLogger('pysys.pysysjava.JavaTestPlugin')

def walkDirTree(dir, dirIgnores=None, followlinks=False):
	"""
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

class JavaTestPlugin(object):
	"""
	This is a PySys test plugin for compiling, running and testing Java applications. 
	
	You can access the methods of this class from any test using ``self.java.XXX`` if you add it to your project 
	configuration with an alias such as ``java``::
	
		<test-plugin classname="pysysjava.javatestplugin.JavaTestPlugin" alias="java"/>
	
	This plugin assumes the existence of a project property named javaHome that contains the path to the JDK. 
	"""

	# Class (static) variables for default plugin property values:
	defaultCompilerArgs = '-g'
	"""
	A space-delimited string of ``javac`` arguments. By default we enable full debugging information. 
	
	You may also want to add other options such as ``-source`` and ``-target`` release version. 
	"""
	
	defaultJVMArgs = '-Xmx512m -XX:+HeapDumpOnOutOfMemoryError'
	"""
	A space-delimited string of JVM arguments to use by default when running ``java`` processes. 
		
	By default the maximum heap size is limited to 512MB, but you may wish to set a larger heap limit if you are 
	starting processes that require more memory - but be careful that the test machine has sufficient resources to 
	cope with multiple tests running concurrently without risking out of memory conditions. 
	"""

	defaultClasspath = ''
	"""
	A default classpath that will be used for Java compilation and execution unless overridden. 
	
	For details of how this plugin handles delimiters in the classpath string see `toClasspathList()`.
	
	You can assign to self.defaultClasspath within a test to update the default that will be used for later 
	compilation or Java execution tasks, for example::
	
		TODO - add example
	
	"""

	_codeCoverageArgs = []
	"""
	A list of JVM arguments to add whenever starting a Java process, unless the ``disableCoverage`` 
	flag is set. This property is not set in pysysproject.xml but by a Java code coverage writer (if enabled). 
	"""

	def setup(self, testObj):
		self.owner = self.testObj = testObj
		
		# This message isn't useful for debugging errors so suppress it
		self.owner.logFileContentsDefaultExcludes.append('Picked up JAVA_TOOL_OPTIONS:')
		
		self.log = log
		self.javaHome = self.owner.project.javaHome
		assert os.path.isdir(self.javaHome), 'Missing javaHome location "%s"'%self.javaHome
		
		exeSuffix = '.exe' if IS_WINDOWS else ''
		
		self.javacExecutable = os.path.normpath(self.javaHome+'/bin/javac'+exeSuffix)
		"""The full path of the javac compiler executable. """

		self.javaExecutable = os.path.normpath(self.javaHome+'/bin/java'+exeSuffix)
		"""The full path of the java console executable. """
	
	def toClasspathList(self, classpath):
		"""
		Converts the specified classpath string to a list of classpath entries (or just returns the input if it's 
		already a list). Glob expressions such as ``*.jar`` will be expanded if the parent directory exists and there 
		is at least one match. 
		
		If None is specified, the `defaultClasspath` is used. 
		
		In this PySys plugin classpath strings can be delimited with the usual OS separator ``os.pathsep`` 
		(e.g. ``:`` or ``;``), but to allow for platform-independence (given Windows uses ``:`` for drive letters), 
		if the string contains ``;`` or a newline separator those will be used for splitting instead. Any whitespace or empty 
		elements will be deleted. 
		
		It is recommended to use absolute not relative paths for classpath entries. 
		
		>>> plugin = JavaTestPlugin()

		>>> plugin.toClasspathList(['a.jar', 'b.jar'])
		['a.jar', 'b.jar']

		>>> plugin.toClasspathList('  a.jar  ; b.jar ; c:/foo  '])
		['a.jar', 'b.jar', 'c:/foo']

		>>> plugin.toClasspathList(os.pathsep.join(['a.jar', 'b.jar'])
		['a.jar', 'b.jar']

		>>> plugin.toClasspathList(None) is None
		True
		
		"""
		if classpath is None: return self.toClasspathList(self.defaultClasspath)
		
		if isstring(classpath): # assume it's already split unless it's a string
			if '\n' in classpath:
				classpath = classpath.split('\n')
			elif ';' in classpath:
				classpath = classpath.split(';')
			else:
				classpath = classpath.split(os.pathsep)
			classpath = [c.strip() for c in classpath if len(c.strip())>0]
			
		# glob expansion
		if '*' not in ''.join(classpath): return classpath
		
		expanded = []
		for c in classpath:
			if '*' not in c:
				expanded.append(c)
				continue
				
			globbed = sorted(glob.glob(c))
			if not globbed: 
				self.log.debug('Classpath glob entry had no matches: %s', c)
				expanded.append(c)
			else:
				expanded.extend(globbed)
		return expanded

	def compile(self, input=None, output='javaclasses', classpath=None, args=None, **kwargs):
		"""Compile Java source files into classes. By default we compile Java files from the test's input directory to 
		``self.output/javaclasses``. 
		
		:param str or list[str] input: Typically a directory (relative to the test Input dir) in which to search for 
			classpaths; alternatively a list of Java source files. By default we compile source files under the 
			test Input directory. 
		:param str output: The path (relative to the test Output directory) where the output will be written. 
		:param list[str] or str classpath: The classpath to use, or None if the ``self.defaultClasspath`` should 
			be used (which by default is empty). The classpath can be specified as a list or a single string delimited 
			by ``;``, newline or ``os.pathsep``; see `toClasspathList()` for details. 
		:param list[str] args: List of compiler arguments such as ``--Werror`` or ``-nowarn`` (to control warn 
			behaviour). If not specified, the ``defaultCompilerArgs`` plugin property is used. 
		:param kwargs: Additional keyword arguments such as ``timeout=`` will be passed to 
			`pysys.basetest.BaseTest.startProcess`. 
		"""
		# need to escape windows \ else it gets removed; do this the same on all platforms for consistency)
		if args is None: args = shlex.split(self.defaultCompilerArgs.replace(u'\\',u'\\\\'))
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
				assert False, 'Input path does not exist: %s'%i
		assert inputfiles, 'No .java files found to compile in %s'%input		
		displayName = kwargs.pop('displayName', 'javac<%s -> %s>'%(os.path.basename(input[0]), os.path.basename(output)))
		
		classpath = self.toClasspathList(classpath)

		args = list(args)
		
		output = mkdir(os.path.join(self.owner.output, output))
		if os.listdir(output): self.log.warn('Compiling Java to an output directory that already contains some files: %s', output)
		args.extend(['-d', output])
		args.extend(inputfiles)
		
		# duplicate the startProcess logic since these args will be hidden behind the @args filename
		debuginfo = []
		for i, a in enumerate(args): debuginfo.append("    arg #%-2d    : %s"%( i+1, a) )
		debuginfo.append('  with compilation classpath: \n%s' % '\n'.join("     cp #%-2d    : %s%s"%(
			i+1, pathelement, '' if os.path.exists(pathelement) else ' (does not exist!)') for i, pathelement in enumerate(classpath)) 
			or '(none)')
		
		self.log.debug("Javac compiler arguments for %s:\n%s", displayName, '\n'.join(d for d in debuginfo))

		if classpath: args = ['-classpath', os.pathsep.join(classpath)]+args
		
		stdouterr = kwargs.pop('stdouterr', self.owner.allocateUniqueStdOutErr('javac.%s'%os.path.basename(output)))
		
		# Create a file using the default encoding for the javac arguments, since javac command lines can be too 
		# long for the OS otherwise
		argsFilename = stdouterr if isstring(stdouterr) else stdouterr[0][:-4]
		argsFilename = os.path.join(self.owner.output, argsFilename+'.args.txt')
		with openfile(argsFilename, 'w') as f:
			for a in args:
				f.write('"%s"'%a.replace('\\','\\\\')+'\n')
		
		process = self.owner.startProcess(self.javacExecutable, ['@'+argsFilename], stdouterr=stdouterr, displayName=displayName, 
			onError=lambda process: [
				self.owner.logFileContents(process.stderr, maxLines=0, 
					logFunction=lambda line:
						self.log.info(u'  %s', line, extra=pysys.utils.logutils.BaseLogFormatter.tag(
							LOG_ERROR if ': error:' in line else 
							LOG_WARN if ': warning:' in line else 
							LOG_FILE_CONTENTS))
				),
				self.owner.getExprFromFile(process.stderr, '(.*(error|invalid).*)')
			][-1])
		
		# log stderr even when it works so we see warnings
		self.owner.logFileContents(process.stderr, maxLines=0)
		return process

	def startJava(self, classOrJar, args=[], classpath=None, jvmArgs=None, props={}, disableCoverage=False, **kwargs):
		"""
		Start a Java process to execute the specified class or .jar file. 
		
		For example::

			myserver = self.java.startJava(self.project.appHome+'/my_server*.jar', ['127.0.0.1', self.getNextAvailableTCPPort()], 
				stdouterr='my_server', background=True)
		
			self.java.defaultClasspath = [self.project.appHome+'/mydeps.jar']
			self.java.compile(self.input, args=['--Werror'])
			self.java.startJava('myorg.MyHttpTestClient', ['127.0.0.1', port], stdouterr='httpclient', 
				classpath=self.java.defaultClasspath+[self.output+'/javaclasses'], timeout=60)
			
		:param str classOrJar: Either a class (from the classpath) to execute, or the path to a ``.jar`` file 
			(an absolute path or relative to the output directory) whose manifest indicates the main class.
			Since some jar names contain a version number, a ``*`` glob expression can be used in the .jar file 
			provided it matches exactly one jar and still ends with the ``.jar`` suffix.
			
		:param list[str] args: Command line arguments for the specified class. 
		
		:param list[str] or str classpath: The classpath to use, or None if the ``self.defaultClasspath`` should 
			be used (which by default is empty). The classpath can be specified as a list or a single string delimited 
			by ``;``, newline or ``os.pathsep``; see `toClasspathList()` for details. 
			
		:param list[str] jvmArgs: List of JVM arguments to pass before the class/jar name, such as ``-Xmx512m``. 
			If None is specified, the ``defaultJVMArgs`` plugin property is used. 
		
		:param dict[str,str] props: System properties to be added to the jvmArgs (each entry results in a 
			``-Dkey=value`` jvmArg).
		
		:param bool disableCoverage: Set to True to ensure Java code coverage is not captured for this process. 
			Code coverage can also be disabled on a per-test/directory basis by setting ``self.disableCoverage`` or 
			adding the ``disableCoverage`` group to the ``pysystest.xml``.
		
		:param kwargs: Additional keyword arguments such as ``stdouterr=``, ``timeout=``, ``onError=`` and 
			``background=`` will be passed to `pysys.basetest.BaseTest.startProcess`. 
		
		"""
		
		if jvmArgs is None: 
			jvmArgs = shlex.split(self.defaultJVMArgs.replace(u'\\',u'\\\\'))
		else:
			jvmArgs = list(jvmArgs) # copy it so we can mutate it below
		if (not disableCoverage) and not self.owner.disableCoverage:
			jvmArgs = self._codeCoverageArgs+jvmArgs
		for k,v in props.items():
			jvmArgs.append('-D%s=%s'%(k, v))
		originalClasspath = classpath

		displayName = kwargs.pop('displayName', 'java %s'%(kwargs.get('stdouterr',None) or os.path.basename(classOrJar)))

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

		# TODO: maybe delete empty-ish .err files?
		
		return self.owner.startProcess(self.javaExecutable, jvmArgs+args, displayName=displayName, **kwargs)
	
	def jar(self):
		assert False, 'Not implemented yet'
		
	#TODO:  could colour code logFileCOntents output from JVM