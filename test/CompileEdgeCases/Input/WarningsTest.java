import java.util.List;

public class WarningsTest
{
	private String unused1;
	private String unused2;
	
	public static void main(String[] args)
	{
		List<String> list = null;
		List raw = list;
		
		List raw2 = list;
	}
}