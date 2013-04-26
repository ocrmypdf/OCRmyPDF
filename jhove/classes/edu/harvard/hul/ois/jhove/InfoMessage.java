/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  This class encapsulates an informational message from a Module, giving
 *  information (not necessarily a problem)
 *  about the content being analyzed or the way that Jhove
 *  deals with it. 
 */
public class InfoMessage
    extends Message
{
    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** 
     *  Create an InfoMessage.
     *  @param  message   Human-readable string giving the information.
     */
    public InfoMessage (String message)
    {
	super (message);
    }

    /** 
     *  Create an InfoMessage.
     *  @param  message   Human-readable string giving the information.
     *  @param  offset    The offset in the file relevant to the
     *                    situation being described
     */
    public InfoMessage (String message, long offset)
    {
	super (message, offset);
    }

    /** 
     *  Create an InfoMessage.
     *  @param  message   Human-readable string giving the information.
     *  @param  subMessage Human-readable additional information.
     */
    public InfoMessage (String message, String subMessage)
    {
        super (message, subMessage);
    }

    /** 
     *  Create an InfoMessage.
     *  @param  message   Human-readable string giving the information.
     *  @param  subMessage Human-readable additional information.
     *  @param  offset    The offset in the file relevant to the
     *                    situation being described
     */
    public InfoMessage (String message, String subMessage, long offset)
    {
        super (message, subMessage, offset);
    }
}
