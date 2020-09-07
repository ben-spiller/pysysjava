package myorg.myserver;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.*;

@Disabled("this whole suite is disabled")
class MySkippedSuiteTests {

    //private final Calculator calculator = new Calculator();
    
    // TODO: make parallel execution work

    //@Test
    @RepeatedTest(value = 3, name = "XXX {displayName} {currentRepetition}/{totalRepetitions}")
	@DisplayName("My display name")
	@Tag("my-test-tag")
    void addition() throws Exception {
		System.out.println("Some stdout from addition()");
		System.out.println("Some more stdout from addition()");
		System.err.println("Some stderr from addition()");
        assertEquals(2, 2);
    }

	@Test
	@Timeout(value = 100, unit = java.util.concurrent.TimeUnit.MILLISECONDS)
	void shouldTimeout()throws Exception {
		Thread.sleep(10000);
	}
		
	@Nested
	@DisplayName("parent of nested relationship")
	class NestedParent
	{
		@Test
		void shouldFail()throws Exception {
        Thread.sleep(1000);
			assertEquals("Hello world", "Hello funky world");
		}

		@Test
		void shouldError()throws Exception {
			throw new Exception("Bad test");
		}


		@Test
		@Disabled("for demonstration purposes")
		void shouldBeSkipped() {
			assertEquals("Hello world", "Hello funky world");
		}

	}
}

