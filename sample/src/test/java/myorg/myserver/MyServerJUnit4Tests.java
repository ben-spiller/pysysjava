package myorg.myserver;

import java.util.regex.Pattern;

import org.junit.*;

/**
 * A short example of some legacy/vintage JUnit 4 tests, which PySys can also run. 
 */
public class MyServerJUnit4Tests {

	@Test
	public void testThatVersionIsValid() throws Exception {
		Assert.assertTrue("Version is of the form digit.digit", 
			Pattern.matches("[0-9]+\\.[0-9]+", MyServer.VERSION));
	}

	@Test
	@Ignore("Not implemented this JUnit 4 test yet")
	public void testThatSensorValuesHandlerWorks() throws Exception {
	}

}

