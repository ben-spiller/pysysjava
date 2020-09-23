"""
Support for reading the Ant-style XML files often used for report JUnit results (and also for some non-JUnit test 
execution engines). 

"""

import pysys
from pysys.constants import *
from pysys.utils.fileutils import *

import logging
import calendar
import xml.etree.ElementTree as ET # Python 3.3+ will automatically use the fast C version if available

log = logging.getLogger('pysys.java.junitxml')

class JUnitXMLParser:
	""" A fast, minimal parser for Ant-style JUnit XML files.
	
	Note that there are a number of dialects of this file format with different handling of things like stdout 
	(per testsuite or per testcase) and timezone (UTC or local timezone) so check the details carefully if using 
	this for anything other than the JUnit 5 console launcher. If you need something more advanced there are 
	other Python-based JUnit XML parsers out there with more features."""
	
	outcomeDetailsExcludeLinesRegex = r'^\t+(at (java[.]|sun[.]|org[.]junit|org.apache.tools.ant)|\.\.\. [0-9]+ more).*\n'
	"""
	A regular expression specifying lines that should be stripped out of the outcomeDetails stack traces. 
	"""
	
	isTimestampLocalTime = None
	"""
	Set to True to force timestamp to be interpreted as local time (like JUnit5), 
	or False to force to interpret as UTC/GMT (like Ant). Default is to select based on test suite name. 
	
	"""
	
	def __init__(self, path):
		self.path = os.path.normpath(path)
		
		# This approach allows subclasses to extend if they want to, and is also very efficient
		self.unmarshaller = {
			'testsuite': self._testsuite,
			'testcase': self._testcase,
			'system-out': self._systemOut,
			'system-err': self._systemErr,
			'failure': self._outcome,
			'error': self._outcome,
			'skipped': self._outcome,
		}

	def parse(self):
		"""
		Parses this file and returns a tuple of (testsuite: dict[str,obj], testcases: list[dict[str,obj]]) 
		representing the contents of this file. 
		
		The testsuite dictionary contains keys:
		
			* ``tests: int`` - total number of tests executed (depending on the dialect of the file format this may or 
			  may not include skipped tests). 
			* ``durationSecs: float`` - The time elapsed while executing all tests.
			* ``timestamp: float`` - The start time as a POSIX timestamp which can be passed to datetime.fromtimestamp(). 
			* ``stdout: str`` (optional) - Any text written to stdout by all testcases in the suite 
			  for dialects such as Ant which don't provide this per-testcase. (stripped of leading/trailing whitespace) 
			* ``stderr: str`` (optional) - Any text written to stderr by all testcases in the suite 
			  for dialects such as Ant which don't provide this per-testcase. (stripped of leading/trailing whitespace) 
			* other keys vary depending on the dialect

		Each testcase dictionary contains keys:
		
			* ``classname: str`` - The qualified class name containing this testcase. May include $ if has a nested 
			  class. 
			* ``name: str`` - The name of the testcase, typically a method name possibly with a suffix e.g. ``foo()[2]``.
			* ``durationSecs: float`` - The time taken to execute this testcase. 			
			* ``stdout: str`` (optional)  - Any text written to stdout by the testcase (stripped of leading/trailing whitespace), 
			  for dialects such as JUnit5 console launcher that provide this per testcase.
			* ``stderr: str`` (optional) - Any text written to stderr by the testcase (stripped of leading/trailing whitespace), 
			  for dialects such as JUnit5 console launcher that provide this per testcase
			* ``outcome: str`` - passed/failure/error/skipped. 
			* ``outcomeType: str`` (optional) - Java class of the outcome type, if present. 
			* ``outcomeReason: str`` (except if test passed) - reason string or '' if not known. 
			* ``outcomeDetails: str`` (optional) - multi-line details string for the outcome, typically a stack trace. 
			  To avoid excessive verbosity lines involving org.junit.* or java.* packages are excluded. 		
			* ``outcomeDetailsFull: str`` (optional) - multi-line details string for the outcome, without exclusions. 	
			* ``comparisonExpected/comparisonActual: str`` (optional) - actual and expected comparison values from the outcomeReason, if known. 		"""
		
		log.debug('Parsing JUnitXML: %s', self.path)
		
		self.results = []
		self.suite = {}
		self.currenttest = {}
		unmarshaller = self.unmarshaller
		try:
			with open(toLongPathSafe(self.path), 'rb') as fileptr:
				nodepath = []
				for action, elem in ET.iterparse(fileptr, events=['start','end']):
					if action =='start':
						nodepath.append(elem.tag)
					else:
						u = unmarshaller.get(elem.tag)
						if u is not None: u(elem, nodepath)
						nodepath.pop()
			
			# This check is to make sure we've not missed anything while parsing; 
			# note that Ant seems to set tests to the total excluding skipped ones whereas JUnit5 launcher includes 
			# skipped ones; hence not doing an exact check here
			assert len(self.results) >= self.suite['tests'], 'Suite contains %d tests but found %d testcase elements'%(
				self.suite['tests'], len(self.results))
		except Exception as ex: # pragma: no cover
			raise Exception('Failed to parse JUnit XML %s: %s'%(self.path, ex))
		# The order seems to be random, so sort it
		self.results.sort(key=lambda r: (r.get('classname'), r.get('name')))
		
		if len(self.results)==0:
			if 'uniqueId' in self.suite:
				# e.g. if you have JUnit 5 but not JUnit 4 (or vice-versa) you'll get an empty file; the above is a 
				# a way to detect that the suite is from the JUnit5 launcher rather than an actual Ant/JUnit4 test class/suite
				log.debug('Ignoring suite "%s" with no results generated by the JUnit5 launcher', self.suite.get('name'))
			else:
				assert self.suite.get('skipped') >= 1, 'Test suite "%s" contains no results, but skipped=0: %s'%(self.suite.get('name'), self.path)
				# Create a fake result so that it shows up. NB: JUnit 5 always generates a result so this is just for JUnit 4 and/or Ant
				self.results.append({
					"classname": self.suite['name'],
					"durationSecs": 0.0,
					"name": "class",
					"outcome": "skipped",
					"outcomeReason": "Test suite is skipped",
				})
					
		return self.suite, self.results

	def _testsuite(self, elem, nodepath):
		assert len(nodepath)==1, 'Only expecting testsuite elements as the root node, but got: %s'%nodepath
		self.suite.update(elem.attrib)

		# overwrite some with more specific values
		for k in ['tests', 'failures', 'errors', 'skipped', 'aborted']: # errors vs aborted are used in different dialects
			if k in self.suite: self.suite[k] = int(elem.attrib[k])
		self.suite['durationSecs'] = float(self.suite.pop('time', '0'))
		
		if self.isTimestampLocalTime is None:
			self.isTimestampLocalTime = self.suite.get('name') in ['JUnit Jupiter', 'JUnit Vintage']
		self.suite['timestamp'] = (time.mktime if self.isTimestampLocalTime else calendar.timegm)(time.strptime(elem.attrib['timestamp'], '%Y-%m-%dT%H:%M:%S'))

	def _testcase(self, elem, nodepath):
		currenttest = self.currenttest
		
		currenttest['name'] = elem.attrib.get('name')
		currenttest['classname'] = elem.attrib.get('classname')
		currenttest['durationSecs'] = float(elem.attrib.get('time') or '0')
		
		# Now we know the classname try to find the line in the stack trace from that class
		classnameUnqualified = (currenttest['classname'] or '').split('.')[-1].split('$')[0]
		for l in currenttest.get('outcomeDetails', '').split('\n'):
			m = re.match(r'[ \t]+at .*[(]%s[^:]*:([0-9]+)'%classnameUnqualified, l)
			if m is not None:
				currenttest['testFileLine'] = int(m.group(1))
				break
		
		currenttest.setdefault('outcome', 'passed')
		
		self.results.append(currenttest)
		self.currenttest = {}

	def _systemErr(self, elem, nodepath):
		text = elem.text.strip()
		if not text: return
		
		item = self.suite if nodepath[-2]=='testsuite' else self.currenttest
		
		if 'stderr' in item: text = item['stderr']+'\n'+text
		item['stderr'] = text

	def _systemOut(self, elem, nodepath):
		text = elem.text.strip()
		if not text: return

		item = self.suite if nodepath[-2]=='testsuite' else self.currenttest

		# instead of real system output it could contain special output from the JUnit 5 Jupiter engine
		m = re.match('unique-id: (.*)\ndisplay-name: (.+)', text, flags=re.MULTILINE)
		if m:
			item['uniqueId'] = m.group(1)
			item['displayName'] = m.group(2)
			return


		if 'stdout' in item: text = item['stdout']+'\n'+text
		item['stdout'] = text

	def _outcome(self, elem, nodepath):
		t = self.currenttest
		t['outcome'] = elem.tag
		if elem.attrib.get('type'): t['outcomeType'] = elem.attrib['type']

		if elem.attrib.get('message'): 
			t['outcomeReason'] = elem.attrib['message'].strip()
			
			m = re.match('expected: ?<(.*)> but was: ?<(.*)>$', t['outcomeReason'])
			if m is not None and m.group(1)!=m.group(2):
				t['comparisonExpected'], t['comparisonActual'] = m.group(1), m.group(2)
			
			if t['outcome'] == 'error' and t.get('outcomeType') and t['outcomeType'] not in t['outcomeReason']:
				t['outcomeReason'] = '%s: %s'%(t['outcomeType'], t['outcomeReason'])
			
			if elem.text:
				details = elem.text.lstrip()
				if details:
					t['outcomeDetailsFull'] = details
					t['outcomeDetails'] = re.sub(self.outcomeDetailsExcludeLinesRegex, '', details, flags=re.MULTILINE).strip()
		else:
			t['outcomeReason'] = elem.text.strip()
		