package ru.dnechoroshev.yaml;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.lang3.StringUtils;

import ru.dnechoroshev.yaml.model.Annotation;
import ru.dnechoroshev.yaml.model.PropertyStatus;

public class YamlText {
	ArrayList<String> lines = new ArrayList<>();
	int pointer = 0;
	
	Pattern propertyPattern = Pattern.compile("^[a-zA-Z0-9\\-_]+:");
	
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
		
	public void setPosition(int p){
		this.pointer = p;
	}
	
	public String currentLine(){
		return lines.get(pointer-1);
	}
	
	public boolean seekNextElement(int level){		
		int init_pos = pointer;
		while(next()){
			if((checkPropertyStatus()==PropertyStatus.NONE)){
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
		while(next()){			
			if(checkPropertyStatus()!=PropertyStatus.NONE){
				int level = getLevel(); 
				pointer = init_pos;
				return level;
			}
		}
		return -1;		
	}	
	
	private int getLevel() {
		String s = currentLine(); 
		return s.indexOf(s.trim());
	}
	
	public boolean isAnnotation(String s) {
		return s.trim().startsWith("#@");
	}
	
	public Annotation getAnnotation(String s) {
		String[] aValues = s.replace("#@", "").split("=");
		return new Annotation(aValues[0].trim(), aValues[1].trim());
	}
	
	public PropertyStatus checkPropertyStatus() {
		String s = currentLine();
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
	
	public String getElementName() {
		String s = currentLine();
		return StringUtils.chop(s);
	}
	
	public Map<String,Object> getProperty() {
		String s = currentLine();
		Matcher m = propertyPattern.matcher(s.trim());
		if(m.find()) {
			String propertyName = m.group(0).replace(":", "");
			String propertyValue = s.replace(propertyName, "").replace(":", "").trim();
			Map<String,Object> prop = new HashMap<>();
			prop.put(propertyName, propertyValue);
			prop.put("__id__", propertyName);
			return prop;
		}
		return null;
	}
	
}
