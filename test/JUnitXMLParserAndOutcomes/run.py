import json, time

import pysys
from pysys.constants import *

import pysysjava.junittest
import pysysjava.junitxml

class PySysTest(pysysjava.junittest.JUnitTest):
	def execute(self):
		# execute the JUnit test
		super(PySysTest, self).execute()

	def validate(self):
		# Before any other validations, we use this trick to 
		self.log.info('--- validate output:')
		
		recordedOutcomes = []
		addOutcomeSaved = self.addOutcome
		def addOutcomeDEBUG(outcome, outcomeReason='', callRecord=None, override=False, **kwargs):
			if outcome != PASSED: recordedOutcomes.append(f'{outcome}: {outcomeReason}'+
				(" ; override=True" if override else "")+
				(" ; callRecord=%s"%','.join(callRecord) if callRecord else ""))
			addOutcomeSaved(outcome, outcomeReason=outcomeReason, callRecord=callRecord, override=override, **kwargs)
		self.addOutcome = addOutcomeDEBUG
		try:
			super(PySysTest, self).validate()
		finally:
			self.addOutcome = addOutcomeSaved
		self.log.info('--- end of validate output')
		self.addOutcome(PASSED, override=True) # rest outcome
		
		self.log.info('Outcome reasons were: \n  %s\n', '\n  '.join(recordedOutcomes))
		self.assertThat('outcomes == expected', outcomes = recordedOutcomes, expected=[
			'TIMED OUT: JUnit error: java.util.concurrent.TimeoutException: shouldTimeout() timed out after 10 milliseconds [in myorg.mytest.JUnit5Tests.shouldTimeout()] ; callRecord=myorg.mytest.JUnit5Tests:29', 
			'BLOCKED: JUnit error: java.lang.Exception: Bad test [in myorg.mytest.JUnit5Tests$NestedParent.shouldError()] ; callRecord=myorg.mytest.JUnit5Tests$NestedParent:43', 
			'FAILED: Assert that (expected == actual) with expected="Hello world", actual="Hello funky world", testcaseName="myorg.mytest.JUnit5Tests$NestedParent.shouldFail()"', 
			'BLOCKED: JUnit error: java.lang.Exception: This is a test error [in myorg.mytest.JUnit4Tests.shouldError] ; callRecord=myorg.mytest.JUnit4Tests:23', 
			'FAILED: Assert that (expected == actual) with expected="Hello []world", actual="Hello [funky ]world", testcaseName="myorg.mytest.JUnit4Tests.shouldFail"'
		])
	
		parsed = {}
		reportdir = self.output+'/junit-reports'
		for f in sorted(os.listdir(reportdir)):
			if not f.endswith('.xml'): continue
			suite, results = pysysjava.junitxml.JUnitXMLParser(reportdir+'/'+f).parse()
			parsed[f] = {'info':suite, 'results':results}
			self.assertThat('0 < durationSecs < 60', durationSecs=suite['durationSecs'], f=f)
			self.assertThat('now-60 < timestamp <= now', timestamp=suite['timestamp'], now=time.time(), f=f)
			
			# strip out the bits that might change
			for k in ['timestamp', 'durationSecs', 'hostname']:
				if suite.get(k) or suite.get(k)==0.0: suite[k] = '<removed>'
			for r in results:
				for k in ['outcomeDetailsFull', 'durationSecs']:
					if r.get(k) or r.get(k)==0.0: r[k] = '<removed>'
		self.assertDiff(
			self.write_text('parsed_junit_xml.json', json.dumps(parsed, indent='  ', sort_keys=True)) )
		