/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

/**
 *  This class defines enumerated types for the analog/digital
 *  flag of AESAudioMetadata. 
 *  Applications will not create or modify instances of this class, but will
 *  use one of the predefined AnalogDigitalFlagType instances.
 * 
 * @author Gary McGath
 *
 */
public class AnalogDigitalFlagType extends EnumerationType {

    /** Enumeration instance for analog data */
    public static final AnalogDigitalFlagType ANALOG = 
        new AnalogDigitalFlagType ("ANALOG");

    /** Enumeration instance for physical digital data */
    public static final AnalogDigitalFlagType PHYS_DIGITAL = 
        new AnalogDigitalFlagType ("PHYS_DIGITAL");

    /** Enumeration instance for FILE digital data */
    public static final AnalogDigitalFlagType FILE_DIGITAL = 
        new AnalogDigitalFlagType ("FILE_DIGITAL");

    /** 
     *  Applications will never create PropertyTypes directly.
     **/
    private AnalogDigitalFlagType (String value)
    {
        super (value);
    }

}
