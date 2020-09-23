package myorg.myserver;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.Locale;
import java.util.Map;
import java.util.Properties;

class MyArgsParser
{

	static class Config 
	{
		int port;
		String loglevel;
	}

	static final String USAGE = "Usage: java -jar my-server.jar [--port INT] [--loglevel INFO/DEBUG] [--configfile PROPERTIES_FILE]";
	
	static void parseConfigFile(String path, Config c) throws IOException
	{
		Properties p = new Properties();
		try (FileInputStream fis = new FileInputStream(new File(path)))
		{
			p.load(fis);
		}
		for (Map.Entry<Object,Object> e: p.entrySet())
		{
			switch (e.getKey().toString())
			{
			case "port": c.port = Integer.parseInt(e.getValue().toString()); break;
			case "loglevel": c.loglevel = e.getValue().toString(); break;
			default: throw new IllegalArgumentException("Unknown server property: '"+e.getKey()+"'");
			}
			
		}
	}

	static Config parseArgs(String[] args) throws IOException
	{
		Config c = new Config();
		int i = 0;
		while (i<args.length)
		{
			switch(args[i])
			{
			case "--help": 
				System.out.println(USAGE);
				System.exit(0);
				break;
			case "--port": c.port = Integer.parseInt(args[++i]); break;
			case "--loglevel": c.loglevel = args[++i].toUpperCase(Locale.ENGLISH); break;
			case "--configfile": parseConfigFile(args[++i], c); break;
			default:
				throw new IllegalArgumentException("Unexpected argument: '"+args[i]+"'");
			}
			i++;
		}
		if (c.port <= 0) throw new IllegalArgumentException("Invalid port number specified: "+c.port);
		
		return c;
	}
	
}
