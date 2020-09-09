import json, time

import pysys
from pysys.constants import *

import pysysjava.junittest
import pysysjava.junitxml

class PySysTest(pysysjava.junittest.JUnitTest):
	def setup(self):
		pass # do not do any java compilation
	def execute(self):
		# just use some canned ant output
		self.copy(self.input+'/ant-output', self.output+'/junit-reports')

	def validate(self):
		# this is really just to check no exceptions, and for manual glancing at the output
		self.log.info('--- validate output:')
		super(PySysTest, self).validate()
		self.log.info('--- end of validate output')
		self.addOutcome(PASSED, override=True) # reset outcome
		
		self.assertGrep('run.log', 'This testsuite produced some stdout/err.*[.]xml')
		
		parsed = {}
		reportdir = self.output+'/junit-reports'
		allresults = []
		for f in sorted(os.listdir(reportdir)):
			if not f.endswith('.xml'): continue
			suite, results = pysysjava.junitxml.JUnitXMLParser(reportdir+'/'+f).parse()
			parsed[f] = {'info':suite, 
				'results':results}
			allresults.extend(results)
			self.assertThat('0 < durationSecs < 60', durationSecs=suite['durationSecs'], f=f)
			
			# strip out the bits that might change
			for k in ['timestamp', 'durationSecs', 'hostname']:
				if suite.get(k) or suite.get(k)==0.0: suite[k] = '<removed>'
			for r in results:
				for k in ['outcomeDetailsFull', 'durationSecs']:
					if r.get(k) or r.get(k)==0.0: r[k] = '<removed>'
		self.assertDiff(
			self.write_text('parsed_junit_xml.json', json.dumps(parsed, indent='  ', sort_keys=True)) )
