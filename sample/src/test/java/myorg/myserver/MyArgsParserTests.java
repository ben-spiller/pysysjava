package myorg.myserver;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.FileWriter;

import org.junit.jupiter.api.*;

import myorg.myserver.MyArgsParser.Config;

/** JUnit 5 tests for the MyArgsParser class.
 *
 * This class writes some temporary files to the current directory it's run from 
 * (which if it's executed from PySys is completely safe as it'll be automatically cleaned)
 */
class MyArgsParserTests {
	private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(MyServer.class);

	@Test
	void invalidPortValueThrows() throws Exception {
		assertThrows(IllegalArgumentException.class, () -> MyArgsParser.parseArgs(new String[] {"--port", "-100"}));
	}

	@Test
	void invalidArgumentThrows() throws Exception {
		assertThrows(IllegalArgumentException.class, () -> MyArgsParser.parseArgs(new String[] {"--some-invalid-arg"}));
	}
	
	@Test
	void logLevelIsNormalized() throws Exception {
		log.info("About to check that the log level can be parsed correctly");
		assertEquals("DEBUG", MyArgsParser.parseArgs(new String[] {"--port", "124", "--loglevel", "dEbug"}).loglevel);
	}
	
	@Nested
	@DisplayName("Config file parser")
	@Tag("config-files")
	class ConfigFileParser
	{
		@Test
		@DisplayName("handles the port value")
		void port() throws Exception {
			try (FileWriter fw = new FileWriter("testfile.tmp.properties"))
			{
				fw.write("port=1234");
			}
			Config c = new Config();
			MyArgsParser.parseConfigFile("testfile.tmp.properties", c);
			assertEquals(1234, c.port);
		}

		@Test
		@DisplayName("handles the loglevel value")
		void loglevel() throws Exception {
			try (FileWriter fw = new FileWriter("testfile.tmp.properties"))
			{
				fw.write("loglevel=DEBUG");
			}
			Config c = new Config();
			MyArgsParser.parseConfigFile("testfile.tmp.properties", c);
			assertEquals("DEBUG", c.loglevel);
		}
		
		@Test
		@DisplayName("throws an exception when given an invalid key")
		void invalidKey() throws Exception {
			try (FileWriter fw = new FileWriter("testfile.tmp.properties"))
			{
				fw.write("invalidkey=123");
			}
			Config c = new Config();
			assertThrows(IllegalArgumentException.class, () -> MyArgsParser.parseConfigFile("testfile.tmp.properties", c));
		}
	}
}

