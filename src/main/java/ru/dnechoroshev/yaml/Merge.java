package ru.dnechoroshev.yaml;

import java.util.ArrayList;
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
	
	private void mergeStringIntoListOfStrings(String s,List<String> targetList) {		
		if(!targetList.contains(s))
			targetList.add(s);
	}
	
	private static String getIdFieldName(Map<String,Object> m){
		Map<String,Object> value = (Map)m.get("value");
		if(value!=null){
			return (String)value.get("Id");
		}
		return null;
	}
	
	private static String getId(Map<String,Object> m){
		String idField = getIdFieldName(m);
		if(idField!=null){
			Map<String,Object> value = (Map)m.get("value");
			Map<String,Object> idMap = (Map)value.get(idField);
			return (String)idMap.get("value");
		}
		return null;
	}	
	
	private static void mergeMapIntoListOfMaps(Map<String,Object> m,List<Map<String,Object>> targetList) {
		String id = getId(m);
		if(id==null)
			throw new RuntimeException("Id is not correctly set in object: "+m);
		
		for(Map<String,Object> targetElement : targetList) {
			if(id.equals(getId(targetElement))) {
				mergeMaps(m, targetElement);
				return;
			}
		}
		targetList.add(m);
	}
	
	public static void mergeLists(List<Map<String,Object>> source,List<Map<String,Object>> target){
		for(Map<String,Object> sourceElement : source){
			mergeMapIntoListOfMaps(sourceElement, target);
		}
	}
	
	public static void mergeMaps(Map<String,Object> source,Map<String,Object> target) {
		
		if("Disabled".equals(target.get("Reception"))) {
			return;
		}else if ("Disabled".equals(source.get("Promote"))) {
			return;
		}
		
		for(Entry<String,Object> sourceFieldEntry : source.entrySet()) {
			
			String sourceKey = sourceFieldEntry.getKey();
			
			if("level".equals(sourceKey)||"comments".equals(sourceKey)||"Promote".equals(sourceKey)){
				target.put(sourceKey, sourceFieldEntry.getValue());
			}else {
				Object sourceValue = sourceFieldEntry.getValue();
				if(sourceValue instanceof Map){
					Map<String,Object> sourceField = (Map<String,Object>)sourceValue;
					Map<String,Object> targetField = (Map<String,Object>)target.get(sourceFieldEntry.getKey());
					
					if((targetField==null)||!(targetField instanceof Map)) {
						targetField = new HashMap<String,Object>();
						target.put(sourceFieldEntry.getKey(), targetField);
					}
					
					if (isLeafValue(sourceField)){
						propagate(source,target,sourceFieldEntry.getKey());
					}else{
						mergeMaps(sourceField, targetField);
					}
				}if(sourceValue instanceof List){
					List<Map<String,Object>> sourceField = (List<Map<String,Object>>)sourceValue;
					List<Map<String,Object>> targetField = (List<Map<String,Object>>)target.get(sourceFieldEntry.getKey());
					
					if((targetField==null)||!(targetField instanceof List)) {
						targetField = new ArrayList<Map<String,Object>>();
						target.put(sourceFieldEntry.getKey(), targetField);
					}				
					
				}
			}			
		}
		
	}
	
	public static void propagate(Map<String,Object> source,Map<String,Object> target, String fieldName) {
		
		Map<String,Object> sourceField = (Map<String,Object>)source.get(fieldName);
		Map<String,Object> targetField = (Map<String,Object>)target.get(fieldName);
		
		if("Disabled".equals(targetField.get("Reception")))
			return;
		
		targetField.put("level", sourceField.get("level"));
		targetField.put("comments", sourceField.get("comments"));
		targetField.put("Promote", sourceField.get("Promote"));
		
		if("NameAndValue".equals(sourceField.get("Promote")))
			targetField.put("value", sourceField.get("value"));
		else if("Name".equals(sourceField.get("Promote")))
			targetField.put("value", "");
		else if("Disabled".equals(sourceField.get("Promote"))){
			targetField.remove(fieldName);		
		}		
				
	}
	
	public static boolean isLeafValue(Map<String,Object> m) {
		return (m.get("value") instanceof java.lang.String);
	}

}
