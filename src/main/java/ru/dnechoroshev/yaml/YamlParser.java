package ru.dnechoroshev.yaml;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

public class YamlParser {

	static Map<String,File> varFolders = new HashMap<>();
	
	public static void main(String[] args) throws Exception {
		/*Yaml yaml = new Yaml();
		InputStream inputStream = YamlParser.class.getClassLoader().getResourceAsStream("properties.yml");
		Map<String, Object> obj = yaml.load(inputStream);
		System.out.println(obj);*/
		
		Files.walk(Paths.get("d:/temp/group_vars/")).filter(Files::isDirectory).forEach(YamlParser::addVarFolder);
		System.out.println(varFolders);

	}
	
	public static void addVarFolder(Path path){		
		varFolders.put(path.toFile().getName(), path.toFile());		
	}

}
