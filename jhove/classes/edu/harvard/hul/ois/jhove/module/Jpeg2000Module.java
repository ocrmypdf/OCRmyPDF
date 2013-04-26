/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004-2007 by JSTOR and the President and Fellows of Harvard College
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

package edu.harvard.hul.ois.jhove.module;

import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.jpeg2000.*;
import java.io.*;
import java.util.*;

/**
 *  Module for identification and validation of JPEG 2000 files.
 * 
 *  Code is included for JPX, but is almost entirely untested due
 *  to the lack of available sample files that use more than a tiny
 *  fraction of the features.  The current version of the module
 *  is based on the typo-laden and inconsisent "JPEG 2000 Part II 
 *  Final Committee Draft" (7 December 2000).
 *  The final standard (5 May 2004) has just reached our hands,
 *  and this code will be reviewed against it and revised accordingly
 *  in the near future.  (All opinions expressed in this
 *  paragraph are those of the programmer.)
 * 
 *  JPEG 2000 format is not JPEG format, and isn't compatible
 *  with it.  As with JPEG, JPEG 2000 is not in itself
 *  a file format.  It can be encapsulated in JP2 or JPX format,
 *  which are recognized here.
 *
 *  @author Gary McGath
 */
public class Jpeg2000Module extends ModuleBase {

/*
 *   Some general notes on JPEG 2000 parsing:
 *   The format started out as a straightforward stream format, which
 *   could be parsed as a stream from beginning to end.  But JPX throws
 *   us several curves, requiring random access.  The Cross Reference
 *   Box is a direction to replace itself with another box somewhere
 *   else in the file (or even in one or more entirely different files!), which
 *   may be scattered through different parts of the file even if it
 *   doesn't spread to other files.  The Fragment Table Box  does the
 *   same for codestreams.  In addition, the Binary Filter Box allows
 *   boxes to be hidden within its compressed or encrypted data.  All this
 *   makes the concept of "parent box" trickier than it is in unextended
 *   JP2, since parenthood and containment are not necessarily the same thing.
 * 
 *   The way I've chosen deal with this rather chimerical design is to
 *   have a RandomAccessFile for a base, but have each Box based on a
 *   DataInputStream.  Not every Box has its own separate stream -- that
 *   would be wasteful -- but there can be multiple box streams active at
 *   once.  Each box (JP2Box) has a parent (BoxHolder), which can be 
 *   another JP2Box or a TopLevelBoxHolder.  The extension to multiple
 *   files isn't supported here, since the job of Jhove is to validate
 *   individual files, but it wouldn't be difficult to add.  
 * 
 *   Every BoxHolder (hence every box) implements the Iterator interface, 
 *   so that a box can get its subboxes in a way which is blind to the 
 *   details of their encoding.  
 */

    /******************************************************************
     * PRIVATE CLASS FIELDS.
     ******************************************************************/

    private static final String NAME = "JPEG2000-hul";
    private static final String RELEASE = "1.3";
    private static final int[] DATE = { 2007, 1, 8 };
    private static final String[] FORMAT = { "JPEG 2000", "JP2", "JPX" };
    private static final String COVERAGE = "JP2 (ISO/IEC 15444-1:2000/" +
	"ITU-T Rec. T.800 (200)), JPX (ISO/IEC 15444-2:2004)";
    private static final String[] MIMETYPE = { "image/jp2", "image/jpx" };
    private static final String WELLFORMED =
	"The required Signature and File Type box structures are the first " +
	"two boxes in the file; all boxes required by a given profile exist " +
	"in the file; all box structures are well-formed (a four byte " +
	"unsigned integer Box Length, followed by a four byte unsigned " +
	"integer Box type, followed by a eight byte unsigned integer Box " +
	"Length, followed by the Box Contents); no data exist before the " +
	"first byte of the first box or after the last byte of the last box";
    private static final String VALIDITY = "The file is well-formed";
    private static final String REPINFO =
	"Properties capturing the technical attributes of the JPEG 2000 " +
	"image from all boxes";
    private static final String NOTE = null;
    private static final String RIGHTS =
        "Copyright 2004-2007 by JSTOR and the "
            + "President and Fellows of Harvard College. "
            + "Released under the GNU Lesser General Public License.";

    /******************************************************************
     * PRIVATE INSTANCE FIELDS.
     ******************************************************************/

    /* NISO image metadata for the current image */
    protected NisoImageMetadata _niso;

    /* NISO image metadata for default image values */
    protected NisoImageMetadata _defaultNiso;

    /* DataInputSream for reading the file */
    protected DataInputStream _dstream;

    /* RandomAccessFile for reading the file */
    protected RandomAccessFile _raf;
    
    /* RAFInputStream underlying the DataInputStream */
    protected RAFInputStream _rafStream;

    /* Properties which are global to the file */
    protected List<Property> _propList;

    /* List of codestreams.  An entry can be created by
     * either a codestream or a codestream header, depending
     * on which is seen first.  The elements of the List
     * are Codestream objects. */
    protected List<Codestream> codestreams;

    /* List of Binary Filter properties. */
    protected List<Property> binaryFilterProps;
    
    /* List of Association properties. */
    protected List<Property> associationProps;
    
    /* List of Digital Signature properties. */
    protected List<Property> digitalSigProps;

    /* Number of Contiguous Codestreams seen.
     * May be less than or equal to the size of codestreams. */
    protected int nCodestreams;

    /* Number of Codestream headers seen */
    protected int nCodestreamHeaders;

    /* List of Color Spec properties */
    protected List<Property> colorSpecs;

    /* List of UUIDBox properties */
    protected List<Property> uuids;
    
    /* List of Compositing Layer properties */
    protected List<Property> composLayers;
    
    /* List of UUID Info properties */
    protected List<Property> uuidInfos;

    /* List of data (String) extracted from XML boxes */
    protected List<String> xmlList;

    /* Flag for JP2 headerbox detection */
    protected boolean jp2HdrSeen;

    /* Flag for Reader Requirements detection */
    protected boolean rreqSeen;
    
    /* Flag for Color Specification detection */
    protected boolean colorSpecSeen;
        
    /* Flag for Image Header Box detection */
    protected boolean imageHeaderSeen;

    /* Flag for JP2 compliance */
    protected boolean jp2Compliant;

    /* Flag for JPX compliance */
    protected boolean jpxCompliant;

    /* The Codestream currently being worked on.  This
     * is an element of codestreams */
    protected Codestream curCodestream;

    /* Flag which is true when we are reading a 
     * BinaryFilterBox, which needs special handling
     * for byte counts. */
    protected boolean filterMode;

    /* Fixed value for first 12 bytes */
    private static final int[] sigByte =
        {
            0X00,
            0X00,
            0X00,
            0X0C,
            0X6A,
            0X50,
            0X20,
            0X20,
            0X0D,
            0X0A,
            0X87,
            0X0A };

    /******************************************************************
    * CLASS CONSTRUCTOR.
    ******************************************************************/
    /**
      *  Instantiate a <tt>JpegModule</tt> object.
      */
    public Jpeg2000Module() {
        super(
            NAME,
            RELEASE,
            DATE,
            FORMAT,
            COVERAGE,
            MIMETYPE,
            WELLFORMED,
            VALIDITY,
            REPINFO,
            NOTE,
            RIGHTS,
            true);

        Agent agent =
            new Agent("Harvard University Library", AgentType.EDUCATIONAL);
        agent.setAddress(
            "Office for Information Systems, "
                + "90 Mt. Auburn St., "
                + "Cambridge, MA 02138");
        agent.setTelephone("+1 (617) 495-3724");
        agent.setEmail("jhove-support@hulmail.harvard.edu");
        _vendor = agent;

       Document doc = new Document ("Information technology -- " +
        "JPEG 2000 image coding system -- Part 1: Code coding system",
               DocumentType.STANDARD);
       Agent isoAgent = new Agent ("ISO", AgentType.STANDARD);
       isoAgent.setAddress ("1, rue de Varembe, Casa postale 56, " +
                 "CH-1211, Geneva 20, Switzerland");
       isoAgent.setTelephone ("+41 22 749 01 11");
       isoAgent.setFax ("+41 22 733 34 30");
       isoAgent.setEmail ("iso@iso.ch");
       isoAgent.setWeb ("http://www.iso.org/");
       doc.setAuthor (isoAgent);
       doc.setIdentifier (new Identifier ("ISO/IEC 15444-1:2000",
                IdentifierType.ISO));
       doc.setDate ("2002-07-31");
       _specification.add (doc);

       doc = new Document ("Information technology -- " +
        "JPEG 2000 image coding system -- " +
        "Part 2: Extensions",
               DocumentType.STANDARD);
       doc.setAuthor (isoAgent);       // ISO agent
       doc.setIdentifier (new Identifier ("ISO/IEC 15444-2:2004",
                IdentifierType.ISO));
       doc.setDate ("2004-05-15");
       _specification.add (doc);
       
       doc = new Document ("MIME Type Registrations for JPEG 2000 " +
                "(ISO/IEC 15444) RFC 3745",
                DocumentType.RFC);
       Agent ietfAgent = new Agent ("IETF", AgentType.STANDARD);
       ietfAgent.setWeb ("http://www.ietf.org");
       doc.setPublisher (ietfAgent);
       agent = new Agent ("D. Singer",
                AgentType.OTHER);
       doc.setAuthor(agent);
       agent = new Agent ("R. Clark",
                AgentType.OTHER);
       doc.setAuthor(agent);
       agent = new Agent ("D. Lee",
                AgentType.OTHER);
       doc.setAuthor(agent);
       doc.setDate ("2004-04");
       Identifier ident = new Identifier 
           ("http://www.ietf.org/rfc/rfc3745.txt",
            IdentifierType.URL);
       doc.setIdentifier (ident);
       _specification.add (doc);

       doc = new Document ("ITU-T Rec. T.800 (2002), Information " +
			   "technology -- JPEG 2000 image coding system: " +
			   "Core coding system",
            DocumentType.STANDARD);
       Agent ituAgent = new Agent ("ITU", AgentType.STANDARD);
       ituAgent.setAddress("ITU, Place des Nations, " +
			   "CH-1211 Geneva 20 Switzerland");
       ituAgent.setTelephone("+41 22 730 51 11");
       ituAgent.setFax("+41 22 730 6500");
       ituAgent.setEmail ("itumail@itu.int");
       ituAgent.setWeb ("http://www.itu.int/home/");
       doc.setAuthor (ituAgent);
       doc.setDate ("2002-08");
       ident = new Identifier ("ITU-T Rec. T.800 (2002)", 
            IdentifierType.ITU);
       doc.setIdentifier (ident);
       _specification.add (doc);


        Signature sig =
            new InternalSignature (sigByte, SignatureType.MAGIC, 
                                   SignatureUseType.MANDATORY, 0,
                                   "");
        _signature.add (sig);

        sig =
            new ExternalSignature(
                ".jp2",
                SignatureType.EXTENSION,
                SignatureUseType.OPTIONAL);
        _signature.add(sig);

        sig =
            new ExternalSignature(
                ".jpx",
                SignatureType.EXTENSION,
                SignatureUseType.OPTIONAL);
        _signature.add(sig);

        sig =
            new ExternalSignature(
                ".jpf",
                SignatureType.EXTENSION,
                SignatureUseType.OPTIONAL);
        _signature.add(sig);

        // Macintosh signature for JP2 files
        sig =
            new ExternalSignature(
                "jp2 ",
                SignatureType.FILETYPE,
                SignatureUseType.OPTIONAL);
        _signature.add(sig);

        // Macintosh signature for JPX files
        sig =
            new ExternalSignature(
                "jpx ",
                SignatureType.FILETYPE,
                SignatureUseType.OPTIONAL);
        _signature.add(sig);
        
        _bigEndian = true;
    }

    /**
     *   Parse the content of a stream digital object and store the
     *   results in RepInfo.
     * 
     *   This module is based on a RandomAccessFile because of the
     *   requirements of the (so far) rarely used fragmented codestream
     *   feature.  Since just about everything else can be done with
     *   an InputStream, we use a RAFInputStream except on the occasions
     *   when random access is needed.  We pass the module as the <code>counted</code>
     *   argment to all read calls, so that we can compute relative
     *   positions in the stream based on _nByte.
     * 
     *   @param raf    A RandomAccessFile to be parsed.
     * 
     *   @param info      A fresh (on the first call) RepInfo object 
     *                    which will be modified
     *                    to reflect the results of the parsing
     *                    If multiple calls to <code>parse</code> are made 
     *                    on the basis of a nonzero value being returned, 
     *                    the same RepInfo object should be passed with each
     *                    call.
     */
    public final void parse(RandomAccessFile raf, RepInfo info)
        throws IOException {
        initParse();
        _rafStream = new RAFInputStream (raf,
                _je != null ? _je.getBufferSize() : 0);
        _dstream = new DataInputStream
                (_rafStream);
        info.setFormat(_format[0]);
        info.setMimeType(_mimeType[0]);
        info.setModule(this);

        _propList = new ArrayList<Property>(12);
        Property metadata =
            new Property(
                "JPEG2000Metadata",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                _propList);

        _raf = raf;

        // A JPEG 2000 file consists of a series of "boxes."
        // The signature box must match the signature bytes.
        int i = 0;
        boolean badhdr = false;
        try {
            for (i = 0; i < 12; i++) {
                int ch;
                ch = readUnsignedByte(_dstream, this);
                if (ch != sigByte[i]) {
                    badhdr = true;
                    break;
                }
            }
        }
        catch (IOException e) {
            badhdr = true;
        }
        if (badhdr) {
            info.setMessage (new ErrorMessage ("No JPEG 2000 header", i));
            info.setWellFormed(false);
            return;
        }

        /* If we got this far, take note that the signature is OK. */
        info.setSigMatch(_name);

        // Next check the file type box. 
        if (!readFileTypeBox(info)) {
            return;
        }

        // Go through the rest of the boxes.
        if (!readBoxes(info)) {
            return;
        }
        
        if (info.getWellFormed() == RepInfo.FALSE) {
            return;
        }

        // File has been read successfully; do final processing.

        info.setProperty(metadata);

        // Calculate checksums, if necessary. 
        if (_je != null && _je.getChecksumFlag ()) {
            if (info.getChecksum ().size () == 0) {
                Checksummer ckSummer = new Checksummer ();
                calcRAChecksum (ckSummer, raf);
                setChecksums (ckSummer, info);
            }
        }

        // Reader Requirements box is mandatory for JPX
        if (!rreqSeen || info.getValid() != RepInfo.TRUE) {
            jpxCompliant = false;
        }
        if (!imageHeaderSeen ||  !colorSpecSeen || info.getValid() != RepInfo.TRUE) {
            jp2Compliant = false;
        }
        if (jp2Compliant) {
            info.setProfile("JP2");
        }
        if (jpxCompliant) {
            info.setProfile ("JPX");
            String mime = _mimeType[1];
            info.setMimeType(mime);
            curCodestream.getNiso().setMimeType (mime);
            // This doesn't deal with a case where some
            // codestreams are JP2 and others are JPX;
            // can that happen?
            _defaultNiso.setMimeType (mime);
        }

        if (!colorSpecs.isEmpty()) {
            _propList.add(
                new Property(
                    "ColorSpecs",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    colorSpecs));
        }
        if (!binaryFilterProps.isEmpty ()) {
            _propList.add(
                new Property(
                    "BinaryFilters",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    binaryFilterProps));
        }
        if (!associationProps.isEmpty ()) {
            _propList.add(
                new Property(
                    "Associations",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    associationProps));
        }

        if (!digitalSigProps.isEmpty ()) {
            _propList.add(
                new Property(
                    "DigitalSignatures",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    digitalSigProps));
        }
        if (!uuids.isEmpty()) {
            _propList.add(
                new Property(
                    "UUIDs",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    uuids));
        }
        if (!composLayers.isEmpty ()) {
            _propList.add(
                new Property(
                    "CompositingLayers",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    composLayers));
        }
        if (!uuidInfos.isEmpty()) {
            _propList.add(
                new Property(
                    "UUIDInfoBoxes",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    uuidInfos));
        }
        if (!codestreams.isEmpty()) {
            List<Property> csProps = new ArrayList<Property>(codestreams.size());
            ListIterator<Codestream> csIter = codestreams.listIterator();
            while (csIter.hasNext()) {
                Codestream cs = (Codestream) csIter.next();
                csProps.add(cs.makeProperty());
            }
            _propList.add(
                new Property(
                    "Codestreams",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    csProps));

        }
        if (!xmlList.isEmpty()) {
            _propList.add(
                new Property(
                    "XML",
                    PropertyType.STRING,
                    PropertyArity.LIST,
                    xmlList));
        }

        return;
    }

    /**
     *   Return the current position in the module.
     *   This is somewhat optimistically named; it should
     *   be trusted only for relative positions when no
     *   seek operations occur in between calls to getFilePos.
     */
    public long getFilePos() {
        // return _nByte;
        try {
            return _rafStream.getFilePos ();
        }
        catch (IOException e) {
            // really shouldn't happen
            return 0;
        }
    }
    
    /**  Seek to a new file position. */
    public void seek (long pos) throws IOException {
        _rafStream.seek (pos);
    }

    /** Returns the default NisoImageMetadata object. */
    public NisoImageMetadata getDefaultNiso() {
        return _defaultNiso;
    }

    /** Returns the current NisoImageMetadata object.
     *  If curCodestream is null, returns the default
     *  NisoImageMetadata, otherwise returns the 
     *  NisoImageMetadata of curCodestream.
     */
    public NisoImageMetadata getCurrentNiso() {
        if (curCodestream == null) {
            return _defaultNiso;
        } else {
            return curCodestream.getNiso();
        }
    }

    /** Returns the nth <code>Codestream</code>, creating it if necessary,
     *  and make it the current one.  The value of <code>nCodestreams</code>
     *  or <code>nCodestreamHeaders</code>
     *  is not affected, even if a new <code>Codestream</code> is created. */
    public Codestream getCodestream(int n) {
        Codestream cs;
        if (n < codestreams.size()) {
            cs = (Codestream) codestreams.get(n);
        } else {
            cs = new Codestream();
            cs.setDefaultNiso(_defaultNiso);
            codestreams.add(cs);
        }
        curCodestream = cs;
        return cs;
    }

    /** Returns the codestream count.  
     *  Because items may be added to the codestreams list
     *  when only the header is seen, this may be less than
     *  the size of the codestreams list.  It will never be
     *  more. */
    public int getNCodestreams() {
        return nCodestreams;
    }
    
    /** Returns the codestream header count. */
    public int getNCodestreamHeaders() {
        return nCodestreamHeaders;
    }
    

    public boolean isJP2HdrSeen() {
        return jp2HdrSeen;
    }

    /** Sets the codestream count.  This affects only the
     *  variable, not the size of the codestreams list.
     *  The codestream count should never be set to a value
     *  larger than the codestreams list; it signifies the
     *  number of elements of the list for which codestream
     *  boxes have actually been seen.
     */
    public void setNCodestreams(int n) {
        nCodestreams = n;
    }
    
    /** Sets the codestream header count. */
    public void setNCodestreamHeaders(int n) {
        nCodestreamHeaders = n;
    }
    
    /** Set the flag indicating that a JP2 header
     *  has been seen. */
    public void setJP2HdrSeen(boolean b) {
        jp2HdrSeen = b;
    }
    
    /** Set the flag indicating the reader requirements box
     *  has been seen. */
    public void setRReqSeen (boolean b) {
        rreqSeen = b;
    }

    
    /** Set the flag indicating the color specification box
     *  has been seen. */
    public void setColorSpecSeen (boolean b) {
        colorSpecSeen = b;
    }
    
    /** Set the flag indicating the color specification box
     *  has been seen. */
    public void setImageHeaderSeen (boolean b) {
        imageHeaderSeen = b;
    }


    /** Sets a flag indicating JP2 compliance.  If the
     *  flag is set to <code>true</code>, and the JPX
     *  compliance flag is also true, set the MIME type
     *  to "image/jpx". */
    public void setJP2Compliant(boolean b) {
        jp2Compliant = b;
        if (jp2Compliant && jpxCompliant) {
            _defaultNiso.setMimeType(MIMETYPE[1]);
        }
    }

    /** Sets a flag indicating JPX compliance. */
    public void setJPXCompliant(boolean b) {
        jpxCompliant = b;
    }

    /** Adds a property to the JPEG2000 metadata.*/
    public void addProperty(Property p) {
        _propList.add(p);
    }

    /** Adds a color spec property to the metadata. */
    public void addColorSpec(Property p) {
        colorSpecs.add(p);
    }
    
    /** Adds a binary filter property to the metadata. */
    public void addBinaryFilterProp (Property p) {
        binaryFilterProps.add (p);
    }
    
    /** Adds an association property to the metadata. */
    public void addAssociationProp (Property p) {
        associationProps.add (p);
    }

    /** Adds a digital signature property to the metadata. */
    public void addDigitalSignatureProp (Property p)
    {
        digitalSigProps.add (p);
    }

    /** Adds a UUID property to the list of UUID
     *  properties.  Called from the UUIDBox.
     */
    public void addUUID(Property p) {
        uuids.add(p);
    }
    
    /** Adds a UUIDInfo property to the list of UUIDInfo
     *  properties.  Called from UUIDInfoBox.
     */
    public void addUUIDInfo(Property p) {
        uuidInfos.add(p);
    }

    /** Adds a Compositing Layer property to the list
     *  of Compositing Layer properties.  Called
     *  from the ComposLayerHdrBox. */
    public void addComposLayer (Property p) {
        composLayers.add (p);
    }

    /** Adds an XML string to the list of XML properties.
     *  Called from XMLBox. */
    public void addXML(String s) {
        xmlList.add(s);
    }

    /**
     *   Reads 4 bytes and concatenates them into a String.
     */
    public String read4Chars(DataInputStream stream) throws IOException {
        StringBuffer sbuf = new StringBuffer(4);
        for (int i = 0; i < 4; i++) {
            int ch = readUnsignedByte(stream, this);
            sbuf.append((char) ch);
        }
        return sbuf.toString();
    }

    /** One-argument version of <code>readUnsignedShort</code>.
     *  JPEG2000 is always big-endian, so readUnsignedShort can
     *  unambiguously drop its endian argument. */
    public int readUnsignedShort(DataInputStream stream) throws IOException {
        return readUnsignedShort(stream, true, this);
    }

    /** One-argument version of <code>readUnsignedInt</code>.
     *  JPEG2000 is always big-endian, so readUnsignedInt can
     *  unambiguously drop its endian argument. */
    public long readUnsignedInt(DataInputStream stream) throws IOException {
        return readUnsignedInt(stream, true, this);
    }

    /** One-argument version of <code>readSignedLong</code>.
     *  JPEG2000 is always big-endian, so readSignedLong can
     *  unambiguously drop its endian argument. */
    public long readSignedLong(DataInputStream stream) throws IOException {
        return readSignedLong(stream, true, this);
    }

    /**
     *   Initializes the state of the module for parsing.
     */
    protected void initParse() {
        super.initParse();
        colorSpecs = new LinkedList<Property>();
        binaryFilterProps = new LinkedList<Property> ();
        associationProps = new LinkedList<Property> ();
        digitalSigProps = new LinkedList<Property> ();
        uuids = new LinkedList<Property>();
        uuidInfos = new LinkedList<Property>();
        composLayers = new LinkedList<Property> ();
        xmlList = new LinkedList<String>();
        //uuidList = new LinkedList ();
        codestreams = new LinkedList<Codestream>();
        curCodestream = null;
        nCodestreams = 0;
        nCodestreamHeaders = 0;
        jp2HdrSeen = false;
        //paletteSeen = false;
        //cmSeen = false;
        rreqSeen = false;
        filterMode = false;
        _defaultNiso = new NisoImageMetadata();
        _defaultNiso.setByteOrder("big-endian");
        _defaultNiso.setMimeType(MIMETYPE[0]);

        // Compliance flags are innocent till proven guilty
        jp2Compliant = true;
        jpxCompliant = true;
    }

    /*  Dispatcher for reading boxes.  Because of the existence
     *  of filter boxes, any box can come from either _dstream
     *  or from a separate input stream that is being undeflated.
     *  This dispatcher always works from _dstream.  We must 
     *  pass a stream to every box function, to allow these
     *  multiple sources.
     */
    protected boolean readBoxes(RepInfo info) throws IOException {
        // From here on, boxes may occur with some freedom
        // of order.  Apparently the only indication that
        // we're done is an end-of-file condition.

        TopLevelBoxHolder bh = new TopLevelBoxHolder (this, _raf, info,
						      _dstream);
        while (bh.hasNext ()) {
            JP2Box box = (JP2Box) bh.next ();
            // TopLevelBoxHolder.next() may not be reliable about detecting 
            // that no more boxes are left.
            if (box == null) {
                break;
            }
            if (!box.readBox ()) {
                return false;
            }
        }

        return true;
    }

    /* Read the file type box.  This assumes that we are actually
     * positioned at the file type box, and reads its header.
     * If we get something other than a file type box, the file
     * is not well-formed.
     */
    protected boolean readFileTypeBox(RepInfo info) throws IOException {
        BoxHeader hdr = new BoxHeader(this, _dstream);
        hdr.readHeader();
        // 8 bytes have been read
        if (!"ftyp".equals(hdr.getType())) {
            info.setMessage(
                new ErrorMessage(
                    "Expected File Type Box, got " + hdr.getType(),
                    _nByte));
            info.setWellFormed(false);
            return false;

        }
        FileTypeBox box = new FileTypeBox(_raf);
        box.setBoxHeader(hdr);
        box.setDataInputStream(_dstream);
        box.setRandomAccessFile (_raf);
        box.setModule(this);
        box.setRepInfo(info);
        if (!box.readBox()) {
            return false;
        }
        return true;
    }

    /* This is called for any box that isn't recognized, or
     * by placeholder methods for boxes that haven't yet
     * been coded. */
    protected boolean skipOverBox(
        BoxHeader hdr,
        RepInfo info,
        DataInputStream dstrm)
        throws IOException {
        if (hdr.getLength() != 0) {
            skipBytes(dstrm, (int) hdr.getDataLength(), this);
        }
        return true;
    }
}
