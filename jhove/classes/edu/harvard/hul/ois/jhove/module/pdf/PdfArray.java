/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.util.*;

/**
 *  A representation of a PDF array object.
 */
public class PdfArray extends PdfObject
{

        private Vector<PdfObject> _content;

    /** 
     *  Creates a PdfArray object.
     *
     *  @param objNumber  The PDF object number
     *  @param genNumber  The PDF generation number
     */
    public PdfArray (int objNumber, int genNumber)
    {
        super (objNumber, genNumber);
        _content = new Vector<PdfObject> ();
    }

    /** 
     *  Creates a PdfArray object with empty contents.
     *
     */
    public PdfArray ()
    {
        super ();
        _content = new Vector<PdfObject> ();
    }

    /**
     *  Adds an object to the array.
     */
    public void add (PdfObject obj) 
    {
        _content.add (obj);
    }
    
    /**
     *  Return the contents of the array as a Vector.
     */
    public Vector<PdfObject> getContent ()
    {
        return _content;
    }
    
    /** Report if it's within implementation limits defined for PDF/A. */
    public boolean isPdfACompliant ()
    {
        return _content.size() <= 8191;
    }

    /**
     *  Concatenate the elements, if they are PdfSimpleObjects,
     *  into a string separated by spaces.  Return an empty string
     *  if there are no PdfSimpleObjects.
     */
    public String toPipeline ()
    {
        StringBuffer sb = new StringBuffer ();
        for (int i = 0; i < _content.size (); i++) {
            PdfObject elem = (PdfObject) _content.elementAt (i);
            if (elem instanceof PdfSimpleObject) {
                String elemval = ((PdfSimpleObject) elem).getStringValue ();
                // separate items with a space
                if (sb.length () > 0) {
                    sb.append (' ');
                }
                sb.append (elemval);
            }
        }
        return sb.toString ();
    }
    
    /**
     *  Attempts to convert this Array to a PDF rectangle.
     *  If the Array is a valid rectangle (i.e., an array of exactly
     *  four numbers), returns a Java array of four doubles reflecting
     *  the rectangle.  Otherwise returns null.
     */
    public double[] toRectangle ()
    {
        if (_content.size () != 4) {
            return null;
        }
        double[] retval = new double[4];
        try {
            for (int i = 0; i < 4; i++) {
                PdfObject elem = (PdfObject) _content.elementAt (i);
                if (elem instanceof PdfSimpleObject) {
                    double d = ((PdfSimpleObject) elem).getDoubleValue ();
                    retval[i] = d;
                }
                else {
                    return null;
                }
            }
            return retval;
        }
        catch (Exception e) {
            // Any failure (e.g., a ClassCastException) is assumed to mean
            // it wasn't a proper Rectangle
            return null;
        }
    }
}
