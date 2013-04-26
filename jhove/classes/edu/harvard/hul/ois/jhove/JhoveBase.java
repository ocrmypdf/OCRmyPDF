/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2005-2007 by the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import edu.harvard.hul.ois.jhove.handler.*;
import edu.harvard.hul.ois.jhove.module.*;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.logging.*;
import javax.net.ssl.KeyManager;
import javax.net.ssl.HostnameVerifier;
import javax.net.ssl.HttpsURLConnection;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLSession;
import javax.net.ssl.SSLSocketFactory;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;
import javax.xml.parsers.*;
import org.xml.sax.*;
import org.xml.sax.helpers.*;

/**
 * The JHOVE engine, providing all base services necessary to build an
 * application.
 * 
 * More than one JhoveBase may be instantiated and process files in
 * concurrent threads.  Any one instance must not be multithreaded.
 */
public class JhoveBase
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    private static Date _date;
    public static final String _name = "JhoveBase";
    public static final String _release = "1.9";
    public static final int [] DATE = {2012, 12, 17};
    private static final String _rights =
    	"Derived from software Copyright 2004-2011 " +
        "by the President and Fellows of Harvard College. " +
    	"Version 1.7 independently released. " +
    	"Released under the GNU Lesser General Public License.";

    /** JHOVE buffer size property. */
    private static final String BUFFER_PROPERTY = "edu.harvard.hul.ois." +
                                                  "jhove.bufferSize";
    /** JHOVE configuration directory */
    private static final String CONFIG_DIR = "conf";

    /** JHVOE configuration file property. */
    private static final String CONFIG_PROPERTY = "edu.harvard.hul.ois." +
                                                  "jhove.config";
    /** JHOVE default buffer size. */
    private static final int DEFAULT_BUFFER = 131072;

    /** JHOVE default character encoding. */
    private static final String DEFAULT_ENCODING = "utf-8";

    /** Default temporary directory. */
    private static final String DEFAULT_TEMP = ".";

    /** JHOVE encoding property. */
    private static final String ENCODING_PROPERTY = "edu.harvard.hul.ois." +
	                                            "jhove.encoding";
    /** JHOVE home directory */
    private static final String JHOVE_DIR = "jhove";

    /** JHOVE SAX parser class property. */
    private static final String SAX_PROPERTY = "edu.harvard.hul.ois.jhove." +
                                               "saxClass";
    /** JHOVE temporary directory property. */
    private static final String TEMPDIR_PROPERTY = "edu.harvard.hul.ois." +
	                                           "jhove.tempDirectory";
    
    /** MIX schema version property. */
    private static final String MIXVSN_PROPERTY = "edu.harvard.hul.ois." +
                                               "jhove.mixvsn";

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** Flag for aborting activity. */
    protected boolean _abort;
    /** Buffer size for buffered I/O. */
    protected int _bufferSize;
    protected boolean _checksum;
    /** Configuration file pathname. */
    protected String _configFile;
    /** Selected encoding. */
    protected String _encoding;
    /** Associate map of configution extensions. */
    protected Map<String, String> _extensions;
    /** Ordered list of output handlers. */
    protected List<OutputHandler> _handlerList;
    /** Map of output handlers (for fast access by name). */
    protected Map<String, OutputHandler> _handlerMap;
    /** JHOVE home directory. */
    protected String _jhoveHome;
    /** Ordered list of modules. */
    protected List<Module> _moduleList;
    /** Map of modules (for fast access by name). */
    protected Map<String, Module> _moduleMap;
    protected String _outputFile;
    /** SAX parser class. */
    protected String _saxClass;
    protected boolean _showRaw;
    protected boolean _signature;
    /** Temporary directory. */
    protected String _tempDir;
    /** MIX version. */
    protected String _mixVsn;
    /** Number of bytes for fake signature checking. */
    protected int _sigBytes;
    /** Directory for saving files. */
    protected File _saveDir;
    /** Byte count for digital object */
    protected long _nByte;
    /** Callback function to check for termination. */
    Callback _callback;
    /** Current URL connection. */
    protected URLConnection _conn;
    /** Thread currently parsing a document. */
    protected Thread _currentThread;
    
    /** Logger for this class. */
    protected Logger _logger;
    /** Logger resource bundle. */
    protected String _logLevel;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     * Instantiate a <tt>JhoveBase</tt> object.
     * @throws JhoveException If invoked with JVM lower than 1.5
     */
    public JhoveBase ()
	throws JhoveException
    {
        _logger = Logger.getLogger ("edu.harvard.hul.ois.jhove");
        _logger.setLevel (Level.SEVERE);
        /* Make sure we have a satisfactory version of Java. */
        String version = System.getProperty ("java.vm.version");
        if (version.compareTo ("1.5.0") < 0) {
            String bad = "Java 1.5 or higher is required";
            _logger.severe (bad);
	    throw new JhoveException (bad);
        }

    /* Tell any https connections to be accepted automatically. */
    HttpsURLConnection.setDefaultHostnameVerifier (new NaiveHostnameVerifier());
    
	/* Initialize the engine. */

        Calendar calendar = new GregorianCalendar ();
        calendar.set (DATE[0], DATE[1]-1, DATE[2]);
        _date = calendar.getTime ();

        _moduleList  = new ArrayList<Module> (20);
        _moduleMap   = new TreeMap<String, Module> ();

        _handlerList = new ArrayList<OutputHandler> ();
        _handlerMap  = new TreeMap<String, OutputHandler> ();

	_abort       = false;
	_bufferSize  = -1;
	_checksum    = false;
	_showRaw     = false;
	_signature   = false;
        _callback    = null;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /**
     * Initialize the JHOVE engine.
     * @param configFile Configuration file pathname
     */
    public void init (String configFile, String saxClass)
	throws JhoveException
    {
        _configFile = configFile;
        _saxClass = saxClass;

        File        config   = null;
        String err = null;
        // If we get an error, attempt to get through the best we can,
        // then throw a JhoveException with err as its message.

    	if (_configFile != null) {
    	    config = new File (_configFile);
    	    if (!config.exists () || !config.isFile ()) {
    	        DefaultConfigurationBuilder dcb = new DefaultConfigurationBuilder(config);
    	        try {
    	            dcb.writeDefaultConfigFile();
    	        }
    	        catch (Exception e) {
    	            err = "Configuration file " +
                          config.getAbsolutePath() +
                          " not found or " +
                          "not readable and could not create default file; use -c to specify";
    	            config = null;
                }
    	    }

            if (config != null) {
                XMLReader parser = null;
                try {
                    if (saxClass == null) {
                        /* Use Java 1.4 methods to create default parser.
                         */
                        SAXParserFactory factory = 
                            SAXParserFactory.newInstance();
                        factory.setNamespaceAware (true);
                        parser = factory.newSAXParser ().getXMLReader ();
                    }
                    else {
                        parser = XMLReaderFactory.createXMLReader (saxClass);
                    }
                }
                catch (Exception e) {
                    // If we can't get a SAX parser, we're stuck.
                    throw new JhoveException ("SAX parser not found: " +
					      saxClass);
                }
                _logger.info ("Using SAX parser " + parser.getClass ().getName ());
                ConfigHandler configHandler = new ConfigHandler ();
                parser.setContentHandler (configHandler);
                parser.setEntityResolver(configHandler);
                /* Attempt to set schema awareness to avoid validation
                 * errors.
                 */
                try {
                   parser.setFeature("http://xml.org/sax/features/validation",
				      true);
                   parser.setProperty ("http://java.sun.com/xml/jaxp/" +
					"properties/schemaLanguage",
					"http://www.w3.org/2001/XMLSchema");
                }
                catch (SAXException e) 
                    {}

                try {
                    String canonicalPath = config.getCanonicalPath ();
                    String fileURL = "file://";
                    if (canonicalPath.charAt (0) != '/') {
                        fileURL += '/';
                    }
                    fileURL += canonicalPath;
                    parser.parse (fileURL);
                }
                catch (IOException e) {
                      throw new
                      JhoveException ("Cannot read configuration file: " +
                        configFile);
                }
                catch (SAXException s) {
                    throw new
                JhoveException ("Error parsing configuration file: " +
                        s.getMessage ());
            }

            /* Update the application state to reflect the configuration
             * file, if necessary.
             */
            _extensions = configHandler.getExtensions ();
            _jhoveHome  = configHandler.getJhoveHome ();

            _encoding = configHandler.getEncoding ();
            if (_encoding == null) {
                _encoding = getFromProperties (ENCODING_PROPERTY);
                if (_encoding == null) {
                _encoding = DEFAULT_ENCODING;
                }
            }

            _tempDir = configHandler.getTempDir ();
            if (_tempDir == null) {
                _tempDir = getFromProperties (TEMPDIR_PROPERTY);
                if (_tempDir == null) {
            	_tempDir = DEFAULT_TEMP;
                }
            }
                
            // get the MIX version. if not specified, defaults to 2.0. 
            _mixVsn = configHandler.getMixVsn ();
            if (_mixVsn == null) {
                _mixVsn = "2.0";   // default
            }
                
            // Get the maximum number of bytes to examine when doing
            // pseudo-signature checking
            _sigBytes = configHandler.getSigBytes ();
            
            // If a log level was specified in the config file,
            // attempt to set it, unless it was already
            // explicitly set.
            if (_logLevel == null) {
                _logLevel = configHandler.getLogLevel ();
                if (_logLevel != null) {
                    try {
                        _logger.setLevel (Level.parse (_logLevel));
                    }
                    catch (Exception e) {}
                }
            }

    	    _bufferSize = configHandler.getBufferSize ();
            if (_bufferSize < 0) {
                String size = getFromProperties (BUFFER_PROPERTY);
                if (size != null) {
                    try {
                       _bufferSize = Integer.parseInt (size);
                    }
                    catch (Exception e) {}
    		    }
    		    if (_bufferSize < 0) {
                    _bufferSize = DEFAULT_BUFFER;
    		    }
            }
                
            /* Retrieve the ordered lists of modules and output handlers */
            List<ModuleInfo> modList = configHandler.getModule ();
            List<String[]> hanList = null;
            List<List<String>> params = configHandler.getModuleParams ();
            int n = modList.size ();
            for (int i=0; i<n; i++) {
                ModuleInfo modInfo = modList.get (i);
                List<String> param = params.get (i);
                try {
                   Class<?> cl = Class.forName (modInfo.clas);
                   Module module = (Module) cl.newInstance ();
                   module.init (modInfo.init);
                   module.setDefaultParams (param);
                        
                   _moduleList.add (module);
                   _moduleMap.put  (module.getName ().toLowerCase (),
                              module);
                   _logger.info ("Initialized " + module.getName ());
    	        }
                catch (Exception e) {
                    if (err == null) {
                        err = "cannot instantiate module: " +
        		                    modInfo.clas;
                    }
                }
            }

            hanList = configHandler.getHandler ();
            params = configHandler.getHandlerParams ();
            n = hanList.size ();
            for (int i=0; i<n; i++) {
    		    String[] tuple =  hanList.get (i);
                List<String> param = params.get (i);
    		    try {
                    Class<?> cl = Class.forName (tuple[0]);
                    OutputHandler handler =
                                 (OutputHandler) cl.newInstance ();
                    //handler.init (modInfo.init);
                    handler.setDefaultParams (param);
    		
                    _handlerList.add (handler);
                    _handlerMap.put  (handler.getName ().toLowerCase (),
                            		  handler);
                }
                catch (Exception e) {
                    if (err == null) {
                        err = "cannot instantiate handler: " + tuple[0];
                    }
                }
            }
        }
            // If we found any error, the caller needs to deal with it.
            if (err != null) {
                throw new JhoveException (err);
            }
    }
    else {
        throw new JhoveException ("Initialization exception; location not specified for configuration file.");
    }

	/****************************************************************
	 * The Bytestream module and the Text, XML, and Audit output
	 * handlers are always statically loaded.
	 ****************************************************************/

	Module module = new BytestreamModule ();
        module.setDefaultParams (new ArrayList<String> ());
	_moduleList.add (module);
	_moduleMap.put  (module.getName ().toLowerCase (), module);

    OutputHandler handler = new TextHandler ();
    handler.setDefaultParams (new ArrayList<String> ());
    _handlerList.add (handler);
    _handlerMap.put  (handler.getName ().toLowerCase (), handler);
	
    handler = new XmlHandler ();
    handler.setDefaultParams (new ArrayList<String> ());
    _handlerList.add (handler);
    _handlerMap.put  (handler.getName ().toLowerCase (), handler);
	
    handler = new AuditHandler ();
    handler.setDefaultParams (new ArrayList<String> ());
    _handlerList.add (handler);
    _handlerMap.put  (handler.getName ().toLowerCase (), handler);
    }


    /** Sets a callback object for tracking progress.  By default,
     *  the callback is null. */
    public void setCallback (Callback callback)
    {
        _callback = callback;
    }



    /** Processes a file or directory, or outputs information.
     *  If <code>dirFileOrUri</code> is null, Does one of the following:
     *  <ul>
     *   <li>If module is non-null, provides information about the module.
     *   <li>Otherwise if <code>aboutHandler</code> is non-null,
     *       provides information about that handler.
     *   <li>If they're both null, provides information about the
     *       application.
     *  </ul>
     *  @param app          The App object for the application
     *  @param module       The module to be used
     *  @param aboutHandler If specified, the handler about which info is requested
     *  @param handler      The handler for processing the output
     *  @param outputFile   Name of the file to which output should go
     *  @param dirFileOrUri One or more file names or URI's to be analyzed
     */
    public void dispatch (App app, Module module, /* String moduleParam, */
				OutputHandler aboutHandler,
				OutputHandler handler, /*String handlerParam,*/
				String outputFile,
				String [] dirFileOrUri)
	throws Exception
    {
        _abort = false;
    	/* If no handler is specified, use the default TEXT handler. */
    	if (handler == null) {
    	    handler = (OutputHandler) _handlerMap.get ("text");
    	}
    	handler.reset ();
    	_outputFile = outputFile;
    
    	handler.setApp    (app);
    	handler.setBase   (this);
    	handler.setWriter (makeWriter (_outputFile, _encoding));
    	//handler.param     (handlerParam);
    
    	handler.showHeader ();                /* Show handler header info. */
    
    	if (dirFileOrUri == null) {
            if (module != null) {             /* Show info about module. */
                //module.param (moduleParam);
                module.applyDefaultParams();
                module.show  (handler);
            }
            else if (aboutHandler != null) {  /* Show info about handler. */
                handler.show  (aboutHandler);
            }
            else {                            /* Show info about application */
                app.show (handler);
            }
    	}
    	else {
            for (int i=0; i<dirFileOrUri.length; i++) {
                if (!process (app, module, /*moduleParam, */ handler, /*handlerParam,*/
    			   dirFileOrUri[i])) {
                        break;
                }
    	    }
    	}
    
    	handler.showFooter ();                /* Show handler footer info. */
		handler.close();
    }

    /* Returns false if processing should be aborted.
     * Calls itself recursively for directories. */
    public boolean process (App app, Module module, OutputHandler handler, 
			    String dirFileOrUri)
    	throws Exception
    {
        if (_abort) {
            return false;
        }
        File file = null;
        boolean isTemp = false;
        long lastModified = -1;
        
        /* First see if we have a URI, if not it is a directory or a file. */
        URI uri = null;
        try {
            uri = new URI (dirFileOrUri);
        }
        catch (Exception e) {
            /* We may get an exception on Windows paths, if so then fall
             * through and try for a file.
             */
        }
        RepInfo info = new RepInfo (dirFileOrUri);
        if (uri != null && uri.isAbsolute ()) {
            URL url = null;
            try {
                url = uri.toURL ();
            }
            catch (Exception e) {
                throw new JhoveException ("cannot convert URI to URL: " +
        				  dirFileOrUri);
            }
            URLConnection conn = url.openConnection ();
            _conn = conn;
            if (conn instanceof HttpsURLConnection) {
                try {
                        //KeyManager[] km = null;
                        TrustManager[] tm = {new RelaxedX509TrustManager()};
                        SSLContext sslContext = SSLContext.getInstance("SSL");
                        sslContext.init(null, tm, new java.security.SecureRandom());
                        SSLSocketFactory sf = sslContext.getSocketFactory();
                        ((HttpsURLConnection)conn).setSSLSocketFactory(sf);
                        int code = ((HttpsURLConnection) conn).getResponseCode ();
                        if (200 > code || code >= 300) {
                	        throw new JhoveException ("URL not found: " +
                				  dirFileOrUri);
                        }
                }
                catch (Exception e) {
                    throw new JhoveException("URL not found: " + dirFileOrUri);
                }
            }
            lastModified = conn.getLastModified ();
            
            /* Convert the URI to a temporary file and use
             * for the input stream.
             */
        
            try {
                file = connToTempFile (conn, info);
                if (file == null) {
                    return false;     // user aborted
                }
                isTemp = true;
            }
            catch (IOException e) {
                _conn = null;
                String msg = "cannot read URL: " + dirFileOrUri;
                String msg1 = e.getMessage ();
                if (msg1 != null) {
                    msg += " (" + msg1 + ")";
                }
                throw new JhoveException (msg);
            }
            if (conn instanceof HttpsURLConnection) {
                ((HttpsURLConnection) conn).disconnect ();
            }
            _conn = null;
        }
        else {
            file = new File (dirFileOrUri);
        }
    
        if (file.isDirectory ()) {
            File [] files = file.listFiles ();
            info = null;        // free up unused RepInfo before recursing

	    /* Sort the files in ascending order by filename. */
	    Arrays.sort (files);

            handler.startDirectory (file.getCanonicalPath ());
            for (int i=0; i<files.length; i++) {
            	if (!process (app, module, handler,
        		         files[i].getCanonicalPath ())) {
                     return false;
                }
            }
            handler.endDirectory ();
        }
        else {
        
            if (!file.exists ()) {
        	info.setMessage (new ErrorMessage ("file not found"));
        	info.setWellFormed (RepInfo.FALSE);
        	info.show (handler);
            }
            else if (!file.isFile () || !file.canRead ()) {
        	info.setMessage (new ErrorMessage ("file cannot be read"));
        	info.setWellFormed (RepInfo.FALSE);
        	info.show (handler);
            }
	    else if (handler.okToProcess (dirFileOrUri)) {
		info.setSize (file.length ());
            	if (lastModified < 0) {
            	    lastModified = file.lastModified ();
            	}
            	info.setLastModified (new Date (lastModified));
            
            	if (module != null) {
            
            	    /* Invoke the specified module. */
            
            	    if (!processFile (app, module, false, file, info)) {
                                return false;
                    }
            	}
            	else {
            
            	    /* Invoke all modules until one returns well-formed.
                     * If a module doesn't know how to validate, we don't
                     * want to throw arbitrary files at it, so we'll skip it. */
            	    Iterator<Module> iter = _moduleList.iterator();
            	    while (iter.hasNext ()) {
            		Module  mod  = (Module)  iter.next ();
            		RepInfo infc = (RepInfo) info.clone ();

                        if (mod.hasFeature ("edu.harvard.hul.ois.jhove.canValidate")) {
                            try {
                                if (!processFile (app, mod, /*moduleParam,*/ false, file,
                	                    infc)) {
                                    return false;
                                }
                                if (infc.getWellFormed () == RepInfo.TRUE) {
                                    info.copy (infc);
                                    break;
                		}
                                else {
                                    // We want to know what modules matched the
                                    // signature, so we force the sigMatch property
                                    // to be persistent.
                                    info.setSigMatch (infc.getSigMatch ());
                                }        
                            }
                            catch (Exception e) {
            			/* The assumption is that in trying to analyze
            			 * the wrong type of file, the module may go
            			 * off its track and throw an exception, so we
            			 * just continue on to the next module.
            			 */
                                continue;
                            }
                        }
                    }
                }
                info.show (handler);
            }
        }
        if (file != null && isTemp) {
            file.delete ();
        }
        return true;
    }

    /** 
     *  Saves a URLConnection's data stream to a temporary file. 
     *  This may be interrupted asynchronously by calling
     *  <code>abort ()</code>, in which case it will delete
     *  the temporary file and return <code>null</code>.
     */
    public File connToTempFile (URLConnection conn, RepInfo info) 
        throws IOException
    {
        File tempFile;
        try {
            tempFile = newTempFile ();
        }
        catch (IOException e) {
            // Throw a more meaningful exception
            throw new IOException ("cannot create temp file");
        }
        OutputStream outstrm = null;
        DataInputStream instrm = null;
        if (_bufferSize > 0) {
            outstrm = new BufferedOutputStream
                (new FileOutputStream (tempFile), _bufferSize);
        }
        else {
            outstrm = new BufferedOutputStream
                (new FileOutputStream (tempFile));
        }
        try {
            if (_bufferSize > 0) {
                instrm = new DataInputStream (new BufferedInputStream 
                    (conn.getInputStream (), _bufferSize));
            }
            else {
                instrm = new DataInputStream (new BufferedInputStream 
                    (conn.getInputStream ()));
            }
        }
        catch (UnknownHostException e) {
            tempFile.delete ();
            throw new IOException (e.toString ());
        }
        catch (IOException e) {
            // IOExceptions other than UnknownHostException
            tempFile.delete ();
            throw e;
        }
        catch (Exception e) {
            // Arbitrary URL's may throw unpredictable expressions;
            // treat them as IOExceptions
            tempFile.delete ();
            throw new IOException (e.toString ());
        }

        Checksummer ckSummer = null;
        if (_checksum) {
            ckSummer = new Checksummer (); 
        }
        _nByte = 0;

        int appModulo = 4000;
        /* Copy the connection stream to the file. While we're
           here, calculate the checksums. */
        try {
            byte by;
            for (;;) {
                // Make sure other threads can get in occasionally to cancel
                if ((_nByte % appModulo) == 0) {
                    Thread.yield ();
                    if (_callback != null) {
                        _callback.callback (1, new Long (_nByte));
                    }
                    // In order to avoid doing too many callbacks, limit 
                    // the checking to a number of bytes at least 1/10 of
                    // the bytes read so far.
                    if (appModulo * 10 < _nByte) {
                        appModulo = (int) (_nByte / 10);
                    }
                }
                if (_abort) {
                    // Asynchronous abort requested.  Clean up.
                    instrm.close ();
                    outstrm.close ();
                    tempFile.delete ();
                    return null;
                }
                int ch = instrm.readUnsignedByte ();
                if (ckSummer != null) {
                    ckSummer.update (ch);
                }
                by = Checksum.unsignedByteToByte (ch);
                _nByte++;
                outstrm.write (by);
            }
        }
        catch (EOFException e) {
            /* This is the normal way for detecting we're done */
        }
        /* The caller is responsible for disconnecting conn. */
        instrm.close ();
        outstrm.close ();

        /* Update RepInfo */
        info.setSize (_nByte);
        if (ckSummer != null) {
            info.setChecksum (new Checksum (ckSummer.getCRC32 (), 
                                            ChecksumType.CRC32));
            String value = ckSummer.getMD5 ();
            if (value != null) {
                info.setChecksum (new Checksum (value, ChecksumType.MD5));
            }
            value = ckSummer.getSHA1 ();
            if (value != null) {
                info.setChecksum (new Checksum (value, ChecksumType.SHA1));
            }
        }
        return tempFile;
    }

    /**
     *  Aborts an activity.  This simply sets a flag; whether
     *  anything is aborted depends on what activity is
     *  happening.
     */
    public void abort ()
    {
        _abort = true;
        HttpsURLConnection conn = null;
        if (_conn instanceof HttpsURLConnection) {
            conn = (HttpsURLConnection) _conn;
        }
        // If we're stuck in socket I/O, then there is no way
        // to kill the thread cleanly.  Wait a few seconds,
        // and if we're still not terminated, pull the plug on
        // the socket.
        try {
            Thread.sleep (4000);
        }
        catch (InterruptedException e) {
        }
        if (conn != null) {
              // This is a non-deprecated way of bringing the connection
              // to a screeching halt.  disconnect will (we hope) close
              // the underlying socket, killing any hanging I/O.
              conn.disconnect ();
        }
    }



    /* Processes the file.  Returns false if aborted, or if the
     * module is incapable of validation.  This shouldn't be called
     * if the module doesn't have the validation feature. */
    public boolean processFile (App app, Module module, /*String moduleParam,*/
				boolean verbose, File file, RepInfo info)
	throws Exception
    {
        if (!module.hasFeature("edu.harvard.hul.ois.jhove.canValidate")) {
            return false;
        }
        if (_callback != null) {
            _callback.callback (2, info.getUri());
        }
        module.setApp  (app);
        module.setBase (this);
        module.setVerbosity (verbose ? Module.MAXIMUM_VERBOSITY :
			     Module.MINIMUM_VERBOSITY);
        module.applyDefaultParams ();
        if (module.isRandomAccess ()) {

            /* Module needs random access input. */

            RandomAccessFile raf = new RandomAccessFile (file, "r");
            if (_signature) {
               module.checkSignatures (file, raf, info);
            }
            else {
                module.parse (raf, info);
            }
            raf.close ();
        }
        else {

	    /* Module accepts stream input. */

        
        InputStream stream = new FileInputStream (file);
        try {
    	    if (_signature) {
    		module.checkSignatures (file, stream, info);
    	    }
    	    else {
                int parseIndex = module.parse (stream, info, 0);
                /* If parse returns non-zero, reparse with a fresh stream. */
                while (parseIndex != 0) {
                    stream.close ();
                    stream = new FileInputStream (file);
                    parseIndex = module.parse (stream, info, parseIndex);
                }
    	    }
        }
        finally {
            stream.close ();
        }
	}
        return true;    // Successful processing
    }
	
    /**
     *  Creates a temporary file with a unique name.  
     *  The file will be deleted when the application exits.
     */
    public File tempFile ()
	throws IOException
    {
        File file = null;

        /* If no temporary directory has been specified, use the
	 * Java default temp directory.
	 */
        if (_tempDir == null) {
            file = File.createTempFile ("JHOV", "");
        }
        else {
            File dir = new File (_tempDir);
            file = File.createTempFile ("JHOV", "", dir);
        }
        file.deleteOnExit();

        return file;
    }

    /******************************************************************
     * Accessor methods.
     ******************************************************************/
    
    /**
     *  Returns the abort flag.
     */
    public boolean getAbort ()
    {
        return _abort;
    }

    /**
     * Returns buffer size.  A value of -1 signifies that the invoknig
     * code should assume the default buffer size.
     */
    public int getBufferSize ()
    {
        return _bufferSize;
    }

    /**
     * Returns the configuration file.
     */
    public  String getConfigFile ()
    {
        return _configFile;
    }

    /**
     *   Returns the engine date (the date at which 
     *   this instance was created).
     */
    public  Date getDate ()
    {
        return _date;
    }

    /**
     * Returns the output encoding.
     */
    public  String getEncoding ()
    {
        return _encoding;
    }

    /**
     * Return the JHOVE configuration extensions.
     */
    public  Map<String, String> getExtension ()
    {
        return _extensions;
    }

    /**
     * Return the JHOVE configuration extension by name.
     */
    public  String getExtension (String name)
    {
        return (String) _extensions.get (name);
    }

    /**
     * Return a handler by name.
     */
    public  OutputHandler getHandler (String name)
    {
        OutputHandler handler = null;
        if (name != null) {
            handler = _handlerMap.get (name.toLowerCase ());
        }
        return handler;
    }


    /** Returns map of handler names to handlers. */
    public  Map<String, OutputHandler> getHandlerMap ()
    {
        return _handlerMap;
    }
    
    /** Returns the list of handlers. */
    public  List<OutputHandler> getHandlerList ()
    {
        return _handlerList;
    }

    /**
     * Returns the JHOVE home directory.
     */
    public String getJhoveHome ()
    {
        return _jhoveHome;
    }

    /**
     * Returns a module by name.
     */
    public  Module getModule (String name)
    {
        Module module = null;
        if (name != null) {
            module = (Module) _moduleMap.get (name.toLowerCase ());
        }
        return module;
    }

    /** Returns the Map of module names to modules. */
    public  Map getModuleMap ()
    {
        return _moduleMap;
    }
    
    /** Returns the List of modules. */
    public  List getModuleList ()
    {
        return _moduleList;
    }

    /**
     *   Returns the engine name.
     */
    public String getName ()
    {
        return _name;
    }

    /**
     * Returns the output file.
     */
    public  String getOuputFile ()
    {
        return _outputFile;
    }

    /**
     *   Returns the engine release.
     */
    public String getRelease ()
    {
        return _release;
    }

    /**
     *   Return the engine rights statement
     */
    public String getRights ()
    {
        return _rights;
    }

    /**
     * Return the SAX class.
     */
    public String getSaxClass ()
    {
        return _saxClass;
    }

    /**
     * Return the temporary directory.
     */
    public String getTempDirectory ()
    {
        return _tempDir;
    }
    
    /** Return the maximum number of bytes to check, for modules that look for
     *  an indefinitely positioned signature or check the first sigBytes bytes
     *  in lieu of a signature
     */
    public int getSigBytes ()
    {
        return _sigBytes;
    }


    /**
     *  Return the directory designated for saving files.
     *  This is simply the directory most recently set by
     *  setSaveDirectory. */
    public File getSaveDirectory ()
    {
        return _saveDir;
    }
    
    /** Returns <code>true</code> if checksumming is requested. */
    public  boolean getChecksumFlag ()
    {
        return _checksum;
    }
    
    /** Returns <code>true</code> if raw output is requested.
     *  Raw output means numeric rather than symbolic output;
     *  its exact interpretation is up to the module, but generally
     *  applies to named flags. 
     */
    public  boolean getShowRawFlag ()
    {
        return _showRaw;
    }
    
    /** Returns the "check signature only" flag. */
    public  boolean getSignatureFlag ()
    {
        return _signature;
    }
    
    /** Returns the requested MIX schema version. */
    public String getMixVersion () 
    {
        return _mixVsn;
    }

    /******************************************************************
     * Mutator methods.
     ******************************************************************/

    /**
     * Sets the buffer size.  A value of -1 signifies that the invoking
     * code will assume the default buffer size.
     * 
     * Any non-negative value less than 1024 will result in a buffer size of 1024.
     */
    public  void setBufferSize (int bufferSize)
    {
        if (bufferSize >= 0 && bufferSize < 1024) {
            _bufferSize = 1024;
        }
        else {
            _bufferSize = bufferSize;
        }
    }


    /**
     * Sets the output encoding.
     */
    public  void setEncoding (String encoding)
    {
        _encoding = encoding;
    }

    /**
     * Sets the temporary directory path.
     */
    public  void setTempDirectory (String tempDir)
    {
        _tempDir = tempDir;
    }
    
    /**
     * Sets the log level.  The value should be the name of
     * a predefined instance of java.util.logging.Level, 
     * e.g., "WARNING", "INFO", "ALL".  This will override
     * the config file setting.
     */
    public  void setLogLevel (String level)
    {
        _logLevel = level;
        if (level != null) {
            try {
                _logger.setLevel (Level.parse (_logLevel));
            }
            catch (Exception e) {}
        }
    }


    /** Sets the value to be returned by <code>doChecksum()</code>. */
    public  void setChecksumFlag (boolean checksum)
    {
        _checksum = checksum;
    }

    /** Sets the value to be returned by <code>getShowRawFlag ()</code>,
     *  which determines if only raw numeric values should be output. 
     */
    public  void setShowRawFlag (boolean raw)
    {
        _showRaw = raw;
    }

    /** Sets the "check signature only" flag. */
    public  void setSignatureFlag (boolean signature)
    {
        _signature = signature;
    }

    /**
     *  Sets the default directory for subsequent save
     *  operations.
     */
    public  void setSaveDirectory (File dir)
    {
        _saveDir = dir;
    }

    /**
     *  Sets the current thread for parsing.
     */
    public void setCurrentThread (Thread t)
    {
        _currentThread = t;
    }

    /**
     *  Resets the abort flag.  This must be called at the beginning of
     *  any activity for which the abort flag may subsequently be set.
     */
    public void resetAbort ()
    {
        _abort = false;
    }

    /******************************************************************
     * PRIVATE CLASS METHODS.
     ******************************************************************/

    /** Uses the user.home property to locate the configuration
     *  file.  The file is expected to be in the subdirectory
     *  named by CONFIG_DIR under the home directory, and to
     *  be named <code>jhove.conf</code>.  Returns <code>null</code>
     *  if no such file is found.
     */
    public static String getConfigFileFromProperties ()
    {
        String configFile = null;
        configFile = getFromProperties (CONFIG_PROPERTY);
        if (configFile == null) {
            try {
                String fs = System.getProperty ("file.separator");
                configFile = System.getProperty ("user.home") + fs +
                   JHOVE_DIR + fs + CONFIG_DIR + fs + "jhove.conf";
            }
            catch (Exception e) {
            }
        }

        return configFile;
    }

    /** Returns the value of the property 
        <code>edu.harvard.hul.ois.jhove.saxClass</code>,
        which should be the name of the main SAX class.
        Returns <code>null</code> if no such property
        has been set up. */
    public static String getSaxClassFromProperties ()
    {
        String saxClass = getFromProperties (SAX_PROPERTY);

        return saxClass;
    }

    /** Returns a named value from the properties file. */
    public static String getFromProperties (String name)
    {
        String value = null;

        try {
            String fs = System.getProperty ("file.separator");
            Properties props = new Properties ();
            String propsFile = System.getProperty ("user.home") + fs +
                    JHOVE_DIR + fs + "jhove.properties";
            FileInputStream stream = new FileInputStream (propsFile);
            props.load (stream);
            stream.close ();

            value = props.getProperty (name);
        }
        catch (Exception e) {
        }

        return value;
    }

    /**
     * Creates an output PrintWriter.
     * @param outputFile Output filepath.  If null, writer goes to System.out.
     * @param encoding   Character encoding.  Must not be null.
     */
    protected static PrintWriter makeWriter (String outputFile, String encoding)
	throws JhoveException
    {
        PrintWriter output = null;
        OutputStreamWriter osw = null;
        if (outputFile != null) {
            try {
                FileOutputStream stream = new FileOutputStream (outputFile);
                osw = new OutputStreamWriter (stream, encoding);
                output = new PrintWriter (osw);
            }
            catch (UnsupportedEncodingException u) {
                throw new JhoveException ("unsupported character encoding: " +
					  encoding);
            }
            catch (FileNotFoundException e) {
                throw new JhoveException ("cannot open output file: " +
                        outputFile);
            }
        }
        if (output == null) {
            try {
                osw = new OutputStreamWriter (System.out, encoding);
            }
            catch (UnsupportedEncodingException u) {
                throw new JhoveException ("unsupported character encoding: " +
					  encoding);
            }
            output = new PrintWriter (osw);
	    }
        return output;
    }


    /**
     *  Creates a temporary file with a unique name.  
     *  The file will be deleted when the application exits.
     */
    public File newTempFile ()
        throws IOException
    {
        return tempFile ();
    }
    
    
    /** A HostnameVerifier for https connections that will never ask for 
     *  certificates.
     */
    private class NaiveHostnameVerifier implements HostnameVerifier {
        public boolean verify(String hostname, SSLSession session) {
            return true;
        }
    }
    
    /** A TrustManager which should accept all certificates.
     */
    private class RelaxedX509TrustManager implements X509TrustManager {
        public boolean isClientTrusted(java.security.cert.X509Certificate[] chain){ 
            return true; 
        }
        public boolean isServerTrusted(java.security.cert.X509Certificate[] chain) { 
            return true; 
        }
        public java.security.cert.X509Certificate[] getAcceptedIssuers() { 
            return null; 
        }
        public void checkClientTrusted(java.security.cert.X509Certificate[] chain) {
            
        }
        public void checkClientTrusted(java.security.cert.X509Certificate[] chain, String s) {
            
        }
        public void checkServerTrusted(java.security.cert.X509Certificate[] chain) {
            
        }
        public void checkServerTrusted(java.security.cert.X509Certificate[] chain, String s) {
            
        }
    }
}
