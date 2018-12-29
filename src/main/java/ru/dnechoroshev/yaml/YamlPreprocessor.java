package ru.dnechoroshev.yaml;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Scanner;

import ru.dnechoroshev.yaml.model.PropertyStatus;

public class YamlPreprocessor {	
	
	public static void main(String[] args) {
		try {
			//Scanner scanner = new Scanner(new File("D:\\Temp\\group_vars\\app_server_segment2\\test.yml"));
			Scanner scanner = new Scanner(new File("c:\\tmp\\test.yml"));
			YamlText yText = new YamlText(scanner);
			scanner.close();
			Map<String,Object> resultList = new LinkedHashMap<>();			
			int rootLevel = yText.getNextLevel();			
			Map<String,Object> element = null;			
			while((element = getElement(yText, rootLevel))!=null){
				resultList.put((String)element.get("__id__"), element);
				element.remove("__id__");
			}
			
			System.out.println(resultList);
						
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
	}
	
	private static Map<String,Object> getElement(YamlText text,int level){		 
		if(!text.seekNextElement(level)){
			return null;
		}	
		
		PropertyStatus status = text.checkPropertyStatus();		
		switch(status) {			
			case SIMPLE: {
				return text.getProperty();
			}
			case COMPLEX: {
				Map<String,Object> result = new LinkedHashMap<>();				
				String name = text.getElementName();
				name = name + "";
				result.put("__id__", text.getElementName());
				result.put("__comments__", text.getComments());
				result.put("__level__", text.getLevel());
				int nextLevel = text.getNextLevel();
				if(nextLevel>level){
					Map<String,Object> element = null;
					while((element = getElement(text, nextLevel))!=null){
						print(element);
						result.put((String)element.get("__id__"), element);
						element.remove("__id__");
					}
				}
				return result;
			}
			default: {
				return null;
			}
		}		
	}
	
	private static void print(Map<String,Object> m){
		for(Entry<String,Object> e : m.entrySet()){
			System.out.println(e.getKey()+" -> "+e.getValue());			
		}
		System.out.println("-------------------------------");
	}
	
}
