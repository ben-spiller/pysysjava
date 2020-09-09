package myorg.mytest;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.*;

/** A 2nd test class
*/
class JUnit5_2nd_Test {

	@Test
	void shouldpass2() throws Exception {
		assertEquals("Hello world", "Hello world");
	}
}

