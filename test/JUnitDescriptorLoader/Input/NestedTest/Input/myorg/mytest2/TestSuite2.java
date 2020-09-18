package myorg.mytest2;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.*;

class TestSuite2 {

	@Test
	@Tag("my-tag2")
	void shouldPass2() throws Exception {
	}

	@Nested
	public class NestedClass
	{
		@Test
		@Tag("my-tag2")
		void shouldPassNested() throws Exception {
		}
	}

}

