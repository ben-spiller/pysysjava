import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		try:
			self.java.compile('ErrorsTest.java', output='errors')
		except pysys.exceptions.AbortExecution as ex:
			self.addOutcome(PASSED, override=True)
			self.assertThat('expected in compilationErrorMessage', expected='package org.nonexistent', compilationErrorMessage=str(ex))
		else:
			self.addOutcome(FAILED, 'Expected failure due to compilation error')

		self.java.compile('WarningsTest.java', output='warnings', args=['-Xlint'], timeout=60) # set timeout just to check we can pass through xargs to startProcess
		
		# make the classpath long which will force us to use an @args filename
		self.java.compile('ClasspathTest.java', output='classpath', 
			classpath='nonexistent'+('x'*3000)+os.pathsep+
				self.project.testRootDir+'/../target/logging-jars/slf4j*.jar')
		

	def validate(self):
		self.assertGrep('run.log', "package org.nonexistent2 does not exist")
		self.assertPathExists('javac.classpath.args.txt')