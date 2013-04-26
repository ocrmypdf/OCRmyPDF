/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

/**
 *  The abstract superclass for all representations of objects
 *  in PDF files.  Objects may be created using the obj syntax,
 *  in which case they have an object and generation number, or
 *  they may be parts of other objects, in which case they don't.
 *  All subclasses should implement a constructor 
 *  which has the object and generation
 *  numbers as its last two arguments, and one which has the
 *  same arguments except for omitting these two.
 */
public abstract class PdfObject
{
    /** PDF object number.   */
    protected int _objNumber;
    
    /** PDF generation number. */
    protected int _genNumber;

    /** 
     *  Superclass constructor which should be called for all
     *  PdfObject instances that include an object and generation
     *  number.
     *
     *  @param objNumber  The PDF object number
     *  @param genNumber  The PDF generation number
     */
    public PdfObject (int objNumber, int genNumber)
    {
        _objNumber = objNumber;
        _genNumber = genNumber;
    }

    /** 
     *  Superclass constructor for which the object and generation
     *  number will be added separately or not at all.  Initializes
     *  the object and generation numbers to -1 to signify their
     *  absence.
     */
    public PdfObject ()
    {
        _objNumber = -1;
        _genNumber = -1;
    }

    /** Returns the PDF object number.  If the object wasn't
        given an object number, returns -1. */
    public int getObjNumber ()
    {
        return _objNumber;
    }

    /** Returns the PDF generation number.   If the object wasn't
        given a generation number, returns -1.  */
    public int getGenNumber ()
    {
        return _genNumber;
    }
    
    /** Sets the PDF object number. */
    public void setObjNumber (int num) 
    {
        _objNumber = num;
    }

    /** Sets the PDF generation number. */
    public void setGenNumber (int num) 
    {
        _genNumber = num;
    }
}
