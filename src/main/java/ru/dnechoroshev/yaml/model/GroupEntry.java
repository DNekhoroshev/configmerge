package ru.dnechoroshev.yaml.model;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class GroupEntry {
	private String name;
	private GroupEntry parent;
	private Set<GroupEntry> childs = new HashSet<>();	 
	private File source;
	private Map<String, Object> properties = new HashMap<>();	
	
	public GroupEntry(String name, GroupEntry parent) {
		super();
		this.name = name;
		this.parent = parent;
		if(parent!=null){
			parent.getChilds().add(this);
		}
	}
	
	public void addChild(GroupEntry child){
		childs.add(child);
	}
	
	public void removeChild(GroupEntry child){
		childs.remove(child);
	}	
	
	public void rebind(GroupEntry newParent){
		if(this.parent!=null){
			this.parent.removeChild(this);
		}
		this.parent = newParent;
		if(newParent!=null){
			newParent.addChild(this);
		}
	}
	
	public String getName() {
		return name;
	}

	public GroupEntry getParent() {
		return parent;
	}	
	
	public void setParent(GroupEntry parent) {
		this.parent = parent;
	}

	public Set<GroupEntry> getChilds() {
		return childs;
	}
			
	public Map<String, Object> getProperties() {
		return properties;
	}

	public void setProperties(Map<String, Object> properties) {
		this.properties = properties;
	}
	
	protected String getStringRepresentation(GroupEntry e, int level){
		String levelMark = new String(new char[level]).replace("\0", "--");
		String spaceMark = new String(new char[level]).replace("\0", "  ");
		StringBuilder sb = new StringBuilder(levelMark).append(e.getName()).append("\n");
		if(!this.properties.isEmpty()){
			this.properties.forEach((k,v)->sb.append(String.format("%s%s = %s\n",spaceMark,k,v)));
		}
		
		for(GroupEntry child : e.childs){
			sb.append(e.getStringRepresentation(child, level+1));
		}
		return sb.toString();
		
	}
	
	public Object getProperty(String name){
		if(properties.containsKey(name)){
			return properties.get(name);
		}
		if(parent!=null){
			return parent.getProperty(name);
		}
		return null;
	}
	
	public List<GroupEntry> lookup(String propertyName){
		List<GroupEntry> result = new ArrayList<>();
		if(properties.containsKey(propertyName))
			result.add(this);
		for(GroupEntry child : childs){
			result.addAll(child.lookup(propertyName));
		}
		return result;
	}
	
	public boolean isParentOf(GroupEntry ge){
		boolean result = false;
		for(GroupEntry child : childs){
			if(child==ge){
				return true;
			}else{
				result = result || child.isParentOf(ge);
				if(result)
					return true;
			}			
		}
		return false;
	}
	
	@Override
	public String toString(){
		return getStringRepresentation(this, 0);
	}

	public File getSource() {
		return source;
	}

	public void setSource(File source) {
		this.source = source;
	}	
	
}
