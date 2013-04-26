/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2005 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

/**
 * Container for a PDF stream filter.
 *
 * @author Gary McGath
 *
 */
public class Filter {

    private String _filterName;
    private PdfDictionary _decodeParms;
    
    /**
     *  Constructor.
     * 
     *  @param name   The name of the filter.
     */
    public Filter (String name)
    {
        _filterName = name;
    }
    
    /** Returns the name of the filter. */
    public String getFilterName ()
    {
        return _filterName;
    }
    
    /** Returns the DecodeParms dictionary, or null if there is none. */
    public PdfDictionary getDecodeParms ()
    {
        return _decodeParms;
    }
    
    /** Returns the "Name" parameter of the filter, or <code>null</code>
     *  if there is no such parameter.
     *  This is normally associated with a Crypt filter, and
     *  shouldn't be confused with the name of the filter.
     */
    public String getNameParam ()
    {
        try {
            if (_decodeParms != null) {
                PdfSimpleObject obj = 
                    (PdfSimpleObject) _decodeParms.get ("Name");
                return obj.getStringValue();
            }
        }
        catch (Exception e) {
        }
        return null;
    }
    
    /** Stores the DecodeParms or FDecodeParms dictionary
     *  which is associated with this filter. */
    public void setDecodeParms (PdfDictionary parms)
    {
        _decodeParms = parms;
    }
}
