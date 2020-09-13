package myorg.mytest2;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.*;

class TestSuite2 {

	@Test
	@Tag("my-tag2")
	void shouldPass2() throws Exception {
	}

	@Test
	@Tag("my-tag2")
	@Tag("my-tag-disabled")
	@Disabled("Reason test is disabled goes here")
	void shouldBeSkipped2() {
		assertEquals("Hello world", "Hello funky world");
	}
}

