package myorg.myserver;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.*;

class MyServerTests2 {

    //private final Calculator calculator = new Calculator();
    
    // TODO: make parallel execution work

    //@Test
    @Test
	@DisplayName("My display name2")
	@Tag("my-test-tag2")
    void addition() throws Exception {
		System.out.println("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxx Some stdout from addition()");
        Thread.sleep(1000);
    }

	@Nested
	@DisplayName("parent of nested relationshipX")
	class NestedParent
	{
		@Test
		void shouldFail() throws Exception {
        Thread.sleep(1000);
			assertEquals("Hello world", "Hello funky world");
		}


		@Test
		@Disabled("for demonstration purposes")
		void shouldBeSkipped() {
			assertEquals("Hello world", "Hello funky world");
		}

	}
}

