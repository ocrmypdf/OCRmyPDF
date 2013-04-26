package edu.harvard.hul.ois.jhove;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

import edu.harvard.hul.ois.jhove.module.*;

/** This class creates a default configuration if no valid configuration file
 *  is found. */
public class DefaultConfigurationBuilder {

    private final static String FILE_SEP = System.getProperty ("file.separator");
    private final static String HOME_DIR = System.getProperty ("user.home");
    private final static String JHOVE_DIR = HOME_DIR + FILE_SEP + "jhove";
    private final static String TEMP_DIR = System.getProperty("java.io.tmpdir");
    private final static String DEFAULT_ENCODING = "utf-8";
    private final static int DEFAULT_BUFFER_SIZE = 131072;
    
    private File configFile;
    
    
    /** Constructor. A location for the file may be specified or
     *  left null, */
    public DefaultConfigurationBuilder (File location) {
        if (location != null) {
            configFile = location;
        }
        else {
            configFile = new File (JHOVE_DIR +
                      FILE_SEP + "conf" +
                      FILE_SEP + "jhove.conf");
        }
    }
    
    
    public void writeDefaultConfigFile () throws IOException {
//        if (TEMP_DEBUG) {
//            String configFileName = "null";
//            if (configFile != null) 
//                configFileName = configFile.getAbsolutePath();
//            System.out.println ("writeDefaultConfigFile: path is " + configFileName);
//        }
        ConfigWriter cw = new ConfigWriter (configFile, null);
        List<ModuleInfo> modules = getModules();
        // TextHandler, XmlHandler, and AuditHandler are loaded by
        // default, so there are no handlers to put in the config file.
        List<String[]> handlers = new ArrayList<String[]> ();
        File homeDir = new File (JHOVE_DIR);
        File tempDir = new File (TEMP_DIR);
        try {
            cw.writeFile(modules, handlers, homeDir, tempDir, 
                DEFAULT_ENCODING, DEFAULT_BUFFER_SIZE);
        }
        catch (IOException e) {
//            if (TEMP_DEBUG)
//                e.printStackTrace();
            throw e;
        }
    }

//    public void writeDefaultConfigFile () throws IOException {
//        ConfigWriter cw = new ConfigWriter (configFile, null);
//        List<ConfigWriter.ModuleInfo> modules = getModules();
//        // TextHandler, XmlHandler, and AuditHandler are loaded by
//        // default, so there are no handlers to put in the config file.
//        List<String> handlers = new ArrayList<String> ();
//        File homeDir = new File (JHOVE_DIR);
//        File tempDir = new File (TEMP_DIR);
//        cw.writeFile(modules, handlers, homeDir, tempDir, 
//                DEFAULT_ENCODING, DEFAULT_BUFFER_SIZE);
//    }

    public File getConfigFile () {
        return configFile;
    }
    
    
    protected List<ModuleInfo> getModules () {
        int nModules = builtInModules.length;
        ArrayList<ModuleInfo> mods = new ArrayList<ModuleInfo> (nModules);
        try {
            for (int i = 0; i < nModules; i++) {
                Class<?> cls = builtInModules[i];
                ModuleInfo minfo = new ModuleInfo(cls.getName());
                minfo.init = null;       // Never used at present
                minfo.params = getDefaultConfigParameters (cls);
                mods.add(minfo);
            }
        }
        catch (Exception e) {}
        return mods;
    }
    
    
    /** We can't have a static method in an Interface and override it, so we
     *  have to get a bit ugly to fake static inheritance. The advantage of
     *  this is that only the Modules with non-null default config file
     *  parameters have to implement the defaultConfigParams static field. */
    protected String[] getDefaultConfigParameters (Class<?> c) {
        try {
            Field dcpField = c.getField("defaultConfigParams");
            return (String[]) dcpField.get(null);
        }
        catch (Exception e) {
            return new String [] {};
        }
    }
    
    /** The array of build-in modules. If a module is added to or removed from
     *  the build, this array must be changed. The Bytestream module is
     *  loaded by default and so is not listed here. */
    private Class<?>[] builtInModules = {
        AiffModule.class,
        AsciiModule.class,
        GifModule.class,
        HtmlModule.class,
        Jpeg2000Module.class,
        JpegModule.class,
        PdfModule.class,
        TiffModule.class,
        Utf8Module.class,
        WaveModule.class,
        XmlModule.class
    };
}
