/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  This class encapsulates a String to be displayed. 
 */
public abstract class Message
{
    /******************************************************************
     * PUBLIC CLASS FIELDS.
     ******************************************************************/

    /** Value indicating a null offset. */
    public static final long NULL = -1;

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /** Message text. */
    protected String _message;
    
    /** Additional information. */
    protected String _subMessage;
    
    /** Byte offset to which message applies. */
    protected long _offset;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *  Create a Message.  This constructor cannot be invoked directly,
     *                     since Message is abstract.
     *  @param  message   Human-readable string.
     */
    protected Message (String message)
    {
	init (message, null, NULL);
    }

    /**
     *  Create a Message.  This constructor cannot be invoked directly,
     *                     since Message is abstract.  The second argument
     *                     adds secondary details to the primary message;
     *                     the message will typically be displayed in the
     *                     form "message:subMessage".
     *  @param  message    Human-readable string.
     *  @param  subMessage Human-readable additional information.
     */
    protected Message (String message, String subMessage)
    {
	init (message, subMessage, NULL);
    }

    /**
     *  Create a Message.  This constructor cannot be invoked directly,
     *                     since Message is abstract.  The second argument
     *                     adds secondary details to the primary message;
     *                     the message will typically be displayed in the
     *                     form "message:subMessage".
     *  @param  message    Human-readable string.
     *  @param  offset     Byte offset associated with the message.
     */
    protected Message (String message, long offset)
    {
	init (message, null, offset);
    }

    /**
     *  Create a Message.  This constructor cannot be invoked directly,
     *                     since Message is abstract.  The second argument
     *                     adds secondary details to the primary message;
     *                     the message will typically be displayed in the
     *                     form "message:subMessage".
     *  @param  message    Human-readable string.
     *  @param  subMessage Human-readable additional information.
     *  @param  offset     Byte offset associated with the message.
     */
    protected Message (String message, String subMessage, long offset)
    {
	init (message, subMessage, offset);
    }

    /**
     * Initialize the <tt>Message</tt> object.
     *  @param  message    Human-readable string.
     *  @param  subMessage Human-readable additional information.
     */
    private void init (String message, String subMessage, long offset)
    {
        _message    = message;
        _subMessage = subMessage;
	_offset     = offset;
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     *
     * Accessor methods.
     ******************************************************************/

    /**
     *  Get the message string.
     */
    public String getMessage ()
    {
        return _message;
    }

    /**
     *  Get the submessage string.
     */
    public String getSubMessage ()
    {
        return _subMessage;
    }

    /**
     *  Return the offset to which the information is related.
     */
    public long getOffset ()
    {
	return _offset;
    }
}
