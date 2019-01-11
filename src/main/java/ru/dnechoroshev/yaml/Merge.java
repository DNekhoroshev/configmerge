package ru.dnechoroshev.yaml;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;

import ru.dnechoroshev.yaml.model.GroupEntry;

public class Merge {

	public static void main(String[] args) {	
		try {
			ConfigPromoter cp = new ConfigPromoter("d:/temp/group_vars");
			cp.initGroupProperties();
		} catch (Exception e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
	}
	
	public void merge(GroupEntry sourceGroup, GroupEntry targetGroup) {
		for(GroupEntry sourceChild : sourceGroup.getChilds()) {
			GroupEntry targetChild = targetGroup.lookupChildGroup(sourceChild.getName());
			
			if(targetChild==null) {
				targetGroup.addChild(sourceChild);
				continue;
			}
			
			Map<String,Object> sourceChildProps =  sourceChild.getProperties();
			Map<String,Object> targetChildProps =  targetChild.getProperties();
			
			for(Entry<String,Object> childPropsEntry : sourceChildProps.entrySet()) {				
				String key = childPropsEntry.getKey();
				if(targetChildProps.get(key)!=null) {
					//targetChildProps.put(childPropsEntry.getKey(), mergeValues(childPropsEntry.getValue(), targetChildProps.get(key)));
				}else {
					//target
				}
			}
		}
	}
	
	private Object mergeValues(Object source,Object target) throws InstantiationException, IllegalAccessException {
		if((source instanceof String)&&(target instanceof String)) {
			return source;
		}else if ((source instanceof List)&&(target instanceof List)) {
			for(Object sourceElement: (List)source) {
				if(sourceElement instanceof Map) {
					mergeMapIntoListOfMaps((Map)sourceElement, (List)target);
				}else if (sourceElement instanceof String) {
					mergeStringIntoListOfStrings((String)sourceElement, (List)target);
				}
				return target;
			}
		}else if ((source instanceof Map)&&(target instanceof Map)) {
			mergeMaps((Map)source, (Map)target);
			return target;
		}
		return null;
	}
	
	private void mergeMapIntoListOfMaps(Map<String,Object> m,List<Map<String,Object>> targetList) throws InstantiationException, IllegalAccessException {
		String id = (String)m.get("id");
		if(id==null)
			throw new RuntimeException("Id is not correctly set in object: "+m);
		
		for(Map<String,Object> targetElement : targetList) {
			if(id.equals(targetElement.get("id"))) {
				mergeMaps(m, targetElement);
				return;
			}
		}
		targetList.add(m);
	}
	
	private void mergeStringIntoListOfStrings(String s,List<String> targetList) {		
		if(!targetList.contains(s))
			targetList.add(s);
	}
	
	public static void mergeMaps(Map<String,Object> source,Map<String,Object> target) {
		
		if("no".equals(target.get("AcceptanceStrategy"))) {
			return;
		}else if ("never".equals(source.get("PropagationStrategy"))) {
			return;
		}
		
		for(Entry<String,Object> sourceFieldEntry : source.entrySet()) {
			
			String sourceKey = sourceFieldEntry.getKey();
			switch(sourceKey){
				case "level":{
					target.put("level", sourceFieldEntry.getValue());
					break;
				}case "comments":{
					target.put("comments", sourceFieldEntry.getValue());
					break;
				}case "PropagationStrategy":{
					break;
				}case "AcceptanceStrategy":{
					break;
				}default:{
					Map<String,Object> sourceField = (Map<String,Object>)sourceFieldEntry.getValue();
					Map<String,Object> targetField = (Map<String,Object>)target.get(sourceFieldEntry.getKey());
					
					if(targetField==null) {
						targetField = new HashMap<String,Object>();
						target.put(sourceFieldEntry.getKey(), targetField);
					}
					
					if (isLeafValue(sourceField)){
						propagate(source,target,sourceFieldEntry.getKey());
					}else{
						mergeMaps(sourceField, targetField);
					}
					break;
				}
			}		
			
		}
		
	}
	
	public static void propagate(Map<String,Object> source,Map<String,Object> target, String fieldName) {
		
		Map<String,Object> sourceField = (Map<String,Object>)source.get(fieldName);
		Map<String,Object> targetField = (Map<String,Object>)target.get(fieldName);
		
		if("no".equals(targetField.get("AcceptanceStrategy")))
			return;
		
		targetField.put("level", sourceField.get("level"));
		targetField.put("comments", sourceField.get("comments"));
		targetField.put("PropagationStrategy", sourceField.get("PropagationStrategy"));
		
		if("value".equals(sourceField.get("PropagationStrategy")))
			targetField.put("value", sourceField.get("value"));
		else if("empty".equals(sourceField.get("PropagationStrategy")))
			targetField.put("value", "");
		else if("never".equals(sourceField.get("PropagationStrategy"))){
			targetField.remove(fieldName);		
		}		
				
	}
	
	public static boolean isLeafValue(Map<String,Object> m) {
		return (m.get("value") instanceof java.lang.String);
	}

}
