/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

/**
 *  A class which encapsulates a file specification in PDF.  A file
 *  specification may be given as either a string or a dictionary.
 *  The specification is converted to a string according to the following
 *  rules:  If a PDF string object is the file specifier, that string
 *  is used, without attempting to convert file separators to the local
 *  file system.  If a PDF dictionary is used, one of the following is
 *  used, in decreasing order of preference:
 *
 *  <UL>
 *    <LI>The system-neutral file specification string
 *    <LI>The Unix file specification string
 *    <LI>The DOS file specification string
 *    <LI>The Macintosh file specification string
 *  </UL>
 */
public class FileSpecification 
{
    String _specString;
    PdfObject _sourceObject;
    
    /**
     *  Constructor.
     * 
     *  @param  obj  A PdfDictionary with the file specification under the
     *               key "F", "Unix", "DOS", or "Mac"; or
     *               a PdfSimpleObject whose string value is the
     *               file specification.  If <code>obj</code> is
     *               a dictionary and more than one key is specified,
     *               then the first of the keys F, Unix, DOS, and Mac
     *               to be found is used.
     */
    public FileSpecification (PdfObject obj) throws PdfException
    {
        try {
            _sourceObject = obj;
            if (obj instanceof PdfDictionary) {
                PdfDictionary dictObj = (PdfDictionary) obj;
                PdfSimpleObject pathObj;
                pathObj = (PdfSimpleObject) dictObj.get ("F");
                if (pathObj == null) {
                    pathObj = (PdfSimpleObject) dictObj.get ("Unix");
                }
                if (pathObj == null) {
                    pathObj = (PdfSimpleObject) dictObj.get ("DOS");
                }
                if (pathObj == null) {
                    pathObj = (PdfSimpleObject) dictObj.get ("Mac");
                }
                if (pathObj != null) {
                    _specString = pathObj.getStringValue ();
                }
            }
            else if (obj instanceof PdfSimpleObject) {
                _specString = ((PdfSimpleObject) obj).getStringValue ();
            }
        }
        catch (ClassCastException e) {
            throw new PdfInvalidException ("Invalid file specification");
        }
    }
    
    /**
     *  Returns the file specification as a string.  
     */
    public String getSpecString ()
    {
        return _specString;
    }
    
    
    /**
     *   Returns the PdfObject from which the file specification was created.
     */
    public PdfObject getSourceObject ()
    {
	return _sourceObject;
    }
}
