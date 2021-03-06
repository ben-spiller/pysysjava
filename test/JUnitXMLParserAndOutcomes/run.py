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
		self.log.info('--- validate output:')
		
		# Before running the real validations, run the JUnitTest's validate method, intercepting the outcomes
		recordedOutcomes = []
		addOutcomeSaved = self.addOutcome
		def addOutcomeDEBUG(outcome, outcomeReason='', callRecord=None, override=False, **kwargs):
			if outcome != PASSED: recordedOutcomes.append(f'{outcome}: {outcomeReason}'+
				(" ; override=True" if override else "")+
				(" ; callRecord=%s"%(
					'None' if not callRecord else ','.join(
					[(('fullpath/'+os.path.basename(r))
						if os.path.exists(r[:r.rfind(':')]) 
						else r[:r.rfind(':')] 
					) for r in callRecord]))))
			addOutcomeSaved(outcome, outcomeReason=outcomeReason, callRecord=callRecord, override=override, **kwargs)
		self.addOutcome = addOutcomeDEBUG
		try:
			super(PySysTest, self).validate()
		finally:
			self.addOutcome = addOutcomeSaved
		self.log.info('--- end of validate output')
		self.addOutcome(PASSED, override=True) # reset outcome before real validations
		
		self.log.info('Outcome reasons were: \n  %s\n', '\n  '.join(recordedOutcomes))
		self.assertThat('outcomes == expected', outcomes = recordedOutcomes, expected=[
			'TIMED OUT: JUnit error: java.util.concurrent.TimeoutException: shouldTimeout() timed out after 10 milliseconds [in myorg.mytest.JUnit5Tests.shouldTimeout()] ; callRecord=fullpath/JUnit5Tests.java:29', 
			'BLOCKED: JUnit error: java.lang.Exception: Bad test [in myorg.mytest.JUnit5Tests$NestedParent.shouldError()] ; callRecord=fullpath/JUnit5Tests.java:43',
			'FAILED: Assert that (expected == actual) with expected="Hello world", actual="Hello funky world", testcaseName="myorg.mytest.JUnit5Tests$NestedParent.shouldFail()" ; callRecord=None', 
			'BLOCKED: JUnit error: java.lang.Exception: This is a test error [in myorg.mytest.JUnit4Tests.shouldError] ; callRecord=fullpath/JUnit4Tests.java:23', 
			'FAILED: Assert that (expected == actual) with expected="Hello []world", actual="Hello [funky ]world", testcaseName="myorg.mytest.JUnit4Tests.shouldFail" ; callRecord=None'		
		])
	
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
			self.assertThat('now-60*30 < timestamp <= now', timestamp=suite['timestamp'], now=time.time(), f=f)
			
			# strip out the bits that might change
			for k in ['timestamp', 'durationSecs', 'hostname']:
				if suite.get(k) or suite.get(k)==0.0: suite[k] = '<removed>'
			for r in results:
				for k in ['outcomeDetailsFull', 'durationSecs']:
					if r.get(k) or r.get(k)==0.0: r[k] = '<removed>'
		self.assertDiff(
			self.write_text('parsed_junit_xml.json', json.dumps(parsed, indent='  ', sort_keys=True)) )
