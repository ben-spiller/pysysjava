PySys Java Plugins
==================
This project provides some plugins for the PySys System Test Framework that will be useful if your application 
is written in Java(R). Features include:

	- compiling Java test tools from your tests; 
	- easily starting Java processes, with convenient mechanisms to specify the classname/.jar, classpath and JVM 
	  arguments; 
	- executing JUnit test classes just like other PySys tests (providing a unified approach between your system and 
	  unit testing); 
	- generating Java code coverage reports. 

Installation
------------
To use these plugins, you will need:

	- Python 3.6+
	- PySys 1.6.1+
	- Java 8+ (currently tested with Java 8 and Java 14)
	- Optionally: JUnit 5, if you want to run JUnit tests (JUnit 4 is supported via the JUnit 5 vintage engine)
	- Optionally: JaCoCo, if you want to generate Java code coverage reports (currently tested with JaCoCo 0.8.6)

To install, just use the standard ``pip3`` executable (or ``pip.exe`` on Windows):: 

	pip3 install PySys-Java

Test Plugin for Java
--------------------
See `pysysjava.javaplugin` for information about the PySys test (and runner) plugin. 

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

Java Code Coverage Reporting
----------------------------
See `pysysjava.coverage` for information about generating Java code coverage reports from any Java process 
launched by PySys (including JUnit tests and integration tests). 

The writer can merge together all the individual coverage files into a single combined one, and generate both an 
XML report (suitable for uploading to an online coverage reporting service) and an HTML report (for human consumption). 
For the reporting to run it is necessary to specify the classpath and if possible the directories under which the 
source .java files can be found. An example configuration is::

		<writer classname="pysysjava.coverage.JavaCoverageWriter" alias="javaCoverageWriter">
			<property name="jacocoDir" value="${testRootDir}/../jacoco"/>

			<property name="destDir" value="__coverage_java.${outDirName}"/>
			<property name="destArchive" value="JavaCoverage.zip"/>
			
			<property name="agentArgs" value='includes=myorg*'/>

			<property name="classpath" value="${appHome}/*.jar"/>
			<property name="sourceDirs" value="${testRootDir}/../src"/>
			<property name="reportArgs" value='--name "My amazing report"'/>
		</writer>
