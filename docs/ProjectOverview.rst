PySys Java Plugins
==================

This project consists of a plugin for the PySys System Test Framework that allows you to easily compile and run Java(R) 
classes from your PySys tests, and a plugin that allows running JUnit tests as if they were PySys tests. 

To use these plugins, you will need:

	- Python 3.6+
	- PySys 1.6.1+
	- Java 8+ (currently tested with Java 8 and Java 14)
	- Optionally: JUnit 5 (if you want to run JUnit tests); JUnit 4 is supported via the JUnit 5 vintage engine

To install, just use the standard ``pip3`` executable (or ``pip.exe`` on Windows): ``pip3 install PySys-Java``

Test Plugin for Java
--------------------
See `pysysjava.testplugin` for information about the PySys test plugin. 

Once configured in your PySys project, this plugin makes it easy to run Java classes and jars from your PySys 
``run.py`` tests, and also to compile small testing tools needed by individual test cases. 

For example::

	myserver = self.java.startJava(self.project.appHome+'/my_server*.jar', ['127.0.0.1', self.getNextAvailableTCPPort()], 
		stdouterr='my_server', background=True)

	self.java.defaultClasspath = [self.project.appHome+'/mydeps.jar']
	self.java.compile(self.input, output=self.output+'/javaclasses', args=['--Werror'])
	self.java.startJava('myorg.MyHttpTestClient', ['127.0.0.1', port], stdouterr='httpclient', 
		classpath=self.java.defaultClasspath+[self.output+'/javaclasses'], timeout=60)

JUnit Execution from PySys
--------------------------
See `pysysjava.junittest` for information about running JUnit tests from PySys. 

You can either have a single PySys test for a whole directory tree of JUnit tests, or for larger projects and 
increased control, use the JUnit descriptor loader that creates separate PySys tests (in-memory) for each JUnit test
class, allowing them to be executed individually (and in separate JVM processes)::

	pysys run --threads=10 MyJUnitTests_org.myorg.TestSuiteFoo MyJUnitTests_org.myorg.TestSuiteBar

Classpath, JVM arguments, timeout and more can be customized on a per-test or per-directory basis using ``<user-data>`` 
properties in the ``pysystest.xml`` or ``pysysdirconfig.xml`` file, for example::

	<pysysdirconfig>
		
		<id-prefix>MyJUnitTests_</id-prefix>

		<data>
			<user-data name="junitTestDescriptorForEach" value="class"/>

			<user-data name="junitStripPrefixes" value="myorg.mytest1, myorg"/>

			<user-data name="javaClasspath" value="${appHome}/target/logging-jars/*.jar"/>
			<user-data name="jvmArgs" value="-Xmx256M"/>

			<user-data name="junitTimeoutSecs" value="600"/>
			<user-data name="junitConfigArgs" value=""/>
		</data>
	</pysysdirconfig>

There is also a simple parser for Ant-style JUnit XML reports (used to implement the above) in `pysysjava.junitxml`, 
which could also be useful for getting data from other (non-JUnit) testing engines that use the same reporting file 
format. 
