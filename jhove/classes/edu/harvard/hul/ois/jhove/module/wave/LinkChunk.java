/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 *
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;

import edu.harvard.hul.ois.jhove.module.iff.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import java.io.*;
import java.util.*;

import javax.xml.parsers.ParserConfigurationException;
import javax.xml.parsers.SAXParserFactory;

import org.xml.sax.SAXException;
import org.xml.sax.XMLReader;

/**
 * Implementation of the WAVE Link Chunk, as specified in
 * <cite>Specification of the Broadcast Wave Format:
 * A format for audio data files in broadcasting;
 * Supplement 4: &lt;link&gt; Chunk</cite>
 * (European Broadcasting Union)
 * 
 * @author Gary McGath
 *
 */
public class LinkChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public LinkChunk (
            ModuleBase module,
            ChunkHeader hdr,
            DataInputStream dstrm) {
        super(module, hdr, dstrm);
    }


    /** Reads a chunk and puts a BroadcastAudioExtension Property into
     *  the RepInfo object. 
     * 
     *  @return   <code>false</code> if the chunk is structurally
     *            invalid, otherwise <code>true</code>
     */
    public boolean readChunk(RepInfo info) throws IOException {
        WaveModule module = (WaveModule) _module;
        
        // We read the XML into a byte array, then use a ByteArrayXMPSource
        // to parse it.  This isn't XMP, but that code provides a ready-made
        // way to generate an XML InputSource.
        byte[] buf = new byte[(int) bytesLeft];
        ModuleBase.readByteBuf (_dstream, buf, module);
        ByteArrayInputStream bais = new ByteArrayInputStream (buf);
        ByteArrayXMPSource xs = new ByteArrayXMPSource (bais);
        
        try {
            // Create an InputSource to feed the parser.
            SAXParserFactory factory = 
                            SAXParserFactory.newInstance();
            factory.setNamespaceAware (true);
            XMLReader parser = factory.newSAXParser ().getXMLReader ();
            LinkChunkHandler handler = new LinkChunkHandler ();
            parser.setContentHandler (handler);
            parser.parse (xs);
            List fileNames = handler.getFileNames ();
            String id = handler.getID();
            if (!fileNames.isEmpty ()) {
                List plist = new ArrayList (2);
                plist.add (new Property ("FileNames",
                        PropertyType.STRING,
                        PropertyArity.LIST,
                        fileNames));
                if (id != null) {
                    plist.add (new Property ("ID",
                        PropertyType.STRING,
                        id));
                }
                
                module.addWaveProperty (new Property ("Link", 
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        plist));
            }
            
        }
        catch (SAXException se) {
            info.setMessage (new ErrorMessage
                ("SAXException in reading Link Chunk"));
            info.setValid (false);
            return true;
        }
        catch (ParserConfigurationException pe) {
            info.setMessage (new ErrorMessage
                ("ParserConfigurationException in reading Link Chunk"));
            info.setValid (false);
            return true;
        }
        return true;
    }
}
