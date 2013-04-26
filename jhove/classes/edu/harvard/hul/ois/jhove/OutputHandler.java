/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.io.*;
import java.util.*;

/**
 * Public interface for Jhove output handlers.
 * All output handlers must implement OutputHandler, and in 
 * normal cases should subclass HandlerBase.
 */
public interface OutputHandler
{
    
    /**
     * Reset the handler. This needs to be called before each invocation.
     */
    public void reset ();

    /**
     * Callback allowing post-parse, pre-show analysis of object
     * representation information.
     * @param info Object representation information
     */
    public void analyze (RepInfo info);

    /**
     * Callback indicating a directory is finished being processed.
     * Most handlers will do nothing.
     */
    public void endDirectory ();

    /**
     *  Returns the name of this handler
     */
    public String getName ();
    /**
     *  Returns release information for this handler
     */
    public String getRelease ();

    /**
     *  Returns the last modification date of this handler
     */
    public Date getDate ();

    /**
     *  Returns a List of Document objects giving the format
     *  specification documentation
     *
     *  @see Document
     */
    public List<Document> getSpecification ();

    /**
     *  Returns a List of Agent objects giving the vendor(s)
     *  of this handler.
     */
    public Agent getVendor ();

    /**
     *  Returns this handler's note
     */
    public String getNote ();

    /**
     *  Returns this handler's copyright information
     */
    public String getRights ();

    /**
     *  Returns this handler's encoding.
     */
    public String getEncoding ();

    /**
     * Per-instantiation initialization.
     *
     * @param init    Initialization parameter.  This is typically obtained
     *                from the configuration file.
     */
    public void init (String init)
	throws Exception;

    /**
     * Callback to give the handler the opportunity to decide whether or
     * not to process a file.  Most handlers will always return true.
     * @param filepath File pathname
     */
    public boolean okToProcess (String filepath);

    /**
     * Sets list of default parameters.
     * 
     * @param   params     A List whose elements are Strings.
     *                     May be empty.
     */
    public void setDefaultParams (List<String> params);


    /**
     *  Applies the default parameters.
     */
    public void applyDefaultParams ()
        throws Exception;
    
    /** Reset parameter settings.
     *  Returns to a default state without any parameters.
     */
    public void resetParams ()
        throws Exception;

    /**
     * Per-action initialization.
     *
     * @param param   Initialization parameter.
     */
    public void param (String param)
	throws Exception;

    /**
     *  Assigns an application object to provide services to this handler
     */
    public void setApp (App app);

    /**
     *  Assigns the JHOVE engine object to provide services to this handler
     */
    public void setBase (JhoveBase je);

    /**
     *  Assigns the encoding to be used by this OutputHandler
     */
    public void setEncoding (String encoding);

    /**
     *  Assigns a PrintWriter to do output for this OutputHandler
     */
    public void setWriter (PrintWriter output);

    /**
     *  Outputs information about a Module
     */
    public void show (Module module);

    /**
     *  Outputs the information contained in a RepInfo object
     */
    public void show (RepInfo info);

    /**
     *  Outputs information about the OutputHandler specified
     *  in the parameter 
     */
    public void show (OutputHandler handler);

    /**
     *  Outputs minimal information about the application
     */
    public void show ();

    /**
     *  Outputs detailed information about the application,
     *  including configuration, available modules and handlers,
     *  etc.
     */
    public void show (App app);

    /**
     *  Do the initial output.  This should be in a suitable format
     *  for including multiple files between the header and the footer. 
     */
    public void showHeader ();

    /**
     *  Do the final output.  This should be in a suitable format
     *  for including multiple files between the header and the footer. 
     */
    public void showFooter ();

    /**
     *  Do appropriate finalization after all output is complete.
     */
    public void close ();

    /**
     * Callback indicating a new directory is being processed.
     * Most handlers will do nothing.
     * @param directory Directory path
     */
    public void startDirectory (String directory);
}
