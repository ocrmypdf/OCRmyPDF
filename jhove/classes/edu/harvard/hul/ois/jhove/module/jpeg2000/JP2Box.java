/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.module.Jpeg2000Module;
import edu.harvard.hul.ois.jhove.*;
import java.io.*;
import java.util.*;

/**
 * Superclass for JPEG 2000 boxes.
 *
 * @author Gary McGath
 *
 */
public abstract class JP2Box extends BoxHolder {

    protected long startBytesRead;
    protected long _bytesRead;
    protected List<Property> associations;
    
    protected final static String noJP2Hdr = 
        "Other boxes may not occur before JP2 Header";

    /* Name to be used for self-description property. */
    protected final static String DESCRIPTION_NAME =
        "Description";
    
    /**
     *  Constructor.  Has no arguments, so that
     *  invoking lots of different subclasses is
     *  relatively simple.  setModule, setBoxHeader,
     *  setRepInfo, and setDataInputStream should
     *  be called immediately after the constructor.
     */
    public JP2Box (RandomAccessFile raf)
    {
        super (raf);
        init (null);
    }
    
    /**
     *  Constructor for a box which is found within a
     *  superbox.
     * 
     *  @param   parent   parent superbox of this box
     */
    public JP2Box (RandomAccessFile raf, BoxHolder parent)
    {
        super (raf);
        init (parent);
    }
    
    protected void init (BoxHolder parent)
    {
        //_boxHeader = hdr;
        if (parent instanceof JP2Box) {
            _parentBox = (JP2Box) parent;
        }
        else {
            _parentBox = null;
        }
        _bytesRead = 0;
        associations = new LinkedList<Property> ();
    }


    /* This is the key to the reorganization of the code.
     * A normal box generates an RAFInputStream based
     * on the underlying RandomAccessFile.  What do the
     * weird subclasses do, and how do I handle box
     * substitution?  Rather than calling boxMaker statically,
     * should I add a method BoxHeader.getBox?  That doesn't
     * quite cover the case where one header (for a 
     * Binary Filter Box) turns into multiple boxes.  Could
     * have an iterator in the BoxHeader class that is capable
     * of returning no boxes (in the case of a Free box) or
     * multiple boxes, but usually returns one box.
     * 
     * But a subbox iterator, which returns all the top-level
     * boxes (at the top level) or all the subboxes of a given
     * box, is more natural.  For this we need to add a BoxHolder
     * class, of which JP2Box is a subclass.  BoxHolder will
     * have a method to generate an iterator; this method gets
     * a box (which it may keep in its pocket), and knows about
     * Binary Filter boxes and Cross Reference boxes.
     */

    /** Sets the module under which the Box is being read. */
    public void setModule (Jpeg2000Module module)
    {
        _module = module;
    }
    
    /** Sets the BoxHeader from which this Box was obtained. */
    public void setBoxHeader (BoxHeader hdr)
    {
        _boxHeader = hdr;
        bytesLeft = _boxHeader.getDataLength ();
    }
    
    /** Assigns a RepInfo object, so that subclasses of 
     *  JP2Box can add Properties and Messages. */
    public void setRepInfo (RepInfo info)
    {
        _repInfo = info;
    }
    
    /** Assigns the DataInputStream from which the box is
     *  being read.  */
    public void setDataInputStream (DataInputStream dstrm)
    {
        _dstrm = dstrm;
    }


    /** Assigns the RandomAccessFile from which the box is
     *  being read.  */
    public void setRandomAccessFile (RandomAccessFile raf)
    {
        _raf = raf;
    }

    
    /** Static factory method for generating an object of the
     *  appropriate subclass of MarkerSegment, based on the
     *  box type.
     *  This is for use in top-level reading of boxes, not
     *  subboxes.  Provision is made for calling this with a
     *  parent box, but the set of boxes dispatched on
     *  is the set used at top level.
     * 
     *  Certain box types have magical characteristics and have
     *  to be checked by the BoxHolder.  These include 
     *  BinaryFilterBox and CrossReferenceBox.
     * 
     *  @param hType    4-character string indicating the box type
     *  @param parent   parent BoxHolder
     */
    public static JP2Box boxMaker (String hType, BoxHolder parent)
    {
        JP2Box box = null;
        RandomAccessFile raf = null;
        if (parent != null) {
            raf = parent._raf;
        }
        if ("jp2h".equals (hType)) {
            // The JP2 header superbox
            box = new JP2HeaderBox (raf, parent);
        }
        else if ("asoc".equals (hType)) {
            // Association box (JPX)
            box = new AssociationBox (raf, parent);
        }
        else if ("bpcc".equals (hType)) {
            box = new BPCCBox (raf, parent);
        }
        else if ("chck".equals (hType)) {
            box = new DigSignatureBox (raf, parent);
        }
        else if ("cdef".equals (hType)) {
            box = new ChannelDefBox (raf, parent);
        }
        else if ("cgrp".equals (hType)) {
                box = new ColorGroupBox(raf, parent);
            }
        else if ("cmap".equals (hType)) {
            box = new ComponentMapBox (raf, parent);
        }
        else if ("colr".equals (hType)) {
            box = new ColorSpecBox (raf, parent);
        }
        else if ("comp".equals (hType)) {
            // Composition box (JPX)
            box = new CompositionBox (raf, parent);
        }
        else if ("copt".equals (hType)) {
            // Composition options box (JPX)
            box = new CompOptionsBox (raf, parent);
        }
        else if ("creg".equals (hType)) {
            // codestream registration box (JPX)
            box = new CodestreamRegBox (raf, parent);
        }
        else if ("drep".equals (hType)) {
            box = new DesiredReproBox (raf, parent);
        }
        else if ("flst".equals (hType)) {
            box = new FragmentListBox (raf, parent);
        }
        else if ("ftbl".equals (hType)) {
            // Fragment Table box (JPX)
            box = new FragmentTableBox (raf, parent);
        }
        else if ("gtso".equals (hType)) {
            // Graphics Technology Standard Output Box (JPX)
            box = new GTSOBox (raf, parent);
        }
        else if ("inst".equals (hType)) {
            // Instruction Set box (JPX)
            box = new InstructionSetBox (raf, parent);
        }
        else if ("ihdr".equals (hType)) {
            box = new ImageHeaderBox (raf, parent);
        }
        else if ("jp2c".equals (hType)) {
            // The Continuous Codestream box.
            box = new ContCodestreamBox (raf, parent);
        }
        else if ("jpch".equals (hType)) {
            // The Compositing Header box
            box = new CodestreamHeaderBox (raf, parent);
        }
        else if ("jplh".equals (hType)) {
            // The Compositing Layer Header box
            box = new ComposLayerHdrBox (raf, parent);
        }
        else if ("jp2i".equals (hType)) {
            // The Intellectual Property Rights box
            box = new IPRBox (raf, parent);
        }
        else if ("lbl ".equals (hType)) {
            box = new LabelBox (raf, parent);
        }
        else if ("nlst".equals (hType)) {
            // Number list box (JPX)
            box = new NumberListBox (raf, parent);
        }
        else if ("opct".equals (hType)) {
            box = new OpacityBox (raf, parent);
        }
        else if ("pclr".equals (hType)) {
            box = new PaletteBox (raf, parent);
        }
        else if ("res ".equals (hType)) {
            box = new ResolutionBox (raf, parent);
        }
        else if ("roid".equals (hType)) {
            box = new ROIBox (raf, parent);
        }
        else if ("resc".equals (hType)) {
            // Capture Resolution Box (JPX)
            box = new CaptureResolutionBox (raf, parent);
        }
        else if ("resd".equals (hType)) {
            // Default Display Resolution Box (JPX)
            box = new DDResolutionBox (raf, parent);
        }
        else if ("rreq".equals (hType)) {
            // Reader Requirements box (JPX)
            box = new ReaderRequirementsBox (raf, parent);
        }
        else if ("uinf".equals (hType)) {
            box = new UUIDInfoBox (raf, parent);
        }
        else if ("ulst".equals (hType)) {
            box = new UUIDListBox (raf, parent);
        }
        else if ("url ".equals (hType)) {
            box = new DataEntryURLBox (raf, parent);
        }
        else if ("uuid".equals (hType)) {
            box = new UUIDBox (raf, parent);
        }
        else if ("xml ".equals (hType)) {
            box = new XMLBox (raf, parent);
        }
        else {
            // Not recognized; skip over it.
            // The "free" box, which simply indicates
            // unused space, goes through here.
            // So does the Media Data ("mdat") box,
            // whose content is defined only by references
            // into it from a Fragment Table.
            box = new DefaultBox (raf);
        }
        return box;
    }

    /* Bracketing code for calculating bytes read. 
     * Every subclass's readBox() method should start
     * by calling initBytesRead and finish by calling
     * finalizeBytesRead.
     */
    protected void initBytesRead ()
    {
        startBytesRead = _module.getFilePos ();   
    }
    
    protected void finalizeBytesRead ()
    {
        _bytesRead = _module.getFilePos () - startBytesRead;        
    }

    /** Reads the box, putting appropriate information in
     *  the RepInfo object.  setModule, setBoxHeader,
     *  setRepInfo and setDataInputStream must be called
     *  before <code>readBox</code> is called. 
     *  Thus, the header of the box must already have been read.
     *  <code>readBox</code> must completely consume the
     *  box, so that the next byte to be read by the
     *  DataInputStream is the <code>FF</code> byte of the next Box.
     *  The number of bytes read must be placed in _bytesRead.
     */
    public abstract boolean readBox () throws IOException;
    
    public int getBytesRead () 
    {
        return (int) _bytesRead;
    }


    /** Skips over the box.  Can be called when the box is
     *  legal but meaningless in the current context.
     */
    public void skipBox() throws IOException {
        initBytesRead ();
        if (_boxHeader.getLength () != 0) {
            _module.skipBytes (_dstrm, (int) 
                    _boxHeader.getDataLength (), 
                    _module);    
        }
        finalizeBytesRead ();
    }

    /* Adds an Association property.  Most superboxes can
     * contain Association boxes; these report themselves
     * as Association properties. 
     */
    protected void addAssociation (Property p)
    {
        associations.add (p);
    }
    
    
    /** Utility error reporting function for incorrect box length. 
     *  Sets the RepInfo's wellFormed flag to <code>false</code>.
     */
    protected void wrongBoxSize () 
    {
        _repInfo.setMessage (new ErrorMessage
            ("Incorrect Box size for " + getSelfPropName (),
             _module.getFilePos ()));
        _repInfo.setWellFormed (false);
    }
    
    /** Utility error reporting function for box in a context
     *  (superbox or lack thereof) which is not permitted.
     *  Sets the RepInfo's wellFormed flag to <code>false</code>.
     */
    protected void wrongBoxContext ()
    {
        _repInfo.setMessage (new ErrorMessage
            ("Invalid context for " + getSelfPropName (),
             _module.getFilePos ()));
        _repInfo.setWellFormed (false);
    }
    
    /** Utility error reporting function for a box which is
     *  expected to have subboxes, but doesn't.
     */
    protected void emptyBox ()
    {
        _repInfo.setMessage (new ErrorMessage
            ("Box is empty", "Box type = " + getSelfPropName (),
             _module.getFilePos ()));
        _repInfo.setWellFormed (false);
    }
    
    
    /** Make a Property from the association list.
     *  Returns null if the list is empty. */
    protected Property makeAssocProperty ()
    {
        if (associations.isEmpty ()) {
            return null;
        }
        else return new Property ("Associations",
            PropertyType.PROPERTY,
            PropertyArity.LIST,
            associations);
    }
    
    /** Returns a Property which describes the Box, for use
     *  by Association boxes and perhaps others.
     *  Most subclasses will only have to override
     *  <code>getSelfPropName</code> and
     *  <code>getSelfPropDesc</code>.  A subclass
     *  that shouldn't be added to the Association box's
     *  property can override this to return <code>null</code>.
     */
    protected Property selfDescProperty () {
        List subprops = new ArrayList (2);
        String name = getSelfPropName ();
        if (name == null) {
            return null;
        }
        subprops.add (new Property ("Name",
            PropertyType.STRING,
            name));
        Property p2 = getSelfPropDesc ();
        if (p2 != null) {
            subprops.add (p2);
        }
        return new Property ("Box",
            PropertyType.PROPERTY,
            PropertyArity.LIST,
            subprops);
    }


    /** Returns the name of the Box. All Boxes should
     *  override this. */
    protected String getSelfPropName ()
    {
        return null;
    }

    /** Returns a Property which describes the box.  This is
     *  used as a subproperty of the Property returned by
     *  selfDescProperty. Properties that we don't care to
     *  describe don't have to override this.  This class
     *  should return either <code>null</code> or a property
     *  with <code>DESCRIPTION_NAME</code> for its name.
     */
    protected Property getSelfPropDesc (){
        return null;
    }
    
    /** Returns the length of the box, including header, based
     *  on the information in the header.
     */
    protected long getLength ()
    {
        return _boxHeader.getLength();
    }
}
