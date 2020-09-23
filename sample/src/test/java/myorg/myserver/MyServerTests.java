package myorg.myserver;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.FileWriter;

import org.junit.jupiter.api.*;

import myorg.myserver.MyArgsParser.Config;

/** JUnit 5 tests for the MyServer class. Shown here as a demonstration of skipping tests.
 */
@Disabled("Not yet implemented this JUnit test suite yet")
class MyServerTests {

	@Test
	@Timeout(value = 60, unit = java.util.concurrent.TimeUnit.SECONDS)
	void handlesSensorValues() throws Exception {

	}
}

