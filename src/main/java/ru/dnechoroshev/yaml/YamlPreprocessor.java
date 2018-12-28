package ru.dnechoroshev.yaml;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.lang3.StringUtils;

import ru.dnechoroshev.yaml.model.Annotation;
import ru.dnechoroshev.yaml.model.PropertyStatus;

public class YamlPreprocessor {
	
	static Pattern propertyPattern = Pattern.compile("^[a-zA-Z0-9\\-_]+:");
	
	public static void main(String[] args) {
		try {
			//Scanner scanner = new Scanner(new File("D:\\Temp\\group_vars\\app_server_segment2\\test.yml"));
			Scanner scanner = new Scanner(new File("c:\\tmp\\test.yml"));
			Map<String,Object> resultList = new LinkedHashMap<>();
			while (scanner.hasNextLine()) {
				String s = scanner.nextLine();
				if (!checkPropertyStatus(s).equals(PropertyStatus.NONE))
					resultList.putAll(readProperty(scanner,s,0));				
			}
			scanner.close();
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
	}
	
	private static Map<String,Object> readProperty(Scanner scanner,String line,int level){		 
		PropertyStatus status = checkPropertyStatus(line); 
		Map<String,Object> result = new HashMap<String,Object>();
		switch(status) {
			case NONE: {				
				return null;
			}
			case SIMPLE: {
				return getProperty(line);
			}
			case COMPLEX: {
				if(scanner.hasNextLine()) {
					while(scanner.hasNextLine()){
						String newProperty = scanner.nextLine();
						if(!checkPropertyStatus(newProperty).equals(PropertyStatus.NONE)){
							if(getLevel(newProperty)>level){
								result.put(getPropertyName(line), readProperty(scanner,newProperty,getLevel(newProperty)));
							}else{
								return result;
							}
						}
					}
					
					
					
					
				}else {
					result.put(getPropertyName(line), null);
				}
			}
		}
		return result;
	}
	
	private static int getLevel(String s) {
		return s.indexOf(s.trim());
	}
	
	private static boolean isAnnotation(String s) {
		return s.trim().startsWith("#@");
	}
	
	private static Annotation getAnnotation(String s) {
		String[] aValues = s.replace("#@", "").split("=");
		return new Annotation(aValues[0].trim(), aValues[1].trim());
	}
	
	private static PropertyStatus checkPropertyStatus(String s) {
		if((s==null)||(s.trim().isEmpty())||s.trim().startsWith("#")) {
			return PropertyStatus.NONE;
		}
		if(s.trim().matches("^[a-zA-Z0-9\\-_]+:(.)*")) {
			if(s.trim().endsWith(":")) {
				return PropertyStatus.COMPLEX;
			}else {
				return PropertyStatus.SIMPLE;
			}
		}
		return PropertyStatus.NONE;
	}
	
	private static String getPropertyName(String s) {
		return StringUtils.chop(s);
	}
	
	private static Map<String,Object> getProperty(String s) {
		Matcher m = propertyPattern.matcher(s.trim());
		if(m.find()) {
			String propertyName = m.group(0);
			String propertyValue = s.replace(propertyName, "").trim();
			Map<String,Object> prop = new HashMap<>();
			prop.put(propertyName, propertyValue);
			return prop;
		}
		return null;
	}
}
