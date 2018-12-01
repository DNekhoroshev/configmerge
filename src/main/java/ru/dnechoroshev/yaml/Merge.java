package ru.dnechoroshev.yaml;

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
	
	

}
