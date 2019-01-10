package ru.dnechoroshev.yaml;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Scanner;

import ru.dnechoroshev.yaml.model.Annotation;
import ru.dnechoroshev.yaml.model.PropertyStatus;

public class YamlPreprocessor {	
	
	public static void main(String[] args) throws IOException {
		try {
			//Scanner scanner = new Scanner(new File("D:\\Temp\\group_vars\\app_server_segment2\\test.yml"));
			Scanner scanner = new Scanner(new File("c:\\tmp\\test.yml"));
			//Scanner scanner = new Scanner(new File("C:\\Users\\DNekhoroshev\\git\\configuration.dev1\\group_vars\\mq\\ibm-mq-qmgrs.yml"));
			YamlText yText = new YamlText(scanner);
			scanner.close();
			Map<String,Object> globalResult = new LinkedHashMap<>();			
			int rootLevel = yText.getNextLevel();						
			while((readElement(yText, rootLevel,globalResult))){
				System.out.println("Loaded");
			}
			
			System.out.println(globalResult);
			save(globalResult);
						
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
	}
	
	private static void save(Map<String,Object> yml) throws IOException{
		 String fileName = "c:/tmp/test2.yml";
		 FileWriter fileWriter = new FileWriter(fileName);
		 PrintWriter printWriter = new PrintWriter(fileWriter);
		 StringBuilder result = new StringBuilder("---");
		 for(Entry<String,Object> entry : yml.entrySet()){
			 String propertyName = entry.getKey();
			 Map<String,Object> propertyValue = (Map<String,Object>)entry.getValue();
			 System.out.println(getPropertyValue(propertyValue,false));
		 }
		 System.out.println("************************");
	}
	
	private static String getPropertyValue(Map<String,Object> prop,boolean listElement){
			
		int level = (int)prop.get("__level__"); 
		
		StringBuilder result = new StringBuilder(appendLevel(level)+(listElement?"- ":""));
		
		String id = (String)prop.get("__id__");
		List<String> commentList = (List<String>)prop.get("__comments__");
		String value = (String)prop.get("__value__");
		List<Map<String,Object>> valueList = (List<Map<String,Object>>)prop.get("__list__");
				
		if(value!=null){
			result.append(id+": "+value).append("\n");
		}else if(valueList!=null){
			result.append(id+":").append("\n");
			for(Map<String,Object> val : valueList){
				result.append(getPropertyValue(val,true));
			}
		}else{
			
			if(id!=null)
				result.append(id+":").append("\n");
			for(Entry<String,Object> entry : prop.entrySet()){
				String key = entry.getKey();
								
				switch(key){
					case "__comments__": {
						continue;
					}
					case "__annotations__": { 
						continue;
					}
					case "__level__": { 
						continue;
					}
					case "__id__": { 
						continue;
					}
					default:{			
						Map<String,Object> mapValue = (Map<String,Object>)entry.getValue();
						int subLevel = (int)mapValue.get("__level__"); 
						String propertySubValue = getPropertyValue(mapValue,false);
						if(listElement){
							propertySubValue = propertySubValue.replaceAll("^\\s+","");
							listElement = false;
						}
						result.append(propertySubValue);
					}
				}
			}
		}	
		
		return result.toString();
	}
	
	private static String appendLevel(int level){		
		if(level==0)
			return "";
		return String.format("%"+level+"s", "");
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
				return true;
								
			}
			case MAP: {
				String name = text.getElementName();
				
				Map<String,Object> result = new LinkedHashMap<>();									
				result.put("__comments__", text.getComments());
				result.put("__level__", text.getLevel());
				result.put("__annotations__", text.getAnnotations());
				result.put("__id__", name);				
				parent.put(name, result);
				
				int nextLevel = text.getNextLevel();
				if(nextLevel>level){					
					while((readElement(text, nextLevel,result))){
						System.out.println("Loaded");				
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
							System.out.println("Loaded");
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
