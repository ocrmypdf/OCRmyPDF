/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-4 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.io.*;
import java.util.*;

/**
 *  Module for identification of a document.  "Identification"
 *  means determining, by querying modules successively, what the format
 *  of a document is.  The Bytestream module is always queried last,
 *  so a document will by identified as a Bytestream if all else fails.
 */
public class ObjectIdentifier
{
    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    private List _moduleList;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/
    public ObjectIdentifier (List moduleList) 
    {
	_moduleList = moduleList;
    }


    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     *
     * Processing methods.
     *
     ******************************************************************/

    /**
     *  Perform identification on a file.  The file is parsed by
     *  each of the modules in the module list until one
     *  declares that the file is well-formed. It is assumed
     *  that there is a module in the list (normally Bytestream
     *  at the end) which will always consider a file well-formed.
     */
    public void identify (File file, RepInfo info, 
			  String parm, boolean verbose,
			  boolean shortCheck) 
	                 throws IOException 
    {
	/******************************************************
	 *  Go through all modules, in the order in the config
	 *  file, calling the parse method till we find one 
         *  which matches.
	 ******************************************************/

	ListIterator modIter = _moduleList.listIterator();
	while (modIter.hasNext ()) {
	    /* We need clean RepInfo for each run */
	    RepInfo info1;
	    info1 = (RepInfo) info.clone ();

	    Module mod = (Module) modIter.next ();
	    try {
                if (!mod.hasFeature("edu.harvard.hul.ois.jhove.canValidate")) {
                    continue;
                }
		if (mod.isRandomAccess ()) {
                    RandomAccessFile raf = 
                        new RandomAccessFile (file, "r");
                    mod.param (parm);
                    if (verbose) {
                        mod.setVerbosity (Module.MAXIMUM_VERBOSITY);
                    }
                    if (shortCheck) {
                        mod.checkSignatures (file, raf, info1);
                    }
                    else {
                        mod.parse (raf, info1);
                    }
                    raf.close ();
                }
		else {
		    InputStream stream = new FileInputStream (file);
		    mod.param (parm);
		    if (shortCheck) {
		        mod.checkSignatures (file, stream, info1);
		    }
		    else {
                        int parseIndex = mod.parse (stream, info1, 0);
                        while (parseIndex != 0) {
                            stream.close ();
                            stream = new FileInputStream (file);
                            parseIndex = mod.parse (stream, info1, parseIndex);
                        }
		    }
		    stream.close ();
		}
	    }
            catch (Exception e) {
		/*  The assumption is that in trying to analyze
		    the wrong type of file, the module may go
		    off its track and throw an exception, so we
		    just continue on to the next module.
		*/
            continue;
	    }
	    if (info1.getWellFormed () == RepInfo.TRUE) {
               info.copy (info1);
               break;
	    }
	}
    }

    
}
