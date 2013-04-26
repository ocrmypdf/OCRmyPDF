/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004-2008 by JSTOR and the President and Fellows of Harvard College
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
import edu.harvard.hul.ois.jhove.viewer.*;
import javax.swing.*;

/**
 * JhoveView - JSTOR/Harvard Object Validation Environment.
 */
public class JhoveView
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     *
     * Application constants.
     ******************************************************************/

    /** Application name. */
    private static final String NAME = "JhoveView";

    /** Application build date, YYYY, MM, DD. */
    private static int [] _date;

    /** Usage string is meaningless here. */
    private static final String USAGE = null;
    
    /** Application release number. */
    private static String _release;

    /** Default character encoding */
    //private static final String DEFAULT_ENCODING = "UTF-8";

    /** Copyright information. */
    private static final String RIGHTS = 
        "Derived from software Copyright 2004-2011 " +
        "by the President and Fellows of Harvard College. " +
        "Version 1.7 and higher independently released. " +
    	"Released under the GNU Lesser General Public License.";

    /******************************************************************
     * Configuration constants.
     ******************************************************************/

    /** Configuration file property. */
//    private static final String CONFIG_PROPERTY = "edu.harvard.hul.ois." +
//                                                  "jhove.config";
    /** Jhove directory */
//    private static final String JHOVE_DIR = "jhove";

    /** Config directory */
//    private static final String CONFIG_DIR = "conf";

    /** SAX parser class property. */
//    private static final String SAX_PROPERTY = "edu.harvard.hul.ois.jhove." +
//                                               "saxClass";

    /******************************************************************
     * Action constants.
     ******************************************************************/

    /******************************************************************
     * Exit code constants.
     ******************************************************************/

    /** General error. */
    private static final int ERROR = -1;

    /** Incompatible Java VM. */
    private static final int INCOMPATIBLE_VM = -2;

    /** File not writable. */
    //private static final int FILE_NOT_WRITABLE = -11;

    /** No module specified. */
    //private static final int NO_MODULE = -21;

    /** Module not found. */
    //private static final int MODULE_NOT_FOUND = -22;

    /** Output handler not found. */
    //private static final int HANDLER_NOT_FOUND = -31;

    /** No object specified. */
    //private static final int NO_OBJECT = -41;

    /** URL not accessible. */
    //private static final int URL_NOT_ACCESSIBLE = -42;

    /** File not found. */
    //private static final int FILE_NOT_FOUND = -43;

    /** File not readable. */
    //private static final int FILE_NOT_READABLE = -44;

    /** SAX parser not found. */
    //private static final int PARSER_NOT_FOUND = -51;
    

    /******************************************************************
     * PUBLIC CLASS METHODS.
     ******************************************************************/

    /**
     *  Stub constructor.
     */

    private JhoveView ()
    {
    }

    /**
     * Application main entry point.
     * @parm args Command line arguments
     */
    public static void main (String [] args)
    {
        _release = JhoveBase._release;     // Seems safer than final init
        _date = JhoveBase.DATE;
        /* Make sure we have a satisfactory version of Java. */
        String version = System.getProperty ("java.vm.version");
        if (version.compareTo ("1.4.0") < 0) {
            //System.err.println (NAME + ": Java 1.4 or higher is required");
            errorAlert ("Java 1.4 or higher is required");
            System.exit (INCOMPATIBLE_VM);
        }

        // If we're running on a Macintosh, put the menubar at the top
        // of the screen where it belongs.
        System.setProperty ("apple.laf.useScreenMenuBar", "true");

        App app = new App (NAME, _release, _date, USAGE, RIGHTS);
        try {

            /**********************************************************
             * Retrieve the configuration file.
             **********************************************************/
    
            String configFile = JhoveBase.getConfigFileFromProperties ();
            String saxClass   = JhoveBase.getSaxClassFromProperties ();

            /**********************************************************
             * Initialization:
             *  configFile  Configuration file pathname
             *  saxClass    SAX parser class
             **********************************************************/

	    /* Pre-parse the command line for -c and -x config options. */
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
    
            JhoveBase je = new JhoveBase ();
            try {
                je.init (configFile, saxClass);
            }
            catch (JhoveException e) {
                errorAlert (e.getMessage ());
                // Keep going, so user can correct in editor
            }

            // Create the main window to select a file.
            
            JhoveWindow jwin = new JhoveWindow (app, je);
            jwin.setVisible (true);

        }
        catch (Exception e) {
            e.printStackTrace (System.err);
            System.exit (ERROR);
        }
    }
    
    /* Displays an error alert. */
    private static void errorAlert (String msg)
    {
        JFrame hiddenFrame = new JFrame ();
        // Truncate long messages so the alert isn't wider
        // than the screen
        if (msg.length() > 80) {
            msg = msg.substring (0, 79) + "...";
        }
        JOptionPane.showMessageDialog (hiddenFrame, 
            msg, "Jhove Error", JOptionPane.ERROR_MESSAGE);
    }
}
