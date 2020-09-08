package myorg.mytest;

import org.junit.*;

@Ignore("This whole suite is ignored")
public class SkippedJUnit4Tests {

	@Test
	void shouldFail() throws Exception {
		throw new Exception("Should be ignored");
	}
}

