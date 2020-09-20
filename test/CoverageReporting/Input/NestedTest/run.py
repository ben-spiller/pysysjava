import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		self.java.startJava('myorg.MainClass', [], stdouterr='myjava1', classpath=self.project.testRootDir+'/../classpath*')
		self.java.startJava('myorg.MainClass', [], stdouterr='myjava2', classpath=self.project.testRootDir+'/../classpath*')

	def validate(self):
		self.addOutcome(PASSED)
