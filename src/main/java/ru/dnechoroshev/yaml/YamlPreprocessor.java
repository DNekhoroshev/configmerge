package ru.dnechoroshev.yaml;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Scanner;

import org.yaml.snakeyaml.Yaml;

import ru.dnechoroshev.yaml.model.Annotation;
import ru.dnechoroshev.yaml.model.PropertyStatus;

public class YamlPreprocessor {	
	
	public static void main(String[] args) throws IOException {
		try {
			
			Map<String,Object> source = loadYML("c:/tmp/csv/source.yml");
			Map<String,Object> target = loadYML("c:/tmp/csv/target.yml");		
			
			Map<String,Object> transformedSource = transform(source);
			Map<String,Object> transformedTarget = transform(target);
			
			System.out.println(transformedSource);
			System.out.println(transformedTarget);
			
			Merge.mergeMaps(transformedSource, transformedTarget);
		
			System.out.println(dump(transformedTarget));
						
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
	}
	
	private static String dump(Map<String,Object> yml){
		Yaml yaml = new Yaml();
	    StringWriter writer = new StringWriter();
	    yaml.dump(yml, writer);
	    return writer.toString();
	}
	
	private static Map<String,Object> loadYML(String path) throws FileNotFoundException{
		
		Scanner scanner = new Scanner(new File(path));		
		YamlText yText = new YamlText(scanner);
		scanner.close();
		Map<String,Object> result = new LinkedHashMap<>();			
		int rootLevel = yText.getNextLevel();						
		while((readElement(yText, rootLevel,result))){
			System.out.println("Loaded");
		}
		return result;
	}
	
	private static Map<String,Object> transform(Map<String,Object> yml) throws IOException{
		 StringBuilder result = new StringBuilder("---\n");
		 
		 for(Entry<String,Object> entry : yml.entrySet()){			 
			 Map<String,Object> elementValue = (Map<String,Object>)entry.getValue();
			 String enrichedYaml = serialyzeElement(elementValue,0,false); 
			 result.append(enrichedYaml);
		 }	 
		 
		 Yaml yaml = new Yaml();
		 return yaml.load(result.toString());		 
	}	
	
	private static String serialyzeElement(Map<String,Object> prop,int propLevel,boolean listElement){
			
		int level = (int)prop.get("__level__"); 
		
		StringBuilder result = new StringBuilder(appendLevel(propLevel)+(listElement?"- ":""));
		
		String id = (String)prop.get("__id__");
		List<String> commentList = (List<String>)prop.get("__comments__");
		List<Annotation> annotationList = (List<Annotation>)prop.get("__annotations__");
		String value = (String)prop.get("__value__");
		List<Map<String,Object>> valueList = (List<Map<String,Object>>)prop.get("__list__");				
	
		if(value!=null){
			result.append(id+": ").append("\n").append(appendLevel(propLevel+3))
				  .append("value: ").append(value).append("\n").append(appendLevel(propLevel+3))
				  .append("level: ").append(level).append("\n");
			for(Annotation a: annotationList){
				result.append(appendLevel(propLevel+3)).append(a.getName()).append(": ").append(a.getValue()).append("\n");
			}
				  
		}else if(valueList!=null){
			result.append(id+":").append("\n").append(appendLevel(propLevel+3))
				  .append("level: ").append(level).append("\n");
			for(Annotation a: annotationList){
				result.append(appendLevel(propLevel+3)).append(a.getName()).append(": ").append(a.getValue()).append("\n");
			}
			result.append(appendLevel(propLevel+3)).append("value: ").append("\n");
			for(Map<String,Object> val : valueList){
				result.append(serialyzeElement(val,propLevel+4,true));
			}
		}else{			
			if(id!=null){
				result.append(id+":").append("\n");				
			}
			boolean startValues = true;	
			for(Entry<String,Object> entry : prop.entrySet()){
				String key = entry.getKey();							
				switch(key){
					case "__comments__": {						
						if (!commentList.isEmpty()) {
							result.append(appendLevel(propLevel + 2)).append("comments: ").append("\n");
							for (String comment : commentList) {
								result.append(appendLevel(propLevel + 3)).append("- '").append(comment).append("'\n");
							}
						}
						break;
					}
					case "__annotations__": { 
						for(Annotation a: annotationList){
							result.append(appendLevel(propLevel+2)).append(a.getName()).append(": ").append(a.getValue()).append("\n");
						}
						break;
					}
					case "__level__": {						
						if(listElement){
							result.append("level: ").append(level).append("\n");
							listElement = false;
						}else{
							result.append(appendLevel(propLevel+2)).append("level: ").append(level).append("\n");
						}
						break;
					}
					case "__id__": { 
						break;
					}
					default:{			
						if(startValues){
							result.append(appendLevel(propLevel+2)).append("value: ").append("\n");
							startValues =false;
						}
						
						Map<String,Object> mapValue = (Map<String,Object>)entry.getValue();					
						
						String propertySubValue = serialyzeElement(mapValue,propLevel+3,false);
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
	
	private static String getValueWithMetaData(String value, List<Annotation> annotations){
		StringBuilder result = new StringBuilder("{value: "+value);
		for(Annotation a : annotations){
			result.append(",").append(a.getName()).append(":").append(a.getValue());
		}
		result.append("}");
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
				result.put("__level__", text.getAbsoluteLevel());
				result.put("__comments__", text.getComments());				
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
					result.put("__level__", text.getAbsoluteLevel());
					result.put("__comments__", text.getComments());					
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
