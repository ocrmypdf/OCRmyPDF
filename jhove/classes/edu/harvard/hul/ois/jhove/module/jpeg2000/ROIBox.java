/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 *  ROI Description box (JPX).
 *  See ISO/IEC FCD15444-2: 2000, L.9.16 
 *
 * @author Gary McGath
 *
 */
public class ROIBox extends JP2Box {

    private Property roiProp;

    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public ROIBox (RandomAccessFile raf, BoxHolder parent)
    {
        super (raf, parent);
    }

    /** Reads the box, putting appropriate information in
     *  the RepInfo object.  setModule, setBoxHeader,
     *  setRepInfo and setDataInputStream must be called
     *  before <code>readBox</code> is called. 
     *  <code>readBox</code> must completely consume the
     *  box, so that the next byte to be read by the
     *  DataInputStream is the <code>FF</code> byte of the next Box.
     */
    public boolean readBox() throws IOException {
        final String baddata = "Invalid data in ROI";
        initBytesRead ();
        int nroi = ModuleBase.readUnsignedByte (_dstrm, _module);
        
        List propList = new ArrayList (nroi);
        JhoveBase je = _module.getBase ();
        boolean raw = je.getShowRawFlag ();
        for (int i = 0; i < nroi; i++) {
            List roiPropList = new ArrayList (7);
            int incs = ModuleBase.readUnsignedByte (_dstrm, _module);
            if (incs > 1) {
                _repInfo.setMessage (new ErrorMessage 
                        (baddata, _module.getFilePos ()));
                _repInfo.setValid (false);
            }
            roiPropList.add (_module.addIntegerProperty("InCodestream",
                        incs, JP2Strings.inCodestreamStr));
            
            int rtyp = ModuleBase.readUnsignedByte (_dstrm, _module);
            if (rtyp > 1) {
                _repInfo.setMessage (new ErrorMessage 
                        ("Invalid region type in ROI Box", _module.getFilePos ()));
                _repInfo.setValid (false);
            }
            roiPropList.add (_module.addIntegerProperty("RegionType",
                        rtyp, JP2Strings.roiTypeStr));

            int rcp = ModuleBase.readUnsignedByte (_dstrm, _module);
            roiPropList.add (new Property ("CodingPriority",
                        PropertyType.INTEGER,
                        new Integer (rcp)));
            
            long lcx = _module.readUnsignedInt (_dstrm);
            roiPropList.add (new Property ("HorizontalLocation",
                        PropertyType.LONG,
                        new Long (lcx)));
            long lcy = _module.readUnsignedInt (_dstrm);
            roiPropList.add (new Property ("HorizontalLocation",
                        PropertyType.LONG,
                        new Long (lcy)));
            long wdt = _module.readUnsignedInt (_dstrm);
            roiPropList.add (new Property ("Width",
                        PropertyType.LONG,
                        new Long (wdt)));
            long hth = _module.readUnsignedInt (_dstrm);
            roiPropList.add (new Property ("Height",
                        PropertyType.LONG,
                        new Long (hth)));

            propList.add (new Property ("ROI",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    roiPropList));
        }
        roiProp = new Property ("ROIs",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    propList);
        // If the parent box is an Association box, the property
        // will be put into the Association property, so there's no
        // need to put it in two places.
        if (!(_parentBox instanceof AssociationBox)) {
            if (_parentBox instanceof CodestreamHeaderBox) {
                Codestream cs = ((CodestreamHeaderBox) _parentBox).getCodestream ();
                cs.setROIProperty (roiProp);
            }
            else {
                _module.addProperty (roiProp);
            }
        }
        finalizeBytesRead ();
        return true;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "ROI Description Box";
    }
    
    /** Returns a Property which describes the box.  This is
     *  used as a subproperty of the Property returned by
     *  selfDescProperty. 
     */
    protected Property getSelfPropDesc (){
        Property descProp;
        if (roiProp != null) {
            return new Property (DESCRIPTION_NAME,
                PropertyType.PROPERTY,
                roiProp);
        }
        else {
            return null;
        }
    }

}
