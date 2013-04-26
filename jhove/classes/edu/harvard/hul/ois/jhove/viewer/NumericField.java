/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.viewer;

import javax.swing.*;
import java.text.NumberFormat;

/**
 *
 * A JTextField which permits only decimal digits
 * 
 * @author Gary McGath
 *
 */
public class NumericField extends JFormattedTextField {

    // Initializer for number format
    private static NumberFormat numFormat = 
            NumberFormat.getIntegerInstance ();
    
    public NumericField (int init)
    {
        super (numFormat);
        numFormat.setGroupingUsed (false);
        numFormat.setParseIntegerOnly (true);
        setValue (new Integer (init));
    }
}
