/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003-2004 by JSTOR and the President and Fellows of Harvard College
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or (at
 * your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
 * USA
 **********************************************************************/

package edu.harvard.hul.ois.jhove.handler;

import edu.harvard.hul.ois.jhove.*;
import java.text.*;
import java.util.*;

/**
 *  OutputHandler for plain text output.
 */
public class TextHandler
    extends HandlerBase
{
    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    private static final String NAME = "TEXT";
    private static final String RELEASE = "1.5";
    private static final int [] DATE = {2009, 10, 14};
    private static final String NOTE = "This is the default JHOVE output " +
        "handler";
    private static final String RIGHTS = "Copyright 2003-2009 by JSTOR and " +
        "the President and Fellows of Harvard College. " +
        "Released under the terms of the GNU Lesser General Public License.";

    private NumberFormat _format;


    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /* Sample rate. */
    private double _sampleRate;

    /******************************************************************
     * CLASS CONSTRUCTOR.
     ******************************************************************/

    /**
     *  Creates a TextHandler.
     */
    public TextHandler ()
    {
        super (NAME, RELEASE, DATE, NOTE, RIGHTS);
        Agent agent = new Agent ("Harvard University Library",
                                 AgentType.EDUCATIONAL);
        agent.setAddress ("Office for Information Systems, " +
                          "90 Mt. Auburn St., " +
                          "Cambridge, MA 02138");
        agent.setTelephone ("+1 (617) 495-3724");
        agent.setEmail("jhove-support@hulmail.harvard.edu");
        _vendor = agent;

        _format = NumberFormat.getInstance ();
        _format.setGroupingUsed (false);
        _format.setMinimumFractionDigits (0);
    }

    /******************************************************************
     * PUBLIC INSTANCE METHODS.
     ******************************************************************/

    /**
     *  Outputs minimal information about the application
     */
    public void show ()
    {
        String margin = getIndent (++_level);

        _level--;
    }

    /**
     *  Outputs detailed information about the application,
     *  including configuration, available modules and handlers,
     *  etc.
     */
    public void show (App app)
    {
        String margin = getIndent (++_level);

	_writer.println (margin + "App:");
	_writer.println (margin + " API: " + _je.getRelease () + ", " +
			     HandlerBase.date.format (_je.getDate ()));
	String configFile = _je.getConfigFile ();
	if (configFile != null) {
	    _writer.println (margin + " Configuration: " + configFile );
	}
	String s = _je.getSaxClass ();
	if (s != null) {
	    _writer.println (margin + " SAXparser: " + s );
	}
	s = _je.getJhoveHome ();
	if (s != null) {
	    _writer.println (margin + " JhoveHome: " + s);
	}
	s = _je.getEncoding ();
	if (s != null) {
	    _writer.println (margin + " Encoding: " + s);
	}
	s = _je.getTempDirectory ();
	if (s != null) {
	    _writer.println (margin + " TempDirectory: " + s);
	}
	_writer.println (margin + " BufferSize: " + _je.getBufferSize ());
        Iterator iter = _je.getModuleMap ().keySet ().iterator ();
        while (iter.hasNext ()) {
            Module module = _je.getModule ((String) iter.next ());
            _writer.println (margin + " Module: " + module.getName () + " " +
			     module.getRelease ());
        }
        iter = _je.getHandlerMap ().keySet ().iterator ();
        while (iter.hasNext ()) {
            OutputHandler handler = _je.getHandler ((String) iter.next ());
            _writer.println (margin + " OutputHandler: " +
                             handler.getName () + " " +
			     handler.getRelease ());
        }

        _writer.println (margin + " Usage: "  + app.getUsage  ());
        _writer.println (margin + " Rights: " + app.getRights ());

        _level--;
    }

    /**
     *  Outputs information about the OutputHandler specified
     *  in the parameter 
     */
    public void show (OutputHandler handler)
    {
        String margin = getIndent (++_level);

        _writer.println(margin + "Handler: " + handler.getName ());
        _writer.println (margin + " Release: " + handler.getRelease ());
        _writer.println (margin + " Date: " +
                         HandlerBase.date.format (handler.getDate ()));
        List<Document> list = handler.getSpecification ();
        int n = list.size ();
        for (int i=0; i<n; i++) {
            showDocument ( list.get (i), "Specification");
        }
        Agent vendor = handler.getVendor ();
        if (vendor != null) {
            showAgent (vendor, "Vendor");
        }
        String s;
        if ((s = handler.getNote ()) != null) {
            _writer.println (margin + " Note: " + s);
        }
        if ((s = handler.getRights ()) != null) {
            _writer.println (margin + " Rights: " + s);
        }
    }


    /**
     *  Outputs information about a Module
     */
    public void show (Module module)
    {
        String margin = getIndent (++_level);

        _writer.println (margin + "Module: " + module.getName ());
        _writer.println (margin + " Release: " + module.getRelease ());
        _writer.println (margin + " Date: " +
                         HandlerBase.date.format (module.getDate ()));
        String [] ss = module.getFormat ();
        if (ss.length > 0) {
            _writer.print (margin + " Format: " + ss[0]);
            for (int i=1; i<ss.length; i++) {
                _writer.print (", " + ss[i]);
            }
            _writer.println ();
        }
        String s = module.getCoverage ();
        if (s != null) {
            _writer.println (margin + " Coverage: " + s);
        }
        ss = module.getMimeType ();
        if (ss.length > 0) {
            _writer.print (margin + " MIMEtype: " + ss[0]);
            for (int i=1; i<ss.length; i++) {
                _writer.print (", " + ss[i]);
            };
            _writer.println ();
        }
        List list = module.getSignature ();
        int n = list.size ();
        for (int i=0; i<n; i++) {
            showSignature ((Signature) list.get (i));
        }
        list = module.getSpecification ();
        n = list.size ();
        for (int i=0; i<n; i++) {
            showDocument ((Document) list.get (i), "Specification");
        }
        List<String> ftr = module.getFeatures ();
        if (ftr != null) {
            Iterator<String> iter = ftr.iterator();
            while (iter.hasNext ()) {
                s = iter.next ();
                _writer.println (margin + "  Feature: " + s);
            }
        }

        _writer.println (margin + " Methodology:");
        if ((s = module.getWellFormedNote ()) != null) {
            _writer.println (margin + "  Well-formed: " + s);
        }
        if ((s = module.getValidityNote ()) != null) {
            _writer.println (margin + "  Validity: " + s);
        }
        if ((s = module.getRepInfoNote ()) != null) {
            _writer.println (margin + "  RepresentationInformation: " + s);
        }
        Agent vendor = module.getVendor ();
        if (vendor != null) {
            showAgent (vendor, "Vendor");
        }
        if ((s = module.getNote ()) != null) {
            _writer.println (margin + " Note: " + s);
        }
        if ((s = module.getRights ()) != null) {
            _writer.println (margin + " Rights: " + s);
        }

        _level--;
    }

    /**
     *  Outputs the information contained in a RepInfo object
     */
    public void show (RepInfo info)
    {
        String margin = getIndent (++_level);

        Module module = info.getModule ();
        _writer.println (margin + "RepresentationInformation: " +
                         info.getUri ());
        if (module != null) {
            _writer.println (margin + " ReportingModule: " + module.getName() +
                             ", Rel. " + module.getRelease () + " (" +
                             date.format (module.getDate ()) + ")");
        }

        Date date = info.getCreated ();
        if (date != null) {
            _writer.println (margin + " Created: " + dateTime.format (date));
        }
        date = info.getLastModified ();
        if (date != null) {
            _writer.println (margin + " LastModified: " +
                             dateTime.format (date));
        }
        long size = info.getSize ();
        if (size > -1) {
            _writer.println (margin + " Size: " + size);
        }
        String s = info.getFormat ();
        if (s != null) {
            _writer.println (margin + " Format: " + s);
        }
        s = info.getVersion ();
        if (s != null) {
            _writer.println (margin + " Version: " + s);
        }
        if (!_je.getSignatureFlag ()) {
            _writer.print (margin + " Status: ");
            switch (info.getWellFormed ()) {
                case RepInfo.TRUE:
                s = "Well-Formed";
                break;
                
                case RepInfo.FALSE:
                s = "Not well-formed";
                break;
                
                default:
                s = "Unknown";
                break;
            }
            if (info.getWellFormed () == RepInfo.TRUE) {
                switch (info.getValid ()) {
                    
                    case RepInfo.TRUE:
                    s += " and valid";
                    break;
                
                    case RepInfo.FALSE:
                    s += ", but not valid";
                    break;
                    
                    // case UNDETERMINED: add nothing
                }
            }
            _writer.println (s);
        }
        else {
            // If we aren't checking signatures, we still need to say something.
            _writer.print (margin + " Status: ");
            switch (info.getWellFormed ()) {
                case RepInfo.TRUE:
                    s = "Well-Formed";
                    break;
                    
                    default:
                    s = "Not well-formed";
                    break;
            }
            _writer.println (s);
        }
        List list = info.getSigMatch();
        int n = list.size ();
        if (n > 0) {
            _writer.println (margin + " SignatureMatches:");
            for (int i = 0; i < n; i++) {
                _writer.println (margin + "  " + 
                        (String) list.get (i));
            }
        }

        list = info.getMessage ();
        n = list.size ();
        for (int i=0; i<n; i++) {
            showMessage ((Message) list.get (i));
        }
        s = info.getMimeType ();
        if (s != null) {
            _writer.println (margin + " MIMEtype: " + s);
        }

        list = info.getProfile ();
        n = list.size ();
        if (n > 0) {
            _writer.print (margin + " Profile: " + (String) list.get (0));
            for (int i=1; i<n; i++) {
                _writer.print (", " + (String) list.get (i));
            }
            _writer.println ();
        }

        Map map = info.getProperty ();
        if (map != null) {
            Iterator iter = map.keySet ().iterator ();
            while (iter.hasNext ()) {
                String key = (String) iter.next ();
                showProperty (info.getProperty (key), key, margin);
            }
        }

        list = info.getChecksum ();
        n = list.size ();
        for (int i=0; i<n; i++) {
            showChecksum ((Checksum) list.get (i));
        }

        _level--;
    }


    /******************************************************************
     * PRIVATE INSTANCE METHODS.
     ******************************************************************/

    private void showAgent (Agent agent, String label)
    {
        String margin = getIndent (++_level);

        _writer.println (margin + label + ": " + agent.getName ());
        _writer.println (margin + " Type: " + agent.getType ().toString ());
        String s = agent.getAddress ();
        if (s != null) {
            _writer.println (margin + " Address: " + s);
        }
        if ((s = agent.getTelephone ()) != null) {
            _writer.println (margin + " Telephone: " + s);
        }
        if ((s = agent.getFax ()) != null) {
            _writer.println (margin + " Fax: " + s);
        }
        if ((s = agent.getEmail ()) != null) {
            _writer.println (margin + " Email: " + s);
        }
        if ((s = agent.getWeb ()) != null) {
            _writer.println (margin + " Web: " + s);
        }
        _level--;
    }

    private void showChecksum (Checksum checksum)
    {
        String margin = getIndent (++_level);

        _writer.println (margin + "Checksum: " + checksum.getValue ());
        _writer.println (margin + " Type: " + checksum.getType ().toString ());

        _level--;
    }

    private void showDocument (Document document, String label)
    {
        String margin = getIndent (++_level);

        _writer.println (margin + label + ": " + document.getTitle ());
        _writer.println (margin + " Type: " + document.getType ());
        List list = document.getAuthor ();
        int n = list.size ();
        for (int i=0; i<n; i++) {
            showAgent ((Agent) list.get (i), "Author");
        }
        list = document.getPublisher ();
        n = list.size ();
        for (int i=0; i<n; i++) {
            showAgent ((Agent) list.get (i), "Publisher");
        }
        String s = document.getEdition ();
        if (s != null) {
            _writer.println (margin + " Edition: " + s);
        }
        if ((s = document.getDate ()) != null) {
            _writer.println (margin + " Date: " + s);
        }
        if ((s = document.getEnumeration ()) != null) {
            _writer.println (margin + " Enumeration: " + s);
        }
        if ((s = document.getPages ()) != null) {
            _writer.println (margin + " Pages: " + s);
        }
        list = document.getIdentifier ();
        n = list.size ();
        for (int i=0; i<n; i++) {
            showIdentifier ((Identifier) list.get (i));
        }
        if ((s = document.getNote ()) != null) {
            _writer.println (margin + " Note: " + s);
        }
        _level--;
    }

    /** Do the final output.  This should be in a suitable format
     *  for including multiple files between the header and the footer. */
    public void showFooter ()
    {
        _level--;

        _writer.flush ();
    }

    /** Do the initial output.  This should be in a suitable format
     *  for including multiple files between the header and the footer. */
    public void showHeader ()
    {
        String margin = getIndent (++_level);

        _writer.println (margin + _app.getName () + " (Rel. " +
                         _app.getRelease () + ", " +
			 HandlerBase.date.format (_app.getDate ()) + ")");
        _writer.println (margin + " Date: " +
                         HandlerBase.dateTime.format (new Date()));
    }

    private void showIdentifier (Identifier identifier)
    {
        String margin = getIndent (++_level);

        _writer.println (margin + "Identifier: " + identifier.getValue ());
        _writer.println (margin + " Type: " + identifier.getType().toString());
        String note = identifier.getNote ();
        if (note != null) {
            _writer.println (margin + " Note: " + note);
        }
        _level--;
    }

    private void showMessage (Message message)
    {
        String margin = getIndent (++_level);
        String prefix;
        if (message instanceof ErrorMessage) {
            prefix = "ErrorMessage: ";
        }
        else if (message instanceof InfoMessage) {
            prefix = "InfoMessage: ";
        }
        else {
            prefix = "Message: ";
        }

        String str = message.getMessage ();
        // Append submessage, if any, after a colon.
        String submsg = message.getSubMessage ();
        if (submsg != null) {
            str += ": " + submsg;
        }
        _writer.println (margin + prefix + str);
        long offset = message.getOffset ();
        if (offset > -1) {
            _writer.println (margin + " Offset: " + offset);
        }
        _level--;
    }

    private void showSignature (Signature signature)
    {
        String margin = getIndent (++_level);

        String sigValue;
        if (signature.isStringValue ()) {
            sigValue = signature.getValueString ();
        }
        else {
            sigValue = signature.getValueHexString ();
        }
        _writer.println (margin + signature.getType ().toString () + ": " +
                         sigValue);
        if (signature.getType ().equals (SignatureType.MAGIC)) {
            if (((InternalSignature) signature).hasFixedOffset ()) {
                _writer.println (margin + " Offset: " +
                                 ((InternalSignature) signature).getOffset ());
            }
        }
        String note = signature.getNote ();
        if (note != null) {
            _writer.println (margin + " Note: " + note);
        }
        String use = signature.getUse ().toString ();
        if (use != null) {
            _writer.println (margin + " Use: " + use);
        }
        _level--;
    }

    /* showProperty may be called recursively. */
    private void showProperty (Property property, String key, String margin)
    {
        PropertyArity arity = property.getArity ();

        if (key == null) {
            _writer.print (margin + "  ");
        }
        else {
            _writer.print (margin + " " + key + ": ");
        }
        if (arity.equals (PropertyArity.SCALAR)) {
            showScalarProperty (property, margin);
        }
        else if (arity.equals (PropertyArity.LIST)) {
            showListProperty (property, margin);
        }
        else if (arity.equals (PropertyArity.MAP)) {
            showMapProperty (property, margin);
        }
        else if (arity.equals (PropertyArity.SET)) {
            showSetProperty (property, margin);
        }
        else if (arity.equals (PropertyArity.ARRAY)) {
            showArrayProperty (property, margin);
        }
        else {
            _writer.println ();
        }
    }


    private void showScalarProperty (Property property, String margin)
    {
        PropertyType type = property.getType ();
        if (PropertyType.PROPERTY.equals (type)) {
            _writer.println ();
            Property prop = (Property) property.getValue ();
            showProperty (prop, prop.getName (), margin + " ");
            //_writer.println ();   // Does this improve things?
        }
        else if (PropertyType.NISOIMAGEMETADATA.equals (type)) {
            showNisoImageMetadata ((NisoImageMetadata) property.getValue (),
                                   margin + " ", _je.getShowRawFlag ());
        }
        else if (PropertyType.AESAUDIOMETADATA.equals (type)) {
            showAESAudioMetadata ((AESAudioMetadata) property.getValue (),
                                   margin + " ", _je.getShowRawFlag ());
        }
        else if (PropertyType.TEXTMDMETADATA.equals(type)) {
            showTextMDMetadata((TextMDMetadata) property.getValue(), 
                    margin + " ", _je.getShowRawFlag ());
        }
        else {
            _writer.println (property.getValue ().toString ());
        }
    }

    private void showListProperty (Property property, String margin)
    {
        PropertyType type = property.getType ();
        boolean valueIsProperty  = PropertyType.PROPERTY.equals (type);
        boolean valueIsNiso  = PropertyType.NISOIMAGEMETADATA.equals (type);
        boolean valueIsTextMD = PropertyType.TEXTMDMETADATA.equals(type);
        
        List list = (List) property.getValue ();

        int n = list.size ();
        int i;
        if (n > 0) {
            // Put a blank line after the name of the property list.
            if (valueIsProperty) {
                _writer.println ();
            }
            for (i = 0; i < n; i++) {
                if (valueIsProperty) {
                    Property pval = (Property) list.get (i);
                    showProperty (pval, pval.getName (), margin + " ");
                }
                else if (valueIsNiso) {
                                        showNisoImageMetadata ((NisoImageMetadata) list.get (i),
                                   margin + " ", _je.getShowRawFlag ());
                }
                else if (valueIsTextMD) {
                    showTextMDMetadata( (TextMDMetadata) list.get (i),
                                       margin + " ", _je.getShowRawFlag ());
                }
                else {
                    Object val = list.get (i);
                    if (i == 0) {
                        _writer.print (val);
                    }
                    else {
                        _writer.print (", " + val);
                    }
                }
            }
        }
        if (!valueIsProperty || n == 0) {
            _writer.println ();
        }
    }

    private void showMapProperty (Property property, String margin)
    {
        /* Map output looks like
           key : mapkey1 / mapval1, mapkey2 / mapval2, ... */
        PropertyType type = property.getType ();
        boolean valueIsProperty  = PropertyType.PROPERTY.equals (type);
        boolean valueIsNiso  = PropertyType.NISOIMAGEMETADATA.equals (type);
        boolean valueIsTextMD = PropertyType.TEXTMDMETADATA.equals(type);

        Map propmap = (Map) property.getValue ();
        Set keys = propmap.keySet();
        Iterator propiter = keys.iterator();
        while (propiter.hasNext ()) {
            Object propkey = propiter.next();
            Object val = propmap.get(propkey);
            if (valueIsProperty) {
                Property pval = (Property) val;
                showProperty (pval, pval.getName (), margin + " ");
                String propkeyStr = propkey.toString ();
                if (!(pval.getName ().equals(propkeyStr ))) {
                    _writer.println ("    Key: " + propkeyStr);
                }
            }
            else if (valueIsNiso) {
                showNisoImageMetadata ((NisoImageMetadata) val,
				       margin + " ", _je.getShowRawFlag ());
            }
            else if (valueIsTextMD) {
                showTextMDMetadata ((TextMDMetadata) val,
                       margin + " ", _je.getShowRawFlag ());
            }
            else {
                _writer.println ("   " + val.toString ());
                _writer.println ("     Key: " + propkey.toString ());
            }
        }
    }

    private void showSetProperty (Property property, 
                                   String margin) {
        PropertyType type = property.getType ();
        boolean valueIsProperty  = PropertyType.PROPERTY.equals (type);
        boolean valueIsNiso  = PropertyType.NISOIMAGEMETADATA.equals (type);
        boolean valueIsTextMD = PropertyType.TEXTMDMETADATA.equals(type);

        Set propset = (Set) property.getValue ();
        Iterator propiter = propset.iterator ();
        boolean first = true;
        while (propiter.hasNext ()) {
            Object val = propiter.next ();
            if (valueIsProperty) {
                Property pval = (Property) val;
                showProperty (pval, pval.getName (), margin + " ");
            }
            else if (valueIsNiso) {
                showNisoImageMetadata ((NisoImageMetadata) val,
                                   margin + " ", _je.getShowRawFlag ());
            }
            else if (valueIsTextMD) {
                showTextMDMetadata ((TextMDMetadata) val,
                                   margin + " ", _je.getShowRawFlag ());
            }
            else {
                if (first) {
                    _writer.print (val.toString ());
                    first = false; 
                }
                else {
                    _writer.print (", " + val.toString ());
                }
            }
        }
        _writer.println ();
    }

    private void showArrayProperty (Property property, String margin) {
        boolean[] boolArray = null;
        byte[] byteArray = null;
        char[] charArray = null;
        java.util.Date[] dateArray = null;
        double[] doubleArray = null;
        float[] floatArray = null;
        int[] intArray = null;
        long[] longArray = null;
        Object[] objArray = null;
        Property[] propArray = null;
        short[] shortArray = null;
        String[] stringArray = null;
        Rational[] rationalArray = null;
        NisoImageMetadata[] nisoArray = null;
        TextMDMetadata[] textMDArray = null;
        int n = 0;

        PropertyType propType = property.getType();
        if (PropertyType.BOOLEAN.equals (propType)) {
            boolArray = (boolean []) property.getValue ();
            n = boolArray.length;
        }
        else if (PropertyType.BYTE.equals (propType)) {
            byteArray = (byte []) property.getValue ();
            n = byteArray.length;
        }
        else if (PropertyType.CHARACTER.equals (propType)) {
            charArray = (char []) property.getValue ();
            n = charArray.length;
        }
        else if (PropertyType.DATE.equals (propType)) {
            dateArray = (java.util.Date []) property.getValue ();
            n = dateArray.length;
        }
        else if (PropertyType.DOUBLE.equals (propType)) {
            doubleArray = (double []) property.getValue ();
            n = doubleArray.length;
        }
        else if (PropertyType.FLOAT.equals (propType)) {
            floatArray = (float []) property.getValue ();
            n = floatArray.length;
        }
        else if (PropertyType.INTEGER.equals (propType)) {
            intArray = (int []) property.getValue ();
            n = intArray.length;
        }
        else if (PropertyType.LONG.equals (propType)) {
            longArray = (long []) property.getValue ();
            n = longArray.length;
        }
        else if (PropertyType.OBJECT.equals (propType)) {
                objArray = (Object []) property.getValue ();
                n = objArray.length;
            }
        else if (PropertyType.SHORT.equals (propType)) {
            shortArray = (short []) property.getValue ();
            n = shortArray.length;
        }
        else if (PropertyType.STRING.equals (propType)) {
            stringArray = (String []) property.getValue ();
            n = stringArray.length;
        }
        else if (PropertyType.RATIONAL.equals (propType)) {
            rationalArray = (Rational []) property.getValue ();
            n = rationalArray.length;
        }
        else if (PropertyType.PROPERTY.equals (propType)) {
            propArray = (Property []) property.getValue ();
            n = propArray.length;
        }
        else if (PropertyType.NISOIMAGEMETADATA.equals (propType)) {
            nisoArray = (NisoImageMetadata []) property.getValue ();
            n = nisoArray.length;
        }
        else if (PropertyType.TEXTMDMETADATA.equals(propType)) {
            textMDArray = (TextMDMetadata []) property.getValue ();
            n = textMDArray.length;
        }

        for (int i = 0; i < n; i++) {
            String elem;
            if (PropertyType.BOOLEAN.equals (propType)) {
                elem = String.valueOf (boolArray[i]);
            }
            else if (PropertyType.BYTE.equals (propType)) {
                elem = String.valueOf (byteArray[i]);
            }
            else if (PropertyType.CHARACTER.equals (propType)) {
                elem = String.valueOf (charArray[i]);
            }
            else if (PropertyType.DATE.equals (propType)) {
                elem = dateArray[i].toString();
            }
            else if (PropertyType.DOUBLE.equals (propType)) {
                elem = String.valueOf (doubleArray[i]);
            }
            else if (PropertyType.FLOAT.equals (propType)) {
                elem = String.valueOf (floatArray[i]);
            }
            else if (PropertyType.INTEGER.equals (propType)) {
                elem = String.valueOf (intArray[i]);
            }
            else if (PropertyType.LONG.equals (propType)) {
                elem = String.valueOf (longArray[i]);
            }
            else if (PropertyType.OBJECT.equals (propType)) {
                    elem = objArray[i].toString();
                }
            else if (PropertyType.SHORT.equals (propType)) {
                elem = String.valueOf (shortArray[i]);
            }
            else if (PropertyType.STRING.equals (propType)) {
                elem = stringArray[i];
            }
            else if (PropertyType.RATIONAL.equals (propType)) {
                elem = rationalArray[i].toString ();
            }
            else if (PropertyType.NISOIMAGEMETADATA.equals (propType)) {
                if (i == 0) {
                    _writer.println ();
                }
                NisoImageMetadata niso = nisoArray[i];
                showNisoImageMetadata (niso,
                                   margin + " ", _je.getShowRawFlag ());
                continue;
            }
            else if (PropertyType.TEXTMDMETADATA.equals (propType)) {
                if (i == 0) {
                    _writer.println ();
                }
                showTextMDMetadata (textMDArray[i],
                                   margin + " ", _je.getShowRawFlag ());
                continue;
            }
            else if (PropertyType.PROPERTY.equals (propType)) {
                if (i == 0) {
                    _writer.println ();
                }
                Property pval = propArray[i];
                showProperty (pval, pval.getName (), margin + " ");
                continue;
            }
            else elem = "<error>";
            if (i == 0) {
                _writer.print (elem);
            }
            else {
                _writer.print (", " + elem);
            }
        }
        if (propType != PropertyType.PROPERTY &&
                propType != PropertyType.NISOIMAGEMETADATA) {
            _writer.println ();     
        }
    }

    /* Output the textMD metadata, which is its own special
     * kind of property. */
    private void showTextMDMetadata (TextMDMetadata textMD, String margin,
                                        boolean rawOutput)
    {
        String margn2 = margin + " ";
        String margn3 = margn2 + " ";

        _writer.println ();
        _writer.println (margn2 + "Character_info:");
        String s = textMD.getCharset ();
        if (s != null) {
            _writer.println (margn3 + "Charset: " + s);
        }
        if ((s = textMD.getByte_orderString ()) != null) {
            _writer.println (margn3 + "Byte_order: " + s);
        }
        if ((s = textMD.getByte_size ()) != null) {
            _writer.println (margn3 + "Byte_size: " + s);
        }
        if ((s = textMD.getCharacter_size ()) != null) {
            _writer.println (margn3 + "Character_size: " + s);
        }
        if ((s = textMD.getLinebreakString ()) != null) {
            _writer.println (margn3 + "Linebreak: " + s);
        }

        if ((s = textMD.getLanguage ()) != null) {
            _writer.println (margn2 + "Language: " + s);
        }
        if ((s = textMD.getMarkup_basis ()) != null) {
            _writer.println (margn2 + "Markup_basis: " + s);
        }
        if ((s = textMD.getMarkup_basis_version ()) != null) {
            _writer.println (margn2 + "Markup_basis_version: " + s);
        }
        if ((s = textMD.getMarkup_language ()) != null) {
            _writer.println (margn2 + "Markup_language: " + s);
        }
        if ((s = textMD.getMarkup_language_version ()) != null) {
            _writer.println (margn2 + "Markup_language_version: " + s);
        }
    }

    /* Output the AES audio metadata, which is its own special
     * kind of property. */
    private void showAESAudioMetadata (AESAudioMetadata aes, String margin,
                                        boolean rawOutput)
    {
        String margn2 = margin + " ";
        String margn3 = margn2 + " ";
        String margn4 = margn3 + " ";
        String margn5 = margn4 + " ";

	_sampleRate = aes.getSampleRate ();

        _writer.println ();
        String s = aes.getAnalogDigitalFlag();
        if (s != null) {
            _writer.println (margn2 + "AnalogDigitalFlag: " + s);
        }
        s = aes.getSchemaVersion ();
        if (s != null) {
            _writer.println (margn2 + "SchemaVersion: " + s);
        }        
        s = aes.getFormat ();
        if (s != null) {
            _writer.println (margn2 + "Format: " + s);
        }        
        s = aes.getSpecificationVersion ();
        if (s != null) {
            _writer.println (margn2 + "SpecificationVersion: " + s);
        }        
        s = aes.getAppSpecificData();
        if (s != null) {
            _writer.println (margn2 + "AppSpecificData: " + s);
        }
        s = aes.getAudioDataEncoding ();
        if (s != null) {
            _writer.println (margn2 + "AudioDataEncoding: " + s);
        }
        int in = aes.getByteOrder ();
        if (in != AESAudioMetadata.NULL) {
            _writer.println (margn2 + "ByteOrder: " +
                     (in == AESAudioMetadata.BIG_ENDIAN ?
                      "BIG_ENDIAN" : "LITTLE_ENDIAN"));
        }
        long lin = aes.getFirstSampleOffset ();
        if (lin != AESAudioMetadata.NULL) {
            _writer.println (margn2 + "FirstSampleOffset: " +
                     Long.toString (lin));
        }
        String[] use = aes.getUse ();
        if (use != null) {
            _writer.println (margn2 + "Use:");
            _writer.println (margn3 + "UseType: " + use[0]);
            _writer.println (margn3 + "OtherType: " + use[1]);
        }
        s = aes.getPrimaryIdentifier();
        if (s != null) {
            String t= aes.getPrimaryIdentifierType ();
            _writer.println (margn2 + "PrimaryIdentifier: " + s);
            if (t != null) {
                _writer.println (margn3 + "IdentifierType: " + t);
            }
        }
        List facelist = aes.getFaceList ();
        if (!facelist.isEmpty ()) {
            // Add the face information, which is mostly filler.
            AESAudioMetadata.Face f = 
                    (AESAudioMetadata.Face) facelist.get(0);
            _writer.println (margn2 + "Face: ");
            _writer.println (margn3 + "TimeLine: ");
            AESAudioMetadata.TimeDesc startTime = f.getStartTime();
            if (startTime != null) {
                writeAESTimeRange (margn3, startTime, f.getDuration());
            }
            int nchan = aes.getNumChannels ();
            if (nchan != AESAudioMetadata.NULL) {
                _writer.println (margn4 + "NumChannels: " +
                            Integer.toString (nchan));
            }
            String[] locs = aes.getMapLocations ();
            for (int ch = 0; ch < nchan; ch++) {
                // write a stream description for each channel
                _writer.println (margn4 + "Stream:");
                _writer.println (margn5 + "ChannelNum: " + Integer.toString (ch));
                _writer.println (margn5 + "ChannelAssignment: " + locs[ch]);
            }
        }

        // In the general case, a FormatList can contain multiple
        // FormatRegions.  This doesn't happen with any of the current
        // modules; if it's needed in the future, simply set up an
        // iteration loop on formatList.
        List flist = aes.getFormatList ();
        if (!flist.isEmpty ()) {
            AESAudioMetadata.FormatRegion rgn = 
                (AESAudioMetadata.FormatRegion) flist.get(0);
            int bitDepth = rgn.getBitDepth ();
            double sampleRate = rgn.getSampleRate ();
            int wordSize = rgn.getWordSize ();
            String[] bitRed = rgn.getBitrateReduction ();
            // Build a FormatRegion subtree if at least one piece of data
            // that goes into it is present.
            if (bitDepth != AESAudioMetadata.NULL ||
                    sampleRate != AESAudioMetadata.NILL ||
                    wordSize != AESAudioMetadata.NULL) {
                _writer.println (margn2 + "FormatList:");
                _writer.println (margn3 + "FormatRegion:");
                if (bitDepth != AESAudioMetadata.NULL) {
                    _writer.println (margn4 + "BitDepth: " + Integer.toString (bitDepth));
                }
                if (sampleRate != AESAudioMetadata.NILL) {
                    _writer.println (margn4 + "SampleRate: " + Double.toString (sampleRate));
                }
                if (wordSize != AESAudioMetadata.NULL) {
                    _writer.println (margn4 + "WordSize: " + Integer.toString (wordSize));
                }
                if (bitRed != null) {
                    _writer.println (margn4 + "BitrateReduction");
                      _writer.println (margn5 +  
                            "CodecName: " + bitRed[0]);
                      _writer.println (margn5 + 
                            "codecNameVersion: " + bitRed[1]);
                      _writer.println (margn5 +
                            "codecCreatorApplication: " + bitRed[2]);
                      _writer.println (margn5 +
                            "codecCreatorApplicationVersion: " + bitRed[3]);
                      _writer.println (margn5 +
                            "codecQuality: " + bitRed[4]);
                      _writer.println (margn5 +
                            "dataRate: " + bitRed[5]);
                      _writer.println (margn5 +
                            "dataRateMode: " + bitRed[6]);
                }
            }
        }
    }

    /* start must be non-null, but duration may be null */
    private void writeAESTimeRange (String baseIndent,
        AESAudioMetadata.TimeDesc start,
        AESAudioMetadata.TimeDesc duration)
    {
        final String margn1 = baseIndent + " ";
        final String margn2 = margn1 + " ";
        final String margn3 = margn2 + " ";
        _writer.println (margn1 + "StartTime:");
        _writer.println (margn2 + "FrameCount: 30");
        _writer.println (margn2 + "TimeBase: 1000");
        _writer.println (margn2 + "VideoField: FIELD_1");
        _writer.println (margn2 + "CountingMode: NTSC_NON_DROP_FRAME");
        _writer.println (margn2 + "Hours: " + Integer.toString (start.getHours ()));
        _writer.println (margn2 + "Minutes: " + Integer.toString (start.getMinutes ()));
        _writer.println (margn2 + "Seconds: " + Integer.toString (start.getSeconds ()));
        _writer.println (margn2 + "Frames: " + Integer.toString (start.getFrames ()));
        _writer.println (margn2 + "Samples: ");
	double sr = start.getSampleRate ();
	if (sr == 1.0) {
	    sr = _sampleRate;
	}
	_writer.println (margn3 + "SampleRate: S" +
			 Integer.toString ((int) sr));
	_writer.println (margn3 + "NumberOfSamples: " + 
			 Integer.toString (start.getSamples ()));
        _writer.println (margn2 + "FilmFraming: NOT_APPLICABLE");
	_writer.println (margn3 + "Type: ntscFilmFramingType");
 
        if (duration != null) {
           _writer.println (margn1 + "Duration:");
           _writer.println (margn2 + "FrameCount: 30");
           _writer.println (margn2 + "TimeBase: 1000");
           _writer.println (margn2 + "VideoField: FIELD_1");
           _writer.println (margn2 + "CountingMode: NTSC_NON_DROP_FRAME");
           _writer.println (margn2 + "Hours: " +
			    Integer.toString (duration.getHours ()));
           _writer.println (margn2 + "Minutes: " +
			    Integer.toString (duration.getMinutes ()));
           _writer.println (margn2 + "Seconds: " +
			    Integer.toString (duration.getSeconds ()));
           _writer.println (margn2 + "Frames: " +
			    Integer.toString (duration.getFrames ()));
           _writer.println (margn2 + "Samples: ");
	   sr = duration.getSampleRate ();
	   if (sr == 1.0) {
	       sr = _sampleRate;
	   }
	   _writer.println (margn3 + "SampleRate: S" +
			    Integer.toString ((int) sr));
	   _writer.println (margn3 + "NumberOfSamples: " + 
			    Integer.toString (duration.getSamples ()));
           _writer.println (margn2 + "FilmFraming: NOT_APPLICABLE");
	   _writer.println (margn3 + "Type: ntscFilmFramingType");
        }
    }
    

    /**
     * Display the NISO image metadata formatted according to
     * the MIX schema.  The schema which is used may be 0.2 or 1.0,
     * depending on the module parameters.
     * @param niso NISO image metadata
     */
    protected void showNisoImageMetadata (NisoImageMetadata niso, String margin,
            boolean rawOutput)
    {
        if ("0.2".equals (_je.getMixVersion())) {
            showNisoImageMetadata02 (niso, margin, rawOutput);
        }
        else {
            showNisoImageMetadata10 (niso, margin, rawOutput);
        }
    }

    /* Output the Niso image metadata, which is its own special
     * kind of property. This provides a text approximation to MIX 0.2. */
    private void showNisoImageMetadata02 (NisoImageMetadata niso, String margin,
                                        boolean rawOutput)
    {
        String margn2 = margin + " ";

        _writer.println ();
        String s = niso.getMimeType ();
        if (s != null) {
            _writer.println (margn2 + "MIMEType: " + s);
        }
        if ((s = niso.getByteOrder ()) != null) {
            _writer.println (margn2 + "ByteOrder: " + s);
        }
        int n = niso.getCompressionScheme ();
        if (n != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "CompressionScheme: " +
             addIntegerValue (n, NisoImageMetadata.COMPRESSION_SCHEME,
                              NisoImageMetadata.COMPRESSION_SCHEME_INDEX,
                              rawOutput));
        }
        if ((n = niso.getCompressionLevel ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "CompressionLevel: " + n);
        }
        if ((n = niso.getColorSpace ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "ColorSpace: " +
                     addIntegerValue (n, NisoImageMetadata.COLORSPACE,
                                      NisoImageMetadata.COLORSPACE_INDEX,
                                      rawOutput));
        }
        if ((s = niso.getProfileName ()) != null) {
            _writer.println (margn2 + "ProfileName: " + s);
        }
        if ((s = niso.getProfileURL ()) != null) {
            _writer.println (margn2 + "ProfileURL: " + s);
        }
        int [] iarray = niso.getYCbCrSubSampling ();
        if (iarray != null) {
            _writer.print (margn2 + "YCbCrSubSampling: " + iarray[0]);
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + iarray[i]);
            }
            _writer.println ();
        }
        if ((n = niso.getYCbCrPositioning ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "YCbCrPositioning: " +
                     addIntegerValue (n, NisoImageMetadata.YCBCR_POSITIONING,
                                      rawOutput));
        }
        Rational [] rarray = niso.getYCbCrCoefficients ();
        if (rarray != null) {
            _writer.print (margn2 + "YCbCrCoefficients: " +
                           addRationalValue (rarray[0], rawOutput));
            for (int i=1; i<rarray.length; i++) {
                _writer.print (", " + addRationalValue (rarray[i], rawOutput));
            }
            _writer.println ();
        }
        rarray = niso.getReferenceBlackWhite ();
        if (rarray != null) {
            _writer.print (margn2 + "ReferenceBlackWhite: " +
                           addRationalValue (rarray[0], rawOutput));
            for (int i=1; i<rarray.length; i++) {
                _writer.print (", " + addRationalValue (rarray[i], rawOutput));
            }
            _writer.println ();
        }
        if ((n = niso.getSegmentType ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SegmentType: " +
                     addIntegerValue (n, NisoImageMetadata.SEGMENT_TYPE,
                                      rawOutput));
        }
        long [] larray = niso.getStripOffsets ();
        if (larray != null) {
            _writer.print (margn2 + "StripOffsets: " + larray[0]);
            for (int i=1; i<larray.length; i++) {
                _writer.print (", " + larray[i]);
            }
            _writer.println ();
        }
        long ln = niso.getRowsPerStrip ();
        if (ln != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "RowsPerStrip: " + ln);
        }
        if ((larray = niso.getStripByteCounts ()) != null) {
            _writer.print (margn2 + "StripByteCounts: " + larray[0]);
            for (int i=1; i<larray.length; i++) {
                _writer.print (", " + larray[i]);
            }
            _writer.println ();
        }
        if ((ln = niso.getTileWidth ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "TileWidth: " + ln);
        }
        if ((ln = niso.getTileLength ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "TileLength: " + ln);
        }
        if ((larray = niso.getTileOffsets ()) != null) {
            _writer.print (margn2 + "TileOffsets: " + larray[0]);
            for (int i=1; i<larray.length; i++) {
                _writer.print (", " + larray[i]);
            }
            _writer.println ();
        }
        if ((larray = niso.getTileByteCounts ()) != null) {
            _writer.print (margn2 + "TileByteCounts: " + larray[0]);
            for (int i=1; i<larray.length; i++) {
                _writer.print (", " + larray[i]);
            }
            _writer.println ();
        }
        if ((n = niso.getPlanarConfiguration ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "PlanarConfiguration: " + 
             addIntegerValue (n, NisoImageMetadata.PLANAR_CONFIGURATION,
                              rawOutput));
        }
        if ((s = niso.getImageIdentifier ()) != null) {
            _writer.println (margn2 + "ImageIdentifier: " + s);
        }
        if ((s = niso.getImageIdentifierLocation ()) != null) {
            _writer.println (margn2 + "ImageIdentifierLocation: " + s);
        }
        if ((ln = niso.getFileSize ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "FileSize: " + ln);
        }
        if ((n = niso.getChecksumMethod ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "ChecksumMethod: " + 
             addIntegerValue (n, NisoImageMetadata.CHECKSUM_METHOD,
                              rawOutput));
        }
        if ((s = niso.getChecksumValue ()) != null) {
            _writer.println (margn2 + "ChecksumValue: " + s);
        }
        if ((n = niso.getOrientation ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "Orientation: " + 
                             addIntegerValue (n, NisoImageMetadata.ORIENTATION,
                                              rawOutput));
        }
        if ((n = niso.getDisplayOrientation ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "DisplayOrientation: " + 
             addIntegerValue (n, NisoImageMetadata.DISPLAY_ORIENTATION,
                              rawOutput));
        }
        if ((ln = niso.getXTargetedDisplayAR ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "XTargetedDisplayAR: " + ln);
        }
        if ((ln = niso.getYTargetedDisplayAR ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "YTargetedDisplayAR: " + ln);
        }
        if ((s = niso.getPreferredPresentation ()) != null) {
            _writer.println (margn2 + "PreferredPresentation: " + s);
        }
        if ((s = niso.getSourceType ()) != null) {
            _writer.println (margn2 + "SourceType: " + s);
        }
        if ((s = niso.getImageProducer ()) != null) {
            _writer.println (margn2 + "ImageProducer: " + s);
        }
        if ((s = niso.getHostComputer ()) != null) {
            _writer.println (margn2 + "HostComputer: " + s);
        }
        if ((s = niso.getOS ()) != null) {
            _writer.println (margn2 + "OperatingSystem: " + s);
        }
        if ((s = niso.getOSVersion ()) != null) {
            _writer.println (margn2 + "OSVersion: " + s);
        }
        if ((s = niso.getDeviceSource ()) != null) {
            _writer.println (margn2 + "DeviceSource: " + s);
        }
        if ((s = niso.getScannerManufacturer ()) != null) {
            _writer.println (margn2 + "ScannerManufacturer: " + s);
        }
        if ((s = niso.getScannerModelName ()) != null) {
            _writer.println (margn2 + "ScannerModelName: " + s);
        }
        if ((s = niso.getScannerModelNumber ()) != null) {
            _writer.println (margn2 + "ScannerModelNumber: " + s);
        }
        if ((s = niso.getScannerModelSerialNo ()) != null) {
            _writer.println (margn2 + "ScannerModelSerialNo: " + s);
        }
        if ((s = niso.getScanningSoftware ()) != null) {
            _writer.println (margn2 + "ScanningSoftware: " + s);
        }
        if ((s = niso.getScanningSoftwareVersionNo ()) != null) {
            _writer.println (margn2 + "ScanningSoftwareVersionNo: " + s);
        }
        double d = niso.getPixelSize ();
        if (d != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "PixelSize: " + d);
        }
        if ((d = niso.getXPhysScanResolution ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "XPhysScanResolution: " + d);
        }
        if ((d = niso.getYPhysScanResolution ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "YPhysScanResolution: " + d);
        }

        if ((s = niso.getDigitalCameraManufacturer ()) != null) {
            _writer.println (margn2 + "DigitalCameraManufacturer: " + s);
        }
        if ((s = niso.getDigitalCameraModel ()) != null) {
            _writer.println (margn2 + "DigitalCameraModel: " + s);
        }
        if ((d = niso.getFNumber ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "FNumber: " + d);
        }
        if ((d = niso.getExposureTime ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "ExposureTime: " + d);
        }
        if ((d = niso.getBrightness ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "Brightness: " + d);
        }
        if ((d = niso.getExposureBias ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "ExposureBias: " + d);
        }
        
        double [] darray = niso.getSubjectDistance ();
        if (darray != null) {
            _writer.print (margn2 + "SubjectDistance: " + darray[0]);
            for (int i=1; i<darray.length; i++) {
                _writer.print (", " + darray[i]);
            }
            _writer.println ();
        }
        if ((n = niso.getMeteringMode ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "MeteringMode: " +
                     addIntegerValue (n, NisoImageMetadata.METERING_MODE,
                                              rawOutput));
        }
        if ((n = niso.getSceneIlluminant ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SceneIlluminant: " +
                     addIntegerValue (n, NisoImageMetadata.METERING_MODE,
                                              rawOutput));
        }
        if ((d = niso.getColorTemp ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "ColorTemp: " + d);
        }
        if ((d = niso.getFocalLength ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "FocalLength: " + d);
        }
        if ((n = niso.getFlash ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "Flash: " +
                             addIntegerValue (n, NisoImageMetadata.FLASH,
                                              rawOutput));
        }
        if ((d = niso.getFlashEnergy ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "FlashEnergy: " + d);
        }
        if ((n = niso.getFlashReturn ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "FlashReturn: " +
                     addIntegerValue (n, NisoImageMetadata.FLASH_RETURN,
                                              rawOutput));
        }
        if ((n = niso.getBackLight ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "BackLight: " +
                             addIntegerValue (n, NisoImageMetadata.BACKLIGHT,
                                              rawOutput));
        }
        if ((d = niso.getExposureIndex ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "ExposureIndex: " + d);
        }
        if ((n = niso.getAutoFocus ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "AutoFocus: " +
                             addIntegerValue (n, NisoImageMetadata.AUTOFOCUS,
                                              rawOutput));
        }
        if ((d = niso.getXPrintAspectRatio ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "XPrintAspectRatio: " + d);
        }
        if ((d = niso.getYPrintAspectRatio ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "YPrintAspectRatio: " + d);
        }

        if ((n = niso.getSensor ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "Sensor: " +
                             addIntegerValue (n, NisoImageMetadata.SENSOR,
                                              rawOutput));
        }
        if ((s = niso.getDateTimeCreated ()) != null) {
            _writer.println (margn2 + "DateTimeCreated: " + s);
        }
        if ((s = niso.getMethodology ()) != null) {
            _writer.println (margn2 + "Methodology: " + s);
        }
        if ((n = niso.getSamplingFrequencyPlane()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SamplingFrequencyPlane: " +
             addIntegerValue (n, NisoImageMetadata.SAMPLING_FREQUENCY_PLANE,
                              rawOutput));
        }
        if ((n = niso.getSamplingFrequencyUnit()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SamplingFrequencyUnit: " +
             addIntegerValue (n, NisoImageMetadata.SAMPLING_FREQUENCY_UNIT,
                              rawOutput));
        }
        Rational r = niso.getXSamplingFrequency ();
        if (r != null) {
            _writer.println (margn2 + "XSamplingFrequency: " +
                             addRationalValue (r, rawOutput));

        }
        r = niso.getYSamplingFrequency ();
        if (r != null) {
            _writer.println (margn2 + "YSamplingFrequency: " + 
                            addRationalValue (r, rawOutput));
        }
        if ((ln = niso.getImageWidth ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "ImageWidth: " + ln);
        }
        if ((ln = niso.getImageLength ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "ImageLength: " + ln);
        }
        if ((d = niso.getSourceXDimension ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "SourceXDimension: " + d);
        }
        if ((n = niso.getSourceXDimensionUnit ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SourceXDimensionUnit: " +
             addIntegerValue (n, NisoImageMetadata.SOURCE_DIMENSION_UNIT,
                              rawOutput));
        }
        if ((d = niso.getSourceYDimension ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "SourceYDimension: " + ln);
        }
        if ((n = niso.getSourceYDimensionUnit ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SourceYDimensionUnit: " +
             addIntegerValue (n, NisoImageMetadata.SOURCE_DIMENSION_UNIT,
                              rawOutput));
        }
        if ((iarray = niso.getBitsPerSample ()) != null) {
            _writer.print (margn2 + "BitsPerSample: " + iarray[0]);
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + iarray[i]);
            }
            _writer.println ();
        }
        if ((n = niso.getSamplesPerPixel ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SamplesPerPixel: " + n);
        }
        if ((iarray = niso.getExtraSamples ()) != null) {
            _writer.print (margn2 + "ExtraSamples: " +
                   addIntegerValue (iarray[0], NisoImageMetadata.EXTRA_SAMPLES,
                                    rawOutput));
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + addIntegerValue (iarray[i],
                                               NisoImageMetadata.EXTRA_SAMPLES,
                                                       rawOutput));
            }
            _writer.println ();
        }
        if ((s = niso.getColormapReference ()) != null) {
            _writer.println (margn2 + "ColormapReference: " + s);
        }
        if ((iarray = niso.getColormapBitCodeValue ()) != null) {
            _writer.print (margn2 + "ColormapBitCodeValue: " + iarray[0]);
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + iarray[i]);
            }
            _writer.println ();
        }
        if ((iarray = niso.getColormapRedValue ()) != null) {
            _writer.print (margn2 + "ColormapRedValue: " + iarray[0]);
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + iarray[i]);
            }
            _writer.println ();
        }
        if ((iarray = niso.getColormapGreenValue ()) != null) {
            _writer.print (margn2 + "ColormapGreenValue: " + iarray[0]);
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + iarray[i]);
            }
            _writer.println ();
        }
        if ((iarray = niso.getColormapBlueValue ()) != null) {
            _writer.print (margn2 + "ColormapBlueValue: " + iarray[0]);
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + iarray[i]);
            }
            _writer.println ();
        }
        if ((iarray = niso.getGrayResponseCurve ()) != null) {
            _writer.print (margn2 + "GrayResponseCurve: " + iarray[0]);
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + iarray[i]);
            }
            _writer.println ();
        }
        if ((n = niso.getGrayResponseUnit ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "GrayResponseUnit: " +
                     addIntegerValue (n, NisoImageMetadata.GRAY_RESPONSE_UNIT_02,
                                      rawOutput));
        }
        r = niso.getWhitePointXValue ();
        if (r != null) {
            _writer.println (margn2 + "WhitePointXValue: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getWhitePointYValue ()) != null) {
            _writer.println (margn2 + "WhitePointXValue: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesRedX ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesRedX: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesRedY ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesRedY: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesGreenX ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesGreenX: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesGreenY ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesGreenY: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesBlueX ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesBlueX: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesBlueY ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesBlueY: " +
                             addRationalValue (r, rawOutput));
        }
        if ((n = niso.getTargetType ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "TargetType: " +
             addIntegerValue (n, NisoImageMetadata.TARGET_TYPE, rawOutput)); 
        } 
        if ((s = niso.getTargetIDManufacturer ()) != null) {
            _writer.println (margn2 + "TargetIDManufacturer: " + s);
        }
        if ((s = niso.getTargetIDName ()) != null) {
            _writer.println (margn2 + "TargetIDName: " + s);
        }
        if ((s = niso.getTargetIDNo ()) != null) {
            _writer.println (margn2 + "TargetIDNo: " + s);
        }
        if ((s = niso.getTargetIDMedia ()) != null) {
            _writer.println (margn2 + "TargetIDMedia: " + s);
        }
        if ((s = niso.getImageData ()) != null) {
            _writer.println (margn2 + "ImageData: " + s);
        }
        if ((s = niso.getPerformanceData ()) != null) {
            _writer.println (margn2 + "PerformanceData: " + s);
        }
        if ((s = niso.getProfiles ()) != null) {
            _writer.println (margn2 + "Profiles: " + s);
        }
        if ((s = niso.getDateTimeProcessed ()) != null) {
            _writer.println (margn2 + "DateTimeProcessed: " + s);
        }
        if ((s = niso.getSourceData ()) != null) {
            _writer.println (margn2 + "SourceData: " + s);
        }
        if ((s = niso.getProcessingAgency ()) != null) {
            _writer.println (margn2 + "ProcessingAgency: " + s);
        }
        if ((s = niso.getProcessingSoftwareName ()) != null) {
            _writer.println (margn2 + "ProcessingSoftwareName: " + s);
        }
        if ((s = niso.getProcessingSoftwareVersion ()) != null) {
            _writer.println (margn2 + "ProcessingSoftwareVersion: " + s);
        }
        String [] sarray = niso.getProcessingActions ();
        if (sarray != null) {
            _writer.print (margn2 + "ProcessingActions: " + sarray[0]);
            for (int i=1; i<sarray.length; i++) {
                _writer.print (", " + sarray[i]);
            }
            _writer.println ();
        }

    }

    private void showNisoImageMetadata10 (NisoImageMetadata niso, String margin,
            boolean rawOutput)
    {
        String margn2 = margin + " ";
        String s;
        long ln;
        _writer.println ();
        if ((s = niso.getImageIdentifier ()) != null) {
            _writer.println (margn2 + "ImageIdentifier: " + s);
        }
        if ((ln = niso.getFileSize ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "FileSize: " + ln);
        }
        if ((s = niso.getByteOrder ()) != null) {
            // Convert strings to MIX 1.0 form
            if (s.startsWith ("big")) {
                s = "big_endian";
            }
            else if (s.startsWith ("little")) {
                s = "little_endian";
            }
            _writer.println (margn2 + "ByteOrder: " + s);
        }
        int n = niso.getCompressionScheme ();
        if (n != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "CompressionScheme: " +
             addIntegerValue (n, NisoImageMetadata.COMPRESSION_SCHEME,
                              NisoImageMetadata.COMPRESSION_SCHEME_INDEX,
                              rawOutput));
        }
        if ((n = niso.getCompressionLevel ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "CompressionLevel: " + n);
        }
        if ((n = niso.getChecksumMethod ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "ChecksumMethod: " + 
             addIntegerValue (n, NisoImageMetadata.CHECKSUM_METHOD,
                              rawOutput));
        }
        if ((s = niso.getChecksumValue ()) != null) {
            _writer.println (margn2 + "ChecksumValue: " + s);
        }
        if ((ln = niso.getImageWidth ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "ImageWidth: " + ln);
        }
        if ((ln = niso.getImageLength ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "ImageHeight: " + ln);
        }
        if ((n = niso.getColorSpace ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "ColorSpace: " +
                     addIntegerValue (n, NisoImageMetadata.COLORSPACE,
                                      NisoImageMetadata.COLORSPACE_INDEX,
                                      rawOutput));
        }
        if ((s = niso.getProfileName ()) != null) {
            _writer.println (margn2 + "iccProfileName: " + s);
        }
        if ((s = niso.getProfileURL ()) != null) {
            _writer.println (margn2 + "iccProfileURL: " + s);
        }
        int [] iarray = niso.getYCbCrSubSampling ();
        if (iarray != null) {
            _writer.print (margn2 + "YCbCrSubSampling: " + iarray[0]);
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + iarray[i]);
            }
            _writer.println ();
        }
        Rational [] rarray = niso.getYCbCrCoefficients ();
        if (rarray != null) {
            _writer.print (margn2 + "YCbCrCoefficients: " +
                           addRationalValue (rarray[0], rawOutput));
            for (int i=1; i<rarray.length; i++) {
                _writer.print (", " + addRationalValue (rarray[i], rawOutput));
            }
            _writer.println ();
        }
        rarray = niso.getReferenceBlackWhite ();
        if (rarray != null) {
            _writer.print (margn2 + "ReferenceBlackWhite: " +
                           addRationalValue (rarray[0], rawOutput));
            for (int i=1; i<rarray.length; i++) {
                _writer.print (", " + addRationalValue (rarray[i], rawOutput));
            }
            _writer.println ();
        }
        if ((s = niso.getSourceType ()) != null) {
            _writer.println (margn2 + "SourceType: " + s);
        }
        s = niso.getSourceID ();
        if (s != null) {
            _writer.println (margn2 + "SourceID" + s);
        }
        double d;
        if ((d = niso.getSourceXDimension ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "SourceXDimension: " + d);
        }
        if ((n = niso.getSourceXDimensionUnit ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SourceXDimensionUnit: " +
             addIntegerValue (n, NisoImageMetadata.SOURCE_DIMENSION_UNIT,
                              rawOutput));
        }
        if ((d = niso.getSourceYDimension ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "SourceYDimension: " + ln);
        }
        if ((n = niso.getSourceYDimensionUnit ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SourceYDimensionUnit: " +
             addIntegerValue (n, NisoImageMetadata.SOURCE_DIMENSION_UNIT,
                              rawOutput));
        }
        if ((s = niso.getDateTimeCreated ()) != null) {
            _writer.println (margn2 + "DateTimeCreated: " + s);
        }
        if ((s = niso.getImageProducer ()) != null) {
            _writer.println (margn2 + "ImageProducer: " + s);
        }
        if ((s = niso.getDeviceSource ()) != null) {
            _writer.println (margn2 + "CaptureDevice: " + s);
        }
        if ((s = niso.getScannerManufacturer ()) != null) {
            _writer.println (margn2 + "ScannerManufacturer: " + s);
        }
        if ((s = niso.getScannerModelName ()) != null) {
            _writer.println (margn2 + "ScannerModelName: " + s);
        }
        if ((s = niso.getScannerModelNumber ()) != null) {
            _writer.println (margn2 + "ScannerModelNumber: " + s);
        }
        if ((s = niso.getScannerModelSerialNo ()) != null) {
            _writer.println (margn2 + "ScannerModelSerialNo: " + s);
        }
        double xres = niso.getXPhysScanResolution();
        double yres = niso.getYPhysScanResolution();
        if (xres != NisoImageMetadata.NULL && yres != NisoImageMetadata.NULL) {
            double res = (xres > yres ? xres : yres);
            _writer.println (margn2 +  
                     "MaximumOpticalResolution: " + Double.toString (res));
        }
        if ((s = niso.getScanningSoftware ()) != null) {
            _writer.println (margn2 + "ScanningSoftware: " + s);
        }
        if ((s = niso.getScanningSoftwareVersionNo ()) != null) {
            _writer.println (margn2 + "ScanningSoftwareVersionNo: " + s);
        }
        if ((s = niso.getDigitalCameraManufacturer ()) != null) {
            _writer.println (margn2 + "DigitalCameraManufacturer: " + s);
        }
        if ((s = niso.getDigitalCameraModel ()) != null) {
            _writer.println (margn2 + "DigitalCameraModel: " + s);
        }
        if ((d = niso.getFNumber ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "FNumber: " + d);
        }
        if ((d = niso.getExposureTime ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "ExposureTime: " + d);
        }
        if ((d = niso.getBrightness ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "BrightnessValue: " + d);
        }
        if ((d = niso.getExposureBias ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "ExposureBiasValue: " + d);
        }
        double [] darray = niso.getSubjectDistance ();
        if (darray != null) {
            _writer.print (margn2 + "SubjectDistance: " + darray[0]);
            for (int i=1; i<darray.length; i++) {
                _writer.print (", " + darray[i]);
            }
            _writer.println ();
        }
        if ((n = niso.getMeteringMode ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "MeteringMode: " +
                     addIntegerValue (n, NisoImageMetadata.METERING_MODE,
                                              rawOutput));
        }
        if ((n = niso.getFlash ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "Flash: " +
                             addIntegerValue (n, NisoImageMetadata.FLASH,
                                              rawOutput));
        }
        if ((d = niso.getFocalLength ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "FocalLength: " + d);
        }
        if ((d = niso.getFlashEnergy ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "FlashEnergy: " + d);
        }
        if ((n = niso.getBackLight ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "BackLight: " +
                             addIntegerValue (n, NisoImageMetadata.BACKLIGHT,
                                              rawOutput));
        }
        if ((d = niso.getExposureIndex ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "ExposureIndex: " + d);
        }
        if ((n = niso.getAutoFocus ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "AutoFocus: " +
                             addIntegerValue (n, NisoImageMetadata.AUTOFOCUS,
                                              rawOutput));
        }
        if ((d = niso.getXPrintAspectRatio ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "XPrintAspectRatio: " + d);
        }
        if ((d = niso.getYPrintAspectRatio ()) != NisoImageMetadata.NILL) {
            _writer.println (margn2 + "YPrintAspectRatio: " + d);
        }
        if ((n = niso.getOrientation ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "Orientation: " + 
                             addIntegerValue (n, NisoImageMetadata.ORIENTATION,
                                              rawOutput));
        }
        if ((s = niso.getMethodology ()) != null) {
            _writer.println (margn2 + "Methodology: " + s);
        }
        if ((n = niso.getSamplingFrequencyPlane()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SamplingFrequencyPlane: " +
             addIntegerValue (n, NisoImageMetadata.SAMPLING_FREQUENCY_PLANE,
                              rawOutput));
        }
        if ((n = niso.getSamplingFrequencyUnit()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SamplingFrequencyUnit: " +
             addIntegerValue (n, NisoImageMetadata.SAMPLING_FREQUENCY_UNIT,
                              rawOutput));
        }
        Rational r = niso.getXSamplingFrequency ();
        if (r != null) {
            _writer.println (margn2 + "XSamplingFrequency: " +
                             addRationalValue (r, rawOutput));

        }
        r = niso.getYSamplingFrequency ();
        if (r != null) {
            _writer.println (margn2 + "YSamplingFrequency: " + 
                            addRationalValue (r, rawOutput));
        }
        if ((iarray = niso.getBitsPerSample ()) != null) {
            _writer.print (margn2 + "BitsPerSample: " + iarray[0]);
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + iarray[i]);
            }
            _writer.println ();
            _writer.println (margn2 + "BitsPerSampleUnit: integer");
        }
        if ((n = niso.getSamplesPerPixel ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "SamplesPerPixel: " + n);
        }
        if ((iarray = niso.getExtraSamples ()) != null) {
            _writer.print (margn2 + "ExtraSamples: " +
                   addIntegerValue (iarray[0], NisoImageMetadata.EXTRA_SAMPLES,
                                    rawOutput));
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + addIntegerValue (iarray[i],
                                               NisoImageMetadata.EXTRA_SAMPLES,
                                                       rawOutput));
            }
            _writer.println ();
        }
        if ((s = niso.getColormapReference ()) != null) {
            _writer.println (margn2 + "ColormapReference: " + s);
        }
        // The MIX 1.0 schema requires the letter "N" as the value of the
        // gray response curve, which is clearly a bug. We deviate from
        // the bug here.
        if ((iarray = niso.getGrayResponseCurve ()) != null) {
            _writer.print (margn2 + "GrayResponseCurve: " + iarray[0]);
            for (int i=1; i<iarray.length; i++) {
                _writer.print (", " + iarray[i]);
            }
            _writer.println ();
        }
        if ((n = niso.getGrayResponseUnit ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "GrayResponseUnit: " +
                     addIntegerValue (n, NisoImageMetadata.GRAY_RESPONSE_UNIT_02,
                                      rawOutput));
        }
        r = niso.getWhitePointXValue ();
        if (r != null) {
            _writer.println (margn2 + "WhitePointXValue: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getWhitePointYValue ()) != null) {
            _writer.println (margn2 + "WhitePointXValue: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesRedX ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesRedX: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesRedY ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesRedY: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesGreenX ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesGreenX: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesGreenY ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesGreenY: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesBlueX ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesBlueX: " +
                             addRationalValue (r, rawOutput));
        }
        if ((r = niso.getPrimaryChromaticitiesBlueY ()) != null) {
            _writer.println (margn2 + "PrimaryChromaticitiesBlueY: " +
                             addRationalValue (r, rawOutput));
        }
        if ((n = niso.getTargetType ()) != NisoImageMetadata.NULL) {
            _writer.println (margn2 + "TargetType: " +
             addIntegerValue (n, NisoImageMetadata.TARGET_TYPE, rawOutput)); 
        } 
        if ((s = niso.getTargetIDManufacturer ()) != null) {
            _writer.println (margn2 + "TargetIDManufacturer: " + s);
        }
        if ((s = niso.getTargetIDName ()) != null) {
            _writer.println (margn2 + "TargetIDName: " + s);
        }
        if ((s = niso.getTargetIDNo ()) != null) {
            _writer.println (margn2 + "TargetIDNo: " + s);
        }
        if ((s = niso.getTargetIDMedia ()) != null) {
            _writer.println (margn2 + "TargetIDMedia: " + s);
        }
        if ((s = niso.getImageData ()) != null) {
            _writer.println (margn2 + "ExternalTarget: " + s);
        }
        if ((s = niso.getPerformanceData ()) != null) {
            _writer.println (margn2 + "PerformanceData: " + s);
        }
        if ((s = niso.getSourceData ()) != null) {
            _writer.println (margn2 + "SourceData: " + s);
        }
        if ((s = niso.getProcessingAgency ()) != null) {
            _writer.println (margn2 + "ProcessingAgency: " + s);
        }
        if ((s = niso.getProcessingSoftwareName ()) != null) {
            _writer.println (margn2 + "ProcessingSoftwareName: " + s);
        }
        if ((s = niso.getProcessingSoftwareVersion ()) != null) {
            _writer.println (margn2 + "ProcessingSoftwareVersion: " + s);
        }
        if ((s = niso.getOS ()) != null) {
            _writer.println (margn2 + "OperatingSystem: " + s);
        }
        if ((s = niso.getOSVersion ()) != null) {
            _writer.println (margn2 + "OSVersion: " + s);
        }
        String [] sarray = niso.getProcessingActions ();
        if (sarray != null) {
            _writer.print (margn2 + "ProcessingActions: " + sarray[0]);
            for (int i=1; i<sarray.length; i++) {
                _writer.print (", " + sarray[i]);
            }
            _writer.println ();
        }


    }
    
    
    private String addIntegerValue (int value, String [] labels,
                                    boolean rawOutput)
    {
        String s = null;
        if (!rawOutput && 0 <= value && value < labels.length) {
            s = labels[value];
        }
        else {
            s = Integer.toString (value);
        }

        return s;
    }

    private String addIntegerValue (int value, String [] labels,
                                    int [] index, boolean rawOutput)
    {
        String s = null;
        boolean outOfRange = false;
        if (!rawOutput) {
            int n = -1;
            for (int i=0; i<index.length; i++) {
                if (value == index[i]) {
                    n = i;
                    break;
                }
            }
            if (n > -1) {
                s = labels[n];
            }
            else {
                outOfRange = true;
            }
        }
        if (rawOutput || outOfRange) {
            s = Integer.toString (value);
        }

        return s;
    }

    private String addRationalValue (Rational r, boolean rawOutput)
    {
        String s = null;
        if (!rawOutput) {
            s = _format.format (r.toDouble ());
        }
        else {
            s = r.toString ();
        }

        return s;
    }
}
