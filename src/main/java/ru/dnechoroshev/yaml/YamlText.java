package ru.dnechoroshev.yaml;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.lang3.RegExUtils;
import org.apache.commons.lang3.StringUtils;

import ru.dnechoroshev.yaml.model.Annotation;
import ru.dnechoroshev.yaml.model.PropertyStatus;

public class YamlText {
	ArrayList<String> lines = new ArrayList<>();
	ArrayList<String> commentLines = new ArrayList<>();
	ArrayList<Annotation> annotations = new ArrayList<>();
	
	int pointer = 0;
	
	Pattern propertyPattern = Pattern.compile("^[a-zA-Z0-9\\-_ ]+:");
	
	YamlText(Scanner scanner){		 
		while (scanner.hasNextLine()) {
			lines.add(scanner.nextLine());							
		}
	}
	
	public boolean next(){
		if(pointer<lines.size()){
			pointer++;
			return true;
		}else{
			return false;
		}
	}
	
	public boolean previuos(){
		if(pointer>1){
			pointer--;
			return true;
		}else{
			return false;
		}
	}
	
	public int getPosition(){
		return pointer;
	}
		
	public List<String> getComments(){
		return commentLines;
	}
	
	public List<Annotation> getAnnotations(){
		return annotations;
	}
	
	public void setPosition(int p){
		this.pointer = p;
	}
	
	public String currentLine(){
		return lines.get(pointer-1);
	}
	
	public boolean seekNextElement(int level){		
		commentLines = new ArrayList<>();
		annotations = new ArrayList<>();
		int init_pos = pointer;
		while(next()){
			if((checkPropertyStatus()==PropertyStatus.NONE)){
				continue;
			}else if((checkPropertyStatus()==PropertyStatus.COMMENT)){				
				commentLines.add(currentLine().trim());
				if(isAnnotation()){
					annotations.add(getAnnotation());
				}
				continue;
			}
			if(getLevel()<level){
				pointer = init_pos;
				return false;
			}else if(getLevel()==level){
				return true;
			}
			
		}		
		pointer = init_pos;
		return false;			
	}	
	
	public int getNextLevel(){
		int init_pos = pointer;
		int init_level = 0;
		if (init_pos>0){
			init_level=getLevel();
		}
		
		while(next()){			
			if(checkPropertyStatus()!=PropertyStatus.NONE){
				int level = getLevel(); 
				pointer = init_pos;
				return level;
			}
		}
		return init_level;		
	}	
	
	public int getLevel() {
		String s = currentLine();		
		return s.indexOf(s.trim());
	}
	
	public boolean isAnnotation() {
		String s = currentLine().trim();
		return s.startsWith("#@");
	}
	
	public boolean isListElement(){
		String s = currentLine().trim();
		return s.startsWith("-");
	}
	
	public Annotation getAnnotation() {
		String s = currentLine().trim();
		String[] aValues = s.replace("#@", "").split("=");
		return new Annotation(aValues[0].trim(), aValues[1].trim());
	}
	
	public PropertyStatus checkPropertyStatus() {
		String s = currentLine();
		if((s==null)||(s.trim().isEmpty())) {
			return PropertyStatus.NONE;
		}
		if(s.trim().startsWith("#")){
			return PropertyStatus.COMMENT;
		}
		if(s.trim().startsWith("-")){
			return PropertyStatus.LISTELEMENT;
		}
		if(s.trim().matches("^[a-zA-Z0-9\\-_ ]+:(.)*")) {
			if(s.trim().endsWith(":")) {								
				return PropertyStatus.MAP;
			}else {
				return PropertyStatus.SIMPLE;
			}
		}		
		return PropertyStatus.NONE;
	}
	
	public String getElementName() {
		String s = currentLine().trim();
		if(s.startsWith("-")){
			s = s.substring(1).trim();
		}
		int colIndex = s.indexOf(':');
		if(colIndex>0){
			return s.substring(0, colIndex);
		}
		return "";
	}
	
	public Map<String,Object> getProperty() {
		String s = currentLine();
		Matcher m = propertyPattern.matcher(s.trim());
		if(m.find()) {
			String propertyName = StringUtils.chop(m.group(0)).trim();
			if(propertyName.startsWith("-")){
				propertyName = propertyName.substring(1);
			}
				
			String propertyValue = RegExUtils.removeFirst(s.trim(), propertyPattern);					
			Map<String,Object> prop = new HashMap<>();
			prop.put("__value__", propertyValue);
			prop.put("__id__", propertyName);
			prop.put("__comments__", commentLines);
			prop.put("__annotations__", annotations);
			prop.put("__level__", getLevel());
			return prop;
		}
		return null;
	}
	
}
