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
	public void shouldpass2() throws Exception {
		Assert.assertEquals("Hello world", "Hello world");
	}
	
	@Test
	@Ignore("Reason test is ignored goes here")
	public void shouldBeSkipped() {
		Assert.assertEquals("Hello world", "Hello funky world");
	}

}

