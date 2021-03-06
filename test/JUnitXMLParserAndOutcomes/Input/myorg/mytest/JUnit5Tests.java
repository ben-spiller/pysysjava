package myorg.mytest;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.*;

/** A class demonstrating the main possible test types and outcomes in JUnit5, including:
	repeated, nested, customized displayname.
*/
class JUnit5Tests {

	@RepeatedTest(value = 3, name = "MyRepeatedTest {displayName} {currentRepetition}/{totalRepetitions}")
	@DisplayName("My display name")
	@Tag("my-test-tag")
	void shouldPass() throws Exception {
		System.out.println("Some stdout from shouldPass XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX");
		System.err.println("Some stderr from shouldPass");
		System.out.println("Some more stdout from shouldPass");
		assertEquals(2, 2);
	}

	@Test
	@Timeout(value = 10, unit = java.util.concurrent.TimeUnit.MILLISECONDS)
	void shouldTimeout() throws Exception {
		System.out.println("Some stdout from shouldTimeout XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX");
		System.err.println("Some stderr from shouldTimeout");
		System.out.println("Some more stdout from shouldTimeout");

		Thread.sleep(10000);
	}
		
	@Nested
	@DisplayName("Parent display name")
	class NestedParent
	{
		@Test
		void shouldFail() throws Exception {
			assertEquals("Hello world", "Hello funky world");
		}

		@Test
		void shouldError() throws Exception {
			throw new Exception("Bad test");
		}


		@Test
		@Disabled("Reason test is disabled goes here")
		void shouldBeSkipped() {
			assertEquals("Hello world", "Hello funky world");
		}

	}
}

