/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import java.io.*;
import java.util.*;
import edu.harvard.hul.ois.jhove.*;

/**
 * Compositing Layer Header Box (JPX superbox).
 * See ISO/IEC FCD15444-2: 2000, L.9.4
 * 
 * @author Gary McGath
 *
 */
public class ComposLayerHdrBox extends JP2Box {

    private Property label;
    private Property opacityProp;
    private Property channelDefProp;
    private Property codestreamRegProp;
    private List<Property> colorSpecs;
    


    /**
     *  Constructor with superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public ComposLayerHdrBox(RandomAccessFile raf, BoxHolder parent) {
        super(raf, parent);
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
        if (_parentBox != null) {
            // Box must be at top level.
            wrongBoxContext();
            return false;
        }
        initBytesRead ();
        hasBoxes = true;
        colorSpecs = new LinkedList<Property> ();
        
        // Unlike some other boxes, compositing layer boxes
        // are numbered by their order in the file, starting
        // with 0.  A definite case of design by committee.
        int sizeLeft = (int) _boxHeader.getDataLength() ;
        //BoxHeader subhdr = new BoxHeader (_module, _dstrm);
        int state = 0;        // state variable for checking progress of boxes
        JP2Box box = null;
        boolean hasOpacity = false;
        boolean hasChannelDef = false;
        while (hasNext ()) {
            box = (JP2Box) next ();
            if (box == null) {
                break;
            }
            if (box instanceof ColorGroupBox ||
                box instanceof OpacityBox ||
                box instanceof ChannelDefBox ||
                box instanceof CodestreamRegBox ||
                box instanceof IPRBox ||
                box instanceof ResolutionBox ||
                box instanceof LabelBox) {
                    if (!box.readBox ()) {
                        return false;
                    }
                    if (box instanceof OpacityBox) {
                        hasOpacity = true;
                    }
                    else if (box instanceof ChannelDefBox) {
                        hasChannelDef = true;
                    }
                    if (box instanceof LabelBox) {
                        label = new Property ("Label",
                                PropertyType.STRING,
                                ((LabelBox) box).getLabel ());
                    }
            }
            else {
                box.skipBox ();
            }
        }
        if (hasOpacity && hasChannelDef) {
            _repInfo.setMessage (new ErrorMessage
                    ("Compositing Layer Header may not have both " +
                     "Opacity and Channel Definition Boxes",
                     _module.getFilePos ()));
            _repInfo.setValid (false);
        }
        finalizeBytesRead ();
        
        List<Property> propList = new ArrayList (4);
        if (label != null) {
            propList.add (label);
        }
        if (!colorSpecs.isEmpty ()) {
            propList.add (new Property ("ColorSpecs",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    colorSpecs));
        }
        if (opacityProp != null) {
            propList.add (opacityProp);
        }
        if (channelDefProp != null) {
            propList.add (channelDefProp);
        }
        if (codestreamRegProp != null) {
            propList.add (codestreamRegProp);
        }
        _module.addComposLayer(new Property 
                ("CompositeLayerHeader",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    propList));
        return true;
    }


    /** Add a color specification property. */
    protected void addColorSpec (Property p)
    {
        colorSpecs.add (p);
    }
    
    /** Add an opacity property. */
    protected void addOpacity (Property p)
    {
        opacityProp = p;
    }
    
    /** Add channel definition property. */
    protected void addChannelDef (Property p)
    {
        channelDefProp = p;
    }
    
    /** Add codestream registration property. */
    protected void addCodestreamReg (Property p)
    {
        codestreamRegProp = p;
    }

    /** Returns the name of the Box.  */
    protected String getSelfPropName ()
    {
        return "Compositing Layer Header Box";
    }
}
