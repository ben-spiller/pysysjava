import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.java.compile()
		self.java.startJava('myorg.HelloWorld', ["Hi there!"], stdouterr='java-hello', classpath='javaclasses')

		self.java.compile(self.input+'/myorg/HelloWorld.java', output='javaclasses2')
		self.java.startJava('myorg.HelloWorld', ["Hi there!"], stdouterr='java-hello2', classpath='javaclasses2')

	def validate(self):
		self.logFileContents('java-hello.err')
		self.assertGrep('java-hello.err', ".*", contains=False, ignores=['Picked .*'])
		self.assertGrep('java-hello.out', "Hello world - 'Hi there!'")
	