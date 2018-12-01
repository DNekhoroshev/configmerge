package ru.dnechoroshev.yaml;

import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import ru.dnechoroshev.yaml.model.GroupEntry;

public class Merge {

	public static void main(String[] args) {	
		GroupEntry all = new GroupEntry("all",null);
		GroupEntry lastGroup = all;
		GroupEntry currentGroup = null;
		
		boolean groupContext = false;
		Map<String,GroupEntry> groups = new HashMap<>();
		try {
			List<String> hosts = Files.readAllLines(Paths.get(Merge.class.getClassLoader().getResource("hosts").toURI()), Charset.defaultCharset());			
			for(String host : hosts){
				
				if (!host.isEmpty()) {
					String groupName = getGroupName(host);
					if (isGroup(host)) {
						groupContext = false;
						lastGroup = new GroupEntry(groupName,all);
						if (isChildrenDeclaration(host)) {
							groupContext = true;
						}
						groups.put(groupName, lastGroup);
					} else if (groupContext) {						
						if(groups.containsKey(groupName)){
							currentGroup = groups.get(groupName);
							currentGroup.rebind(lastGroup);
						}else{
							currentGroup = new GroupEntry(groupName, lastGroup);
						}						
					} else{
						currentGroup = new GroupEntry(groupName, lastGroup);
					}
				}
			}
			System.out.println(all);
		} catch (Exception e) {
			e.printStackTrace();
		}

	}
	
	private static boolean isGroup(String s){
		return s.matches("^\\[[a-z0-9:_]*\\]$");
	}
	
	private static boolean isChildrenDeclaration(String s){
		return s.contains(":children");
	}
	
	private static String getGroupName(String groupDeclaration){
		String[] decFields = groupDeclaration.split(":");
		return decFields[0].replace("[", "").replace("]", "");
	}

}
