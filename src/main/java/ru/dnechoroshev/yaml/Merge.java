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
			
			Map<String,Object> sourceChildProps =  sourceChild.getProperties();
			Map<String,Object> targetChildProps =  targetChild.getProperties();
			
			for(Entry<String,Object> childPropsEntry : sourceChildProps.entrySet()) {				
				String key = childPropsEntry.getKey();
				if(targetChildProps.get(key)!=null) {
					targetChildProps.put(childPropsEntry.getKey(), mergeValues(childPropsEntry.getValue(), targetChildProps.get(key)));
				}
			}
		}
	}
	
	private Object mergeValues(Object source,Object target) {
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
	
	private void mergeMapIntoListOfMaps(Map<String,Object> m,List<Map<String,Object>> targetList) {
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
	
	private void mergeMaps(Map<String,Object> source,Map<String,Object> target) {
		if(!source.get("id").equals(target.get("id")))
			throw new RuntimeException(String.format("Cannot merge maps with dirrerent ids: %s :: %s",source,target));
		
		for(Entry<String,Object> sourceFieldEntry : source.entrySet()) {
			Map<String,Object> sourceField = (Map<String,Object>)sourceFieldEntry.getValue();
			Map<String,Object> targetField = (Map<String,Object>)target.get(sourceFieldEntry.getKey());
			if (isLeafValue(sourceField)){
				target.put(sourceFieldEntry.getKey(), propagate(sourceField, targetField));
			}else{
				mergeMaps(sourceField, targetField);
			}
		}
		
	}
	
	private Map<String,Object> propagate(Map<String,Object> source,Map<String,Object> target) {
		
		if(target==null)
			target=new HashMap<>();
		
		if("no".equals(target.get("AcceptanceStrategy")))
			return target;
		
		if("value".equals(source.get("PropagationStrategy")))
			target.put("value", source.get("value"));
		else if("empty".equals(source.get("PropagationStrategy")))
			target.put("value", "");
		else if("never".equals(source.get("PropagationStrategy")))
			target=null;
		
		return target;
				
	}
	
	private boolean isLeafValue(Map<String,Object> m) {
		return m.containsKey("configmerge.leaf");
	}

}
