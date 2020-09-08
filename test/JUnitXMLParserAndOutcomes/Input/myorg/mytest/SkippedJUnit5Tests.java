package myorg.mytest;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.*;

@Disabled("This whole suite is disabled")
public class SkippedJUnit5Tests {

	@Test
	void shouldBeSkipped() throws Exception {
		throw new Exception("Should not happen");
	}
		
	@Nested
	@DisplayName("NestedParent")
	class NestedParent
	{
		@Test
		void shouldBeSkippedNested() throws Exception {
			throw new Exception("Should not happen");
		}
	}
}

