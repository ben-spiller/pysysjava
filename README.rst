.. image:: ../../workflows/PySys/badge.svg
	:target: ../../actions
.. image:: ../../workflows/Docs/badge.svg
	:target: ../../actions
.. image:: https://codecov.io/gh/ben-spiller/pysysjava/branch/main/graph/badge.svg
	:target: https://codecov.io/gh/ben-spiller/pysysjava

Java plugins for PySys
======================
This is a collection of plugins for the PySys System Test Framework that allow you to easily compile and run Java(R) 
classes from your PySys tests, and a plugin that allows running JUnit tests as if they were PySys tests, 
plus support for generating Java code coverage reports. 

This project also serves as a good example of how to create, test, document and package PySys plugins, including:

	- creating a PySys test plugin to make help methods available to all your testcases; 
	- creating a PySys descriptor loader that dynamically creates PySys test descriptors based on the files; 
	  found under a directory (in this case, .java JUnit test classes), allowing seamless integration of JUnit testing 
	  alongside your other PySys tests; 
	- creating a PySys writer plugin to generate code coverage reports; 
	- using GitHub Actions to run PySys tests to check the plugins work correctly (with Python code coverage); 
	- building HTML documentation for the plugins (with cross-references to the main PySys documentation); 
	- generating a Python .whl package for installing them, and a GitHub Actions workflow for uploading to PyPi. 

Feel free to fork this project and use as a starting point for your own plugins that add support for new 
languages/toolsets to PySys. To make it easy to reuse code from this plugin project it has a Public Domain license. 

If this project inspires you to create new PySys plugins that may be useful for others in the PySys community, please 
consider whether you could make them available as an open-source project and on PyPi so that everyone can benefit.

For more information about the features of this plugin and how to install and use it, see the documentation: 
https://ben-spiller.github.io/pysysjava/

This repo uses a Maven POM to download the Java dependencies used for testing and for building the sample application. 
However Maven isn't used by the plugin itself if you prefer to download the jars through some other mechanism that's 
fine. 