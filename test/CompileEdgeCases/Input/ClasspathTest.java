public class ClasspathTest
{
	public static void main(String[] args)
	{
		// just to check we have it on the classpath
		org.slf4j.LoggerFactory.getLogger("foo");
	}
}