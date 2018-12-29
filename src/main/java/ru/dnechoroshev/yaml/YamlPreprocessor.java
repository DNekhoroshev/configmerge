package ru.dnechoroshev.yaml;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Scanner;

import ru.dnechoroshev.yaml.model.PropertyStatus;

public class YamlPreprocessor {	
	
	public static void main(String[] args) {
		try {
			//Scanner scanner = new Scanner(new File("D:\\Temp\\group_vars\\app_server_segment2\\test.yml"));
			Scanner scanner = new Scanner(new File("c:\\tmp\\test.yml"));
			//Scanner scanner = new Scanner(new File("C:\\Users\\DNekhoroshev\\git\\configuration.dev1\\group_vars\\mq\\ibm-mq-qmgrs.yml"));
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
			case MAP: {
				Map<String,Object> result = new LinkedHashMap<>();				
				String name = text.getElementName();
				name = name + "";
				result.put("__id__", text.getElementName());
				result.put("__comments__", text.getComments());
				result.put("__level__", text.getLevel());
				result.put("__annotations__", text.getAnnotations());
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
			case LIST: {
				Map<String,Object> result = new LinkedHashMap<>();				
				String name = text.getElementName();
				name = name + "";
				result.put("__id__", text.getElementName());
				result.put("__comments__", text.getComments());
				result.put("__level__", text.getLevel());
				result.put("__annotations__", text.getAnnotations());
				result.put("__list__", new ArrayList<Map<String,Object>>());
				return result;
			}
			default: {
				return null;
			}
		}		
	}
	
	private static List<Map<String,Object>> getList(YamlText text, int level){
		List<Map<String,Object>> result = new ArrayList<>();			
			 
		Map<String,Object> element = null;
		Map<String,Object> listElement = null;
		while(text.getLevel()>=level){			
			if(text.getLevel()==level){
				//Starts next list element
				listElement = new LinkedHashMap<>();				
				result.add(listElement);				 
			}
			element = getElement(text, text.getLevel());
			listElement.put((String)element.get("__id__"), element);
			
		}
		
		return result;
		
	}
	
	
	private static void print(Map<String,Object> m){
		for(Entry<String,Object> e : m.entrySet()){
			System.out.println(e.getKey()+" -> "+e.getValue());			
		}
		System.out.println("-------------------------------");
	}
	
}
