/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004-2007 by the President and Fellows of Harvard College
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or (at
 * your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
 * USA
 **********************************************************************/

import edu.harvard.hul.ois.jhove.*;
//import java.io.*;
import java.util.*;

public class Jhove
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    /** Application name. */
    private static final String NAME = "Jhove";

    /** Application build date, YYYY, MM, DD. */
    private static int [] DATE;

    /** Application release number. */
    private static String RELEASE;

    /** Application invocation syntax. */
    private static final String USAGE = "java " + NAME + " [-c config] " +
        "[-m module] [-h handler] [-e encoding] [-H handler] [-o output] " +
	"[-x saxclass] [-t tempdir] [-b bufsize] [-l loglevel] [[-krs] " +
	"dir-file-or-uri [...]]";

    /** Copyright information. */
    private static final String RIGHTS =
	"Derived from software Copyright 2004-2011 " +
    "by the President and Fellows of Harvard College. " +
    "Version 1.7 and higher independently released. " +
	"Released under the GNU Lesser General Public License.";

    /******************************************************************
     * MAIN ENTRY POINT.
     ******************************************************************/

    public static void main (String [] args)
    {
        RELEASE = JhoveBase._release;      // possibly safer than final static init
        DATE = JhoveBase.DATE;
        /* Make sure we have a satisfactory version of Java. */
        String version = System.getProperty ("java.vm.version");
        if (version.compareTo ("1.5.0") < 0) {
            //System.err.println (NAME + ": Java 1.4 or higher is required");
            System.out.println ("Java 1.5 or higher is required");
            System.exit (-1);
        }

        try {
    
    	    /**********************************************************
    	     * Initialize the application state object.
    	     **********************************************************/
    
    	    App app = new App (NAME, RELEASE, DATE, USAGE, RIGHTS);
    
    	    /**********************************************************
    	     * Retrieve the configuration file.
    	     **********************************************************/
    
    	    String configFile = JhoveBase.getConfigFileFromProperties ();
    	    String saxClass   = JhoveBase.getSaxClassFromProperties ();
    
    	    /* Pre-parse the command line for -c and -x config options. 
    	     * With Windows, we have to deal with quote marks on our own. With Unix,
    	     * the shell takes care of quotes for us. */
    	    boolean quoted = false;
    	    for (int i=0; i<args.length; i++) {
    		if (quoted) {
    		    int len = args[i].length ();
                if (args[i].charAt (len-1) == '"') {
                    quoted = false;
                }
    		}
    		else {
    		    if (args[i].equals ("-c")) {
                    if (i < args.length-1) {
                        configFile = args[++i];
                    }
                }
    		    else if (args[i].equals ("-x")) {
                    if (i <args.length-1) {
                        saxClass = args[++i];
                    }
                }
    		    else if (args[i].charAt (0) == '"') {
                    quoted = true;
                }
    		}
        }
    
    	    /**********************************************************
    	     * Initialize the JHOVE engine.
    	     **********************************************************/
    
    	    String encoding     = null;
    	    String tempDir      = null;
    	    int    bufferSize   = -1;
    
            String moduleName   = null;
            String handlerName  = null;
            String aboutHandler = null;
            String logLevel     = "SEVERE";
            String outputFile   = null;
            boolean checksum    = false;
            boolean showRaw     = false;
            boolean signature   = false;
            List<String> list   = new ArrayList<String> ();
    
    	 
                /**********************************************************
                 * Parse command line arguments:
                 *  -m module    Module name
                 *  -h handler   Output handler
    	     *  -e encoding  Output encoding
                 *  -H handler   About handler
                 *  -o output    Output file pathname
                 *  -t tempdir   Directory for temp files
                 *  -b bufsize   Buffer size for buffered I/O
                 *  -k           Calculate checksums
                 *  -r           Display raw numeric flags 
                 *  -s           Check internal signatures only
                 *  dirFileOrUri Directories, file pathnames, or URIs
    	     *
    	     * The following arguments were defined in previous
    	     * versions, but are now obsolete
                 *  -p param     OBSOLETE
                 *  -P param     OBSOLETE
    	     **********************************************************/
    
    	    quoted = false;
    	    StringBuffer filename = null;
    
            for (int i=0; i<args.length; i++) {
                if (quoted) {
                    int len = args[i].length ();
                    if (args[i].charAt (len-1) == '"') {
                        filename.append (" " + args[i].substring (0, len-1));
                        list.add (filename.toString ());
                        quoted = false;
                    }
                    else {
                        filename.append (" " + args[i]);
                    }
                }
                else {
        		    if (args[i].equals ("-c")) {
                        i++;
        		    }
        		    else if (args[i].equals ("-m")) {
                        if (i < args.length-1) {
                            moduleName = args[++i];
                        }
        		    }
        		    else if (args[i].equals ("-p")) {
                        // Obsolete -- but eat the next arg for compatibility
                        if (i <args.length-1) {
                            @SuppressWarnings("unused")
                            String moduleParam = args[++i];
                        }
                    }
        		    else if (args[i].equals ("-h")) {
                        if (i < args.length-1) {
                            handlerName = args[++i];
                        }
                    }
        		    else if (args[i].equals ("-P")) {
                        // Obsolete -- but eat the next arg for compatibility
                        if (i <args.length-1) {
                            @SuppressWarnings("unused")
                            String handlerParam = args[++i];
                        }
        		    }
        		    else if (args[i].equals ("-e")) {
                        if (i < args.length-1) {
                            encoding = args[++i];
                        }
        		    }
        		    else if (args[i].equals ("-H")) {
                        if (i < args.length-1) {
                            aboutHandler = args[++i];
                        }
                    }
        		    else if (args[i].equals ("-l")) {
                        if (i < args.length-1) {
                            logLevel = args[++i];
                        }
        		    }
        		    else if (args[i].equals ("-o")) {
                        if (i < args.length-1) {
                            outputFile = args[++i];
                        }
                    }
        		    else if (args[i].equals ("-x")) {
                        i++;
        		    }
        		    else if (args[i].equals ("-t")) {
                        if (i <args.length-1) {
                            tempDir = args[++i];
                        }
                    }
        		    else if (args[i].equals ("-b")) {
                        if (i <args.length-1) {
                            try {
                                bufferSize = Integer.parseInt (args[++i]);
                            }
                            catch (NumberFormatException e) {
                                System.err.println ("Invalid buffer size, using default.");
                            }
                        }
        		    }
        		    else if (args[i].equals ("-k")) {
                        checksum = true;
        		    }
        		    else if (args[i].equals ("-r")) {
                        showRaw = true;
        		    }
        		    else if (args[i].equals ("-s")) {
                        signature = true;
                    }
        		    else if (args[i].charAt (0) != '-') {
                        if (args[i].charAt (0) == '"') {
                            filename = new StringBuffer ();
                            filename.append (args[i].substring (1));
                            quoted = true;
                        }
                        else {
                            list.add (args[i]);
                        }
        		    }
        		}
            }
            if (quoted) {
                list.add (filename.toString ());
    	    }
    
            JhoveBase je = new JhoveBase ();
            je.setLogLevel (logLevel);
            je.init (configFile, saxClass);
            if (encoding == null) {
                encoding = je.getEncoding ();
            }
            if (tempDir == null) {
                tempDir = je.getTempDirectory ();
            }
            if (bufferSize < 0) {
                bufferSize = je.getBufferSize ();
            }
            Module module = je.getModule  (moduleName);
            if (module == null && moduleName != null) {
                System.out.println ("Module '" + moduleName + "' not found");
                System.exit (-1);
            }
            OutputHandler about   = je.getHandler (aboutHandler);
            if (about == null && aboutHandler != null) {
                System.out.println ("Handler '" + aboutHandler + "' not found");
                System.exit (-1);
            }
    	    OutputHandler handler = je.getHandler (handlerName);
            if (handler == null && handlerName != null) {
                System.out.println ("Handler '" + handlerName + "' not found");
                System.exit (-1);
            }
    	    String [] dirFileOrUri = null;
    	    int len = list.size ();
            if (len > 0) {
        		dirFileOrUri = new String [len];
        		for (int i=0; i<len; i++) {
        		    dirFileOrUri[i] = (String) list.get (i);
        		}
            }
    
    	    /**********************************************************
    	     * Invoke the JHOVE engine.
    	     **********************************************************/
                
            je.setEncoding (encoding);
            je.setTempDirectory (tempDir);
            je.setBufferSize (bufferSize);
            je.setChecksumFlag (checksum);
            je.setShowRawFlag (showRaw);
            je.setSignatureFlag (signature);
    	    je.dispatch (app, module, about, handler, outputFile, 
    			 dirFileOrUri);
    	}
        catch (Exception e) {
            e.printStackTrace (System.err);
            System.exit (-1);
        }
    }
    

}
