import json, time

import pysys
from pysys.constants import *

import pysysjava.junittest
import pysysjava.junitxml

class PySysTest(pysysjava.junittest.JUnitTest):
	def validate(self):
		# First the JnNit validation
		super(PySysTest, self).execute()

		# Now additional verification
		
		# This checks that the JUnit5 --config options were passed through
		self.assertGrep('junit.out', 'Using parallel execution mode')
	
		# This checks that the log4j2 configuration is working correctly
		self.assertGrep('junit-reports/TEST-junit-jupiter.xml', 'This is a log message from pysysModeAsSystemProperty')
		