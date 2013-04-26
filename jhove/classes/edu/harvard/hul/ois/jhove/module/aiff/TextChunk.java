/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import java.io.DataInputStream;
import java.io.IOException;
import edu.harvard.hul.ois.jhove.*;
import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

/**
 * Abstract superclass for the name, author, copyright,
 * and annotation chunks, all of which have the same
 * format.
 *
 * @author Gary McGath
 *
 */
public abstract class TextChunk extends Chunk {

    /** Name of the property.  The subclass constructor
     * must set this appropriately. */
    protected String propName;
    
    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public TextChunk (AiffModule module, ChunkHeader hdr,
		      DataInputStream dstrm)
    {
        super(module, hdr, dstrm);
    }

    /** Reads a chunk and puts appropriate information into
     *  the RepInfo object. 
     * 
     *  This method works for TextChunk, CopyrightChunk and
     *  AuthorChunk.  AnnotationChunk overrides it, since there
     *  can be multiple annotations.
     */
    public boolean readChunk (RepInfo info)
	throws IOException
    {
        AiffModule module = (AiffModule) _module;
        String name = readText ();
        module.addAiffProperty (new Property (propName, PropertyType.STRING,
					      name));
        return true;
    }

    /**
     * Reads the chunk's text data.
     * All text chunk subclasses consist of a text string
     * which takes up the full byte count of the chunk.
     * By the specification, the text is required to be ASCII.
     */
    protected String readText ()
	throws IOException
    {
        byte[] buf = new byte[(int) bytesLeft];
        ModuleBase.readByteBuf (_dstream, buf, _module);
	/* Ensure that each byt is a printable ASCII character. */
	for (int i=0; i<buf.length; i++) {
	    if (buf[i] < 32 || buf[i] > 127) {
		buf[i] = 32;
	    }
	}
        return new String (buf, "ASCII");
    }
}
