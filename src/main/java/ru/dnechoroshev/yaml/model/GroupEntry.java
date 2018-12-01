package ru.dnechoroshev.yaml.model;

import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class GroupEntry {
	private String name;
	private GroupEntry parent;
	private Set<GroupEntry> childs = new HashSet<>();
	private Map<String, Object> properties;	
	
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
			
	public void loadProperties(){
		
	}
	
	protected String getStringRepresentation(GroupEntry e, int level){
		String levelMark = new String(new char[level]).replace("\0", "--");
		StringBuilder sb = new StringBuilder(levelMark).append(e.getName()).append("\n");
		for(GroupEntry child : e.childs){
			sb.append(e.getStringRepresentation(child, level+1));
		}
		return sb.toString();
		
	}
	
	@Override
	public String toString(){
		return getStringRepresentation(this, 0);
	}
	
}
