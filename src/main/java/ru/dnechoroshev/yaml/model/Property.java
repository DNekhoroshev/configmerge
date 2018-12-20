package ru.dnechoroshev.yaml.model;

import java.io.File;

public class Property {
	private String name;
	private Object value;
	private File source;
	
	public Property(String name, Object value, File source) {
		super();
		this.name = name;
		this.value = value;
		this.source = source;
	}

	public String getName() {
		return name;
	}

	public Object getValue() {
		return value;
	}

	public File getSource() {
		return source;
	}

	@Override
	public String toString() {
		return "Property [name=" + name + ", value=" + value + ", source=" + source + "]";
	}
	
	
	
}
