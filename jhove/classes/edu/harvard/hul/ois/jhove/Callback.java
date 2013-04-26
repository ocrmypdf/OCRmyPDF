/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  An interface for supporting a general, simple callback function.
 */
public interface Callback 
{
    /**
     *  A generic callback function.  Any class which needs to support
     *  callback can implement callback and pass a reference to itself
     *  to the function that does the callback.
     *
     *  @param  selector  An indicator of the function to be performed.
     *                    Interpretation is determined by the implementing class.
     *  @param  parm      Whatever data may be appropriate to the callback.
     *
     *  @return          As specified by the implementing class.
     */
    public int callback (int selector, Object parm);
}
