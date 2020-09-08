import pysys
from pysys.constants import *
from pysys.utils.fileutils import *

import calendar
import xml.etree.ElementTree as ET # Python 3.3+ will automatically use the fast C version if available

class JUnitXMLParser:
	""" A fast, minimal parser for Ant-style JUnit XML files."""
	
	outcomeDetailsExcludeLinesRegex = r'^\t+(at (java[.]|sun[.]|org[.]junit)|\.\.\. [0-9]+ more).*\n'
	"""
	A regular expression specifying lines that should be stripped out of the outcomeDetails stack traces. 
	"""
	
	def __init__(self, path):
		self.path = path
		
		# This approach allows subclasses to extend if they want to
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
		
		The testsuite dicionary contains keys:
		
			* ``tests: int`` - total number of tests executed. 
			* ``durationSecs: float`` - The time elapsed while executing all tests.
			* ``timestamp: float`` - The start time as a POSIX timestamp which can be passed to datetime.fromtimestamp(). 

		Each testcase dicionary contains keys:
		
			* ``classname: str`` - The qualified class name containing this testcase. May include $ if has a nested 
			  class. 
			* ``name: str`` - The name of the testcase, typically a method name possibly with a suffix e.g. ``foo()[2]``.
			* ``durationSecs: float`` - The time taken to execute this testcase. 			
			* ``stdout: str`` - Any text written to stdout by the testcase (stripped of leading/trailing whitespace). 			
			* ``stderr: str`` - Any text written to stderr by the testcase (stripped of leading/trailing whitespace). 
			* ``outcome: str`` - passed/failure/error/skipped. 
			* ``outcomeType: str`` (optional) - Java class of the outcome type, if present. 
			* ``outcomeReason: str`` (except if passed) - reason string or '' if not known. 
			* ``outcomeDetails: str`` (optional) - multi-line details string for the outcome, typically a stack trace. 
			  To avoid excessive verbosity lines involving org.junit.* or java.* packages are excluded. 		
			* ``outcomeDetailsFull: str`` (optional) - multi-line details string for the outcome, without exclusions. 	
			* ``comparisonExpected/comparisonActual: str`` (optional) - actual and expected comparison values from the outcomeReason, if known. 		"""
		self.results = []
		self.suite = {}
		self.currenttest = {}
		unmarshaller = self.unmarshaller
		with open(toLongPathSafe(self.path), 'rb') as fileptr:
			for action, elem in ET.iterparse(fileptr):
				u = unmarshaller.get(elem.tag)
				if u is not None: u(elem)
		
		# This check is to make sure we've not missed anything while parsing
		assert self.suite['tests'] == len(self.results), 'Suite contains %d tests but found %d testcase elements'%(
			self.suite['tests'], len(self.results))
		
		# The order seems to be random, so sort it
		self.results.sort(key=lambda r: (r.get('classname'), r.get('name')))
		
		return self.suite, self.results

	def _testsuite(self, elem):
		assert not self.suite, 'Not expecting multiple testsuite elements in a single file'
		self.suite = dict(elem.attrib)

		# overwrite some with more specific values
		for k in ['tests', 'failures', 'errors', 'skipped']:
			if k in self.suite: self.suite[k] = int(elem.attrib[k])
		self.suite['durationSecs'] = float(self.suite.pop('time', '0'))
		self.suite['timestamp'] = time.mktime(time.strptime(elem.attrib['timestamp'], '%Y-%m-%dT%H:%M:%S'))

	def _testcase(self, elem):
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

	def _systemErr(self, elem):
		text = elem.text.strip()
		if not text: return
		if 'stderr' in self.currenttest: text = self.currenttest['stderr']+'\n'+text
		self.currenttest['stderr'] = text

	def _systemOut(self, elem):
		text = elem.text.strip()
		if not text: return
		
		# instead of real system output it could contain special output from the JUnit 5 Jupiter engine
		m = re.match('unique-id: (.*)\ndisplay-name: (.+)', text, flags=re.MULTILINE)
		if m:
			self.currenttest['uniqueId'] = m.group(1)
			self.currenttest['displayName'] = m.group(2)
			return

		if 'stdout' in self.currenttest: text = self.currenttest['stdout']+'\n'+text
		self.currenttest['stdout'] = text

	def _outcome(self, elem):
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
			
			details = elem.text.lstrip()
			if details:
				t['outcomeDetailsFull'] = details
				t['outcomeDetails'] = re.sub(self.outcomeDetailsExcludeLinesRegex, '', details, flags=re.MULTILINE).strip()
		else:
			t['outcomeReason'] = elem.text.strip()
		