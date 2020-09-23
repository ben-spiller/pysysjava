# PySys-Java Sample
[![PySys tests](https://github.com/ben-spiller/pysysjava/workflows/PySys-Java-Sample/badge.svg)](https://github.com/ben-spiller/pysysjava/actions)
[![codecov](https://codecov.io/gh/ben-spiller/pysysjava/branch/main/graph/badge.svg)](https://codecov.io/gh/ben-spiller/pysysjava)

This project shows how to use the PySys-Java plugins for the PySys system test framework to test a sample Java 
application (a small REST/HTTP server). 

Explore the tests in this sample to get an idea for what is possible with PySys-Java, or fork it to get started 
with your own Java/PySys project.

# License

This sample is released into the public domain (as described in the LICENSE file) to simplify copying and freely 
reusing in your own projects, whatever license they may use. 

# Running the tests

To use this project you need Python 3.6+, the latest version of PySys-Java, Java 8+, and Maven. Note that although 
PySys-Java does not itself require/use Maven (or require a Maven-style directory layout), we use Maven to build the 
sample and to demonstrate how PySys testing could be slotted into the standard Maven directory layout. 

The first step is to build the sample Java application (and download libraries such as JUnit that PySys will be using):

	mvn package

To see a list of the available PySys test:

	cd src/test
	pysys.py print

You'll note that in addition to standard PySys system tests, there are also dynamically loaded PySys tests representing 
each JUnit test class found under the test/java directory. 

You can then run all the tests, including the JUnit tests with "pysys.py run". 
For faster execution, do it multi-threaded with -j0, and if you're interested in seeing how the Java (JaCoCo-based) 
code coverage looks, run with this command:

	pysys.py run -j0 -XcodeCoverage

To run just the JUnit tests, use a PySys inclusion group:

	pysys.py run -j0 -i junit

Note that there is a separate JVM process for each test class, ensuring complete isolation between executions 
of each class. 

To again run just the JUnit tests and also pass arguments to the JUnit 5 console launcher asking it to only execute 
tests that have the "config-files" JUnit tag, use the following PySys -X option:

	pysys.py run -j0 -i junit "-XjunitArgs=-t config-files"
	
	
# Exploring the sample tests

Now it's time to start exploring the run.py and .xml files in each of the tests. 

The system (non-unit) tests are in the src/test/pysys/ subdirectory, and demonstrate how to run Java jars/classes 
using the JavaPlugin which the project file imports as a test-plugin aliased to "self.java". They also show how to 
compile and use small Java test utilities that are needed by a single test, and how to configure the popular Log4j2 
library with a simple console-based configuration that's useful for testing. 

The JUnit tests are in src/test/java (the conventional Maven directory for unit tests written in Java). For 
demonstration purposes, these tests show some common JUnit 5 testing patterns including use of nested test classes 
and display names. Any stdout/err logged during execution of the JUnit is recorded alongside the test method that 
it came from. There is also a JUnit 4 test class to show how JUnit 5's vintage engine can automatically run 
JUnit 4 tests alongside the JUnit 5 ones. All that's needed to configure PySys to treat this as a directory of JUnit 
tests rather than a directory of normal PySys tests is the pysysdirconfig.xml file you'll see in that directory. 
This configuration file set the output path for the PySys tests to src/test/java/__pysys_output (with subdirectories 
created under that the directory output for each test class) but this can be changed if desired.

The pysysproject.xml file in this project is a useful starting point for new PySys/Java test projects using this 
plugin. It shows how to configure the test-plugin, how to enable the JUnit descriptor-loader, how to configure 
the Java code coverage report writer (which uses JaCoCo), and some project properties and defaults that are helpful 
for Java-based projects, especially ones that follow the directory layout popularized by Maven. 

If you want to see how the system and JUnit test results look when there are failures, try changing the source of 
MyServer.java to make it do the wrong thing.

Hope you enjoy using this plugin and sample. Feel free to copy anything here that is useful for your own projects. 
Send a pull request if you want to add/improve something in this plugin. 
If this project inspires you to create new PySys plugins that may be useful for others in the PySys community, please 
consider whether you could make them available as an open-source project and on PyPi so that everyone can benefit.
