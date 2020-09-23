import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.java.compile()
		self.java.startJava('myorg.HelloWorld', ["Hi there!"], stdouterr='java-hello', classpath='javaclasses')

		self.java.compile(self.input+'/myorg/HelloWorld.java', output='javaclasses2')
		self.java.startJava('myorg.HelloWorld', ["Hi there!"], stdouterr='java-hello2', classpath='javaclasses2')
		
		# check we can do the same via the runner
		self.deleteDir(self.runner.output+'/javaclasses')
		if os.path.exists(self.runner.output+'/java-hello-runner.out'): os.remove(self.runner.output+'/java-hello-runner.out')
		self.runner.java.compile(self.input)
		self.runner.java.startJava('myorg.HelloWorld', ["Hi there!"], stdouterr='java-hello-runner', classpath='javaclasses')

	def validate(self):
		self.logFileContents('java-hello.err')
		self.assertGrep('java-hello.err', ".*", contains=False, ignores=['Picked .*'])
		self.assertGrep('java-hello.out', "Hello world - 'Hi there!'")

		self.assertPathExists(self.runner.output+'/javaclasses')
		self.assertGrep(self.runner.output+'/java-hello-runner.out', "Hello world - 'Hi there!'")
	