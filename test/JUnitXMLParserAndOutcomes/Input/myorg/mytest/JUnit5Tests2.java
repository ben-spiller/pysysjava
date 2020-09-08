package myorg.mytest;

import static org.junit.jupiter.api.Assertions.assertNotEquals;

import org.junit.jupiter.api.*;

/** A 2nd test class
*/
class JUnit5Tests2 {

	@Test
	void shouldFail() throws Exception {
		assertNotEquals("Hello world", "Hello world");
	}
}

