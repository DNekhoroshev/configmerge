package ru.dnechoroshev.yaml;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.yaml.snakeyaml.Yaml;

import ru.dnechoroshev.yaml.model.GroupEntry;

public class ConfigPromoter {

	private Map<String,File> varFolders = new HashMap<>();
	
	private GroupEntry all;
	
	public ConfigPromoter(String rootPath) throws Exception{		
		Files.walk(Paths.get(rootPath)).filter(Files::isDirectory).forEach(this::addVarFolder);		
	}	
	
	public void initGroupProperties() throws IOException, URISyntaxException{
		all = new GroupEntry("all",null);
		GroupEntry lastGroup = all;
		GroupEntry currentGroup = null;
		
		boolean groupContext = false;
		Map<String,GroupEntry> groups = new HashMap<>();
		
		List<String> hosts = Files.readAllLines(Paths.get(Merge.class.getClassLoader().getResource("hosts").toURI()),Charset.defaultCharset());
		for (String host : hosts) {

			if (!host.isEmpty()) {
				String groupName = getGroupName(host);
				if (isGroup(host)) {
					groupContext = false;
					lastGroup = new GroupEntry(groupName, all);
					if (isChildrenDeclaration(host)) {
						groupContext = true;
					}
					groups.put(groupName, lastGroup);
				} else if (groupContext) {
					if (groups.containsKey(groupName)) {
						currentGroup = groups.get(groupName);
						currentGroup.rebind(lastGroup);
					} else {
						currentGroup = new GroupEntry(groupName, lastGroup);
					}
				} else {
					currentGroup = new GroupEntry(groupName, lastGroup);
				}
			}
		}		
	}	
	
	private void loadGroupProperties(GroupEntry group,File groupPropsFile) throws FileNotFoundException{
		Yaml yaml = new Yaml();
		Map<String, Object> properties = yaml.load(new FileInputStream(groupPropsFile));
		group.getProperties().putAll(properties);				
	}	
	
	private static boolean isGroup(String s) {
		return s.matches("^\\[[a-z0-9:_]*\\]$");
	}

	private static boolean isChildrenDeclaration(String s) {
		return s.contains(":children");
	}

	private static String getGroupName(String groupDeclaration) {
		String[] decFields = groupDeclaration.split(":");
		return decFields[0].replace("[", "").replace("]", "");
	}
		
	private void addVarFolder(Path path){		
		varFolders.put(path.toFile().getName(), path.toFile());		
	}

	public Map<String, File> getVarFolders() {
		return varFolders;
	}
	
	
}
