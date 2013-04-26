/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.wave;


import edu.harvard.hul.ois.jhove.RepInfo;
import edu.harvard.hul.ois.jhove.module.iff.*;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.WaveModule;
import java.io.*;
import java.util.*;

/**
 * Implementation of the WAVE Broadcast Audio Extension Chunk.
 *
 * @author Gary McGath
 *
 */
public class BroadcastExtChunk extends Chunk {

    /**
     * Constructor.
     * 
     * @param module   The WaveModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the WAVE data are being read
     */
    public BroadcastExtChunk (
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
        byte[] buf256 = new byte[256];
        ModuleBase.readByteBuf (_dstream, buf256, module);
        String description = byteBufString(buf256);
        byte[] buf32 = new byte[32];
        ModuleBase.readByteBuf (_dstream, buf32, module);
        String originator = byteBufString (buf32);
        ModuleBase.readByteBuf (_dstream, buf32, module);
        String originatorRef = byteBufString (buf32);
        byte[] buf10 = new byte[10];
        ModuleBase.readByteBuf (_dstream, buf10, module);
        String originationDate = byteBufString (buf10);
        byte[] buf8 = new byte[8];
        ModuleBase.readByteBuf (_dstream, buf8, module);
        String originationTime = byteBufString (buf8);
        // TimeReference is stored as a 64-bit little-endian
        // number -- I think
        long timeReference = module.readSignedLong (_dstream);
        int version = module.readUnsignedShort (_dstream);
        module.setBroadcastVersion (version);
        byte[] smtpe_umid = new byte[64];
        ModuleBase.readByteBuf (_dstream, smtpe_umid, module);
        module.skipBytes (_dstream, 190, module);
        String codingHistory = "";
        if (bytesLeft > 602) {
            byte[] bufCodingHistory = new byte[(int) bytesLeft - 602];
	    ModuleBase.readByteBuf (_dstream, bufCodingHistory, module);
            codingHistory = byteBufString (bufCodingHistory);
        }

        // Whew -- we've read the whole thing.  Now make that into a
        // list of Properties.
        List plist = new ArrayList (20);
        if (description.length () > 0) {
            plist.add (new Property 
                    ("Description", PropertyType.STRING, description));
        }
        if (originator.length () > 0) {
            plist.add (new Property 
                    ("Originator", PropertyType.STRING, originator));
        }
        if (originatorRef.length () > 0) {
            plist.add (new Property 
                    ("Originator Reference", PropertyType.STRING, originatorRef));
        }
        if (originationDate.length () > 0) {
            plist.add (new Property
                    ("OriginationDate", PropertyType.STRING, originationDate));
        }
        if (originationTime.length () > 0) {
            plist.add (new Property
                    ("OriginationTime", PropertyType.STRING, originationTime));
        }
        plist.add (new Property
                    ("TimeReference", PropertyType.LONG, new Long (timeReference)));
        plist.add (new Property
                    ("Version", PropertyType.INTEGER, new Integer (version)));
        plist.add (new Property ("UMID", 
                PropertyType.BYTE,
                PropertyArity.ARRAY,
                smtpe_umid));
        if (codingHistory.length () > 0) {
            plist.add (new Property
                    ("CodingHistory", PropertyType.STRING, codingHistory));
        }

        module.addWaveProperty (new Property ("BroadcastAudioExtension", 
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                plist));
				
	// set time reference in AES metadata set @author David Ackerman
	AESAudioMetadata aes = module.getAESMetadata ();
	aes.setStartTime (timeReference);

        return true;
    }

}
