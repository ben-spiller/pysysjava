package myorg.mytest;

import org.junit.*;

/**
	Some JUnit 4 tests
*/
public class JUnit4Tests {

    @Test
    public void shouldpass() throws Exception {
		System.out.println("Some stdout from shouldPass");
        Assert.assertEquals(2, 2);
    }

	@Test
	public void shouldFail() throws Exception {
		Assert.assertEquals("Hello world", "Hello funky world");
	}

	@Test
	public void shouldError() throws Exception {
		throw new Exception("This is a test error");
	}
	
	@Test
	@Ignore("Reason test is ignored goes here")
	public void shouldBeSkipped() {
		Assert.assertEquals("Hello world", "Hello funky world");
	}

}

