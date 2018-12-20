package ru.dnechoroshev.yaml.model;

public class Annotation {
	private String name;
	private String value;
	public Annotation(String name, String value) {
		super();
		this.name = name;
		this.value = value;
	}
	public String getName() {
		return name;
	}
	public String getValue() {
		return value;
	}
	@Override
	public String toString() {
		return "Annotation [name=" + name + ", value=" + value + "]";
	}
}
