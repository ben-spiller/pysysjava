package mytest;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;

class JUnit5Tests {

	private static final Logger logger = LoggerFactory.getLogger(JUnit5Tests.class);

	@Test
	void jvmArgSystemProperty() throws Exception {
		logger.info("This is a log message from jvmArgSystemProperty");
		assertEquals(System.getProperty("myJVMArg"), "my value");
	}

	@Test
	void pysysModeAsSystemProperty() throws Exception {
		logger.info("This is a log message from pysysModeAsSystemProperty");
		assertEquals(System.getProperty("pysys.mode"), "MyPySysMode");
	}

	@Test
	void standardSystemProperties() throws Exception {
		assertTrue(new File(System.getProperty("pysys.input")).exists(), "pysys.input exists");
		assertTrue(new File(System.getProperty("pysys.project.testRootDir")).exists(), "pysys.project.testRootDir exists");
	}
}

