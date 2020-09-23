package myorg.myserver;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Date;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

/**
 * A trivial HTTP REST server providing a REST interface that simulates getting sensor data from some devices. 
 * 
 * To keep things simple, this sample uses no third party libraries other than for logging (this is obviously not 
 * how you'd implement a real server, but the purpose here is to demonstrate the testing not the application).
 */
public class MyServer
{
	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(MyServer.class);

	public static String VERSION = "1.0";
	
	public static void main( String[] args ) throws Exception
	{
		try
		{
			MyArgsParser.Config config = MyArgsParser.parseArgs(args);
			org.apache.logging.log4j.core.config.Configurator.setLevel("myorg", org.apache.logging.log4j.Level.toLevel(config.loglevel));
	
			final com.sun.net.httpserver.HttpServer server = com.sun.net.httpserver.HttpServer.create(new InetSocketAddress("127.0.0.1", config.port), 100);
			server.createContext("/shutdown", new HttpHandler() {
				@Override
				public void handle(HttpExchange e) throws IOException
				{
					log.info("Clean shutdown requested");
					e.sendResponseHeaders(200, 0);
					e.close();
					System.exit(0);
				}
			});
			
			server.createContext("/sensorValues", new GetSensorValuesHandler());
	
			log.debug("Initializing server with args: {}", Arrays.asList(args));
			server.start();
			log.info("Started MyServer v{} on port {}", VERSION, config.port);
		} catch (Exception ex)
		{
			log.error("Server failed: {}", ex.getMessage(), ex);
			System.exit(123);
		}
	}
	
	static class GetSensorValuesHandler implements HttpHandler
	{
		@Override
		public void handle(HttpExchange e) throws IOException
		{
			StringBuilder body = new StringBuilder();
			body.append("{");
			body.append("\"sensorId\": \""+"ABC1234"+"\", ");
			body.append("\"timestamp\": \""+new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'").format(new Date())+"\", ");
			body.append("\"collectionHost\": \""+InetAddress.getLocalHost().getHostName()+"\", ");
			body.append("\"measurements\": [123.4, 670, "+(10/3.0)+", null, 123.4], ");
			body.append("\"measurementTimeSpanSecs\": 2.5, ");
			body.append("\"dataPaths\": \"c:\\devicedata*\\sensor.json\"".replace("\\", "\\\\"));
			body.append("}");
			byte[] bytes = body.toString().getBytes("UTF-8");

			e.sendResponseHeaders(200, bytes.length);
			e.getResponseBody().write(bytes);
			e.getResponseBody().flush();
			
			e.close();
		}
	}
	
}
