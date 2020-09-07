package myorg.myserver;

import org.junit.*;

@Ignore("this whole suite is disabled")
class MySkippedVintageTests {

		@Test
		void shouldFail() throws Exception {
			throw new Exception("Should be ignored");
		}
}

