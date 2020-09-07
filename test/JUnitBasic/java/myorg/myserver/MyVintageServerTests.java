package myorg.myserver;

import org.junit.*;

public class MyVintageServerTests {

    @Test
    public void addition() throws Exception {
		System.out.println("Some stdout from addition()");
        Assert.assertEquals(2, 2);
    }

	@Test
	public void shouldFail() throws Exception {
	Thread.sleep(1000);
		Assert.assertEquals("Hello world", "Hello funky world");
	}

	@Test
	public void shouldError() throws Exception {
	
		throw new Exception("This is a test error");
	}
	@Test
	@Ignore("for demonstration purposes")
	public void shouldBeSkipped() {
		Assert.assertEquals("Hello world", "Hello funky world");
	}

}

