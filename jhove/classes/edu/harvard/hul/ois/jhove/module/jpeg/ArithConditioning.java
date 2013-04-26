/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg;

import edu.harvard.hul.ois.jhove.*;

/**
 * Encapsulation of an arithmetic conditioning entry for a JPEG image.
 * 
 * @author Gary McGath
 *
 */
public class ArithConditioning {

    private int _tableClass;
    private int _destIdentifier;


    /**
     *   Constructor.
     */
    public ArithConditioning(int tableClass, int destIdentifier) {
        _tableClass = tableClass;
        _destIdentifier = destIdentifier;
    }


    /**
     *  Returns a Property defining the conditioning data
     */
    public Property makeProperty (boolean raw)
    {
        Property[] parray = new Property[2];
        if (raw) {
            parray[0] = new Property ("TableClass",
                    PropertyType.INTEGER,
                    new Integer (_tableClass));
        }
        else {
            String prec = "Undefined";
            try {
                prec = JpegStrings.DAC_CLASS[_tableClass];
            }
            catch (Exception e) {}
            parray[0] = new Property ("Precision",
                    PropertyType.STRING,
                    prec);
        }
        parray[1] = new Property ("DestinationIdentifier",
                PropertyType.INTEGER,
                new Integer (_destIdentifier));
        return new Property ("ArithmeticConditioning",
                PropertyType.PROPERTY,
                PropertyArity.ARRAY,
                parray);
    }

}
