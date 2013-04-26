package edu.harvard.hul.ois.jhove;

/** A small class to hold information about a module. */
public class ModuleInfo {
    public String clas;
    public String init;
    public String[] params;
    
    public ModuleInfo (String className) {
        clas = className;
    }
    
    public ModuleInfo (String className, String init) {
        clas = className;
        this.init =  init;
    }
}
