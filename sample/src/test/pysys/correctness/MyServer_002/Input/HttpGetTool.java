import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * A simple test tool that performs an HTTP GET and returns the result.
 */
public class HttpGetTool
{
	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(HttpGetTool.class);

	public static void main(String[] args) throws Exception
	{
		HttpURLConnection httpURLConnection = (HttpURLConnection) new URL(args[0]).openConnection();
		httpURLConnection.setRequestMethod("GET");
		if (httpURLConnection.getResponseCode() != HttpURLConnection.HTTP_OK)
			throw new Exception("Error from HTTP request: " + httpURLConnection.getResponseMessage());

		try (BufferedReader in = new BufferedReader(new InputStreamReader(httpURLConnection.getInputStream(), "UTF-8")))
		{
			String line;
			while ((line = in.readLine()) != null)
			{
				System.out.println(line);
			}
		}
		log.debug("Completed request");
	}

}
