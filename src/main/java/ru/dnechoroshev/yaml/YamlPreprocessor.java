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
			while((readElement(yText, rootLevel,resultList))){
				//resultList.put((String)element.get("__id__"), element);
				//element.remove("__id__");
			}
			
			System.out.println(resultList);
						
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
	}
	
	private static boolean readElement(YamlText text,int level,Map<String,Object> parent){		 
		if(!text.seekNextElement(level)){
			return false;
		}		
				
		PropertyStatus status = text.checkPropertyStatus();		
		switch(status) {			
			case SIMPLE: {
				Map<String,Object> property = text.getProperty();
				parent.put((String)property.get("__id__"), property);
				property.remove("__id__");			
				return true;
								
			}
			case MAP: {
				String name = text.getElementName();
				
				Map<String,Object> result = new LinkedHashMap<>();									
				result.put("__comments__", text.getComments());
				result.put("__level__", text.getLevel());
				result.put("__annotations__", text.getAnnotations());
				
				parent.put(text.getElementName(), result);
				
				int nextLevel = text.getNextLevel();
				if(nextLevel>level){					
					while((readElement(text, nextLevel,result))){
						print(result);					
					}
				}
				return true;
			}
			case LISTELEMENT: {
				
				if(parent.get("__list__")==null){
					parent.put("__list__", new ArrayList<Map<String,Object>>());						
				}
				
				@SuppressWarnings("unchecked")
				List<Map<String,Object>> parentList = (List<Map<String,Object>>)parent.get("__list__");								
				
				do {
					String name = text.getElementName();
	
					Map<String, Object> result = new LinkedHashMap<>();
					result.put("__comments__", text.getComments());
					result.put("__level__", text.getLevel());
					result.put("__annotations__", text.getAnnotations());
					result.put(text.getElementName(), text.getProperty());
	
					parentList.add(result);
					
					int nextLevel = text.getNextLevel();
					if (nextLevel > level) {
						while ((readElement(text, nextLevel, result))) {
							print(result);
						}
					}
				} while (text.seekNextElement(level));
				
				return true;
			}
			default: {
				return false;
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
