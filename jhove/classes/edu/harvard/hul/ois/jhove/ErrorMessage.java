/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  This class encapsulates an error message from a Module, representing
 *  a problem in the content being analyzed. 
 */
public class ErrorMessage
    extends Message
{
    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /** 
     *  Create an ErrorMessage.
     *  @param  message   Human-readable string describing the problem.
     */
    public ErrorMessage (String message)
    {
	super (message);
    }

    /** 
     *  Create an ErrorMessage.
     *  @param  message   Human-readable string describing the problem.
     *  @param  offset    The offset in the file at which the problem
     *                    was detected.
     */
    public ErrorMessage (String message, long offset)
    {
	super (message, offset);
    }
    /** 
     *  Create an ErrorMessage.
     *  @param  message   Human-readable string describing the problem.
     */
    public ErrorMessage (String message, String subMessage)
    {
        super (message, subMessage);
    }

    /** 
     *  Create an ErrorMessage.
     *  @param  message   Human-readable string describing the problem.
     *  @param  subMessage Human-readable additional information.
     *  @param  offset    The offset in the file at which the problem
     *                    was detected.
     */
    public ErrorMessage (String message, String subMessage, long offset)
    {
        super (message, subMessage, offset);
    }
}
