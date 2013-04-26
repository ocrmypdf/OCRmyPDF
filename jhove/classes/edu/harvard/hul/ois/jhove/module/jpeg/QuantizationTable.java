/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg;

import edu.harvard.hul.ois.jhove.*;

/**
 * Encapsulation of a quantization table entry for a JPEG image.
 * 
 * @author Gary McGath
 *
 */
public class QuantizationTable {

    private int _precision;
    private int _destIdentifier;


    /**
     *   Constructor.
     */
    public QuantizationTable(int precision, int destIdentifier) {
        _precision = precision;
        _destIdentifier = destIdentifier;
    }


    /**
     *  Returns a Property defining the quantization table
     */
    public Property makeProperty (boolean raw)
    {
        Property[] parray = new Property[2];
        if (raw) {
            parray[0] = new Property ("Precision",
                    PropertyType.INTEGER,
                    new Integer (_precision));
        }
        else {
            String prec = "Undefined";
            try {
                prec = JpegStrings.DQT_PRECISION[_precision];
            }
            catch (Exception e) {}
            parray[0] = new Property ("Precision",
                    PropertyType.STRING,
                    prec);
        }
        parray[1] = new Property ("DestinationIdentifier",
                PropertyType.INTEGER,
                new Integer (_destIdentifier));
        return new Property ("QuantizationTable",
                PropertyType.PROPERTY,
                PropertyArity.ARRAY,
                parray);
    }
}
