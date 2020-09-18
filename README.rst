HTML documentation is available at: https://ben-spiller.github.io/pysysjava/
.. image:: ../../workflows/PySys/badge.svg
	:target: ../../actions
.. image:: ../../workflows/Docs/badge.svg
	:target: ../../actions
.. image:: https://codecov.io/gh/ben-spiller/pysysjava/branch/main/graph/badge.svg
	:target: https://codecov.io/gh/ben-spiller/pysysjava
.. inclusion-marker-section-project-links

Java plugins for PySys
======================
This is a collection of plugins for the PySys System Test Framework that support compiling and running Java(R) classes 
in your PySys tests, and a wrapper that allows running JUnit tests as if they were PySys tests. 

This project also serves as a good example of how to create, test, document and package PySys plugins, including 
the use of GitHub Actions to run PySys tests (with Python code coverage), build HTML documentation for the plugins, 
and generate a Python .whl package for installing them. 

So feel free to fork it and use as a starting point for your own plugins supporting the language or toolset of your 
choice. To make this as easy as possible, this plugin project has a simple Public Domain license. 

Installation
------------
To use these plugins, you will need:

	- Python 3.6+
	- PySys 1.6.1+
	- Java 8+ (currently tested with Java 8 and Java 14)

To install, just use the standard ``pip3`` (or on Windows ``pip.exe``) executable::

	pip3 install PySys-Java
