import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		# The logging jars in this directory are used throughout this test, so rather than pass this argument to 
		# each compile() and startJava() we can 
		self.java.defaultClasspath.append(self.project.appHome+'/dependency-jars/*.jar')

		# Compile a small tool used by this test from the Input/ directory, and add it to the default classpath
		self.java.compile(self.input, output=self.output+'/javaclasses', arguments=['-Werror'])
		self.java.defaultClasspath.append(self.output+'/javaclasses')
	
		# Although in this case we have an executable jar this example shows how we could launch it if we wanted to 
		# execute a specific class from the jar instead
		port = self.getNextAvailableTCPPort()
		server1 = self.java.startJava(
			'myorg.myserver.MyServer',
			classpath=[self.project.appHome+'/my-server*.jar'], # Not using the default classpath here
			arguments=['--port', str(port), ], 
			jvmProps={'log4j.configurationFile': self.project.testLogConfigURL},
			
			# Usually you will want to capture process stdout and stderr. The stdouterr specifies a prefix onto which 
			# PySys will append .out or .err for this process's output. Be sure not to reuse the filename in this test
			stdouterr='my_server1', 
			
			# It's good practice to set a displayName for use in log and error messages (startJava will automatically 
			# provide one based on the stdouterr name if this argument isn't given)
			displayName='my_server1<port %s>'%port, 
			
			# The info dictionary allows us to stash useful info such as port numbers in the Process object
			info={'port':port},
			
			background=True)
		
		# To make the test easier to debug, register a function that will log any lines from the server's stderr during 
		# this test's cleanup phase (i.e. after validate), in case there were any errors from the server
		self.addCleanupFunction(lambda: self.logFileContents(server1.stderr))
		
		# Although all processes are automatically killed by PySys during cleanup, it's beneficial to perform 
		# a clean shutdown first as the code coverage tools only generate output during a graceful shutdown
		self.addCleanupFunction(lambda: [
			self.java.startJava('HttpGetTool', [f'http://127.0.0.1:{server1.info["port"]}/shutdown'], 
				stdouterr=self.allocateUniqueStdOutErr('my_server1_shudown'), displayName='my_server1 clean shutdown', ignoreExitStatus=True), 
			server1.wait(TIMEOUTS['WaitForProcessStop'])] if server1.running() else None)
		
		# A common way to wait for a server to start is by by polling for a grep regular expression. The 
		# errorExpr/process arguments ensure we abort with a really informative message if the server fails to start
		self.waitForGrep('my_server1.out', 'Started MyServer .*on port .*', errorExpr=[' (ERROR|FATAL) '], process=server1) 
		
		self.log.info('')
		
		# Run our test tool to check it's servicing requests properly
		self.java.startJava('HttpGetTool', arguments=[f'http://127.0.0.1:{server1.info["port"]}/sensorValues'], 
			stdouterr="httpget_check_connection", timeout=60)

		# Test error case of server startup
		self.java.startJava(
			self.project.appHome+'/my-server*.jar', 
			arguments=['--port', '-1'], 
			jvmProps={'log4j.configurationFile': self.project.testLogConfigURL},
			stdouterr="my_server_invalid_port", 
			expectedExitStatus="== 123")

	def validate(self):	
		self.assertGrep('my_server1.out', r' (ERROR|FATAL|WARN) .*', contains=False)

		self.assertThatGrep('my_server_invalid_port.out', r' ERROR +(.*)', "value == expected", 
			expected="Server failed: Invalid port number specified: -1")
