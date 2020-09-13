package myorg.mytest1;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.*;

class TestSuite1 {

	@Test
	@Tag("my-tag1")
	void shouldPass() throws Exception {
	}

	@Test
	@Tag("my-tag1")
	@Tag("my-tag-disabled")
	@Disabled("Reason test is disabled goes here")
	void shouldBeSkipped() {
		assertEquals("Hello world", "Hello funky world");
	}
}

