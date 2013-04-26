/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.aiff;

import java.io.DataInputStream;
import edu.harvard.hul.ois.jhove.module.AiffModule;
import edu.harvard.hul.ois.jhove.module.iff.*;

/**
 * Implementation of the AIFF Author Chunk.
 *
 * @author Gary McGath
 *
 */
public class AuthorChunk extends TextChunk {

    /**
     * Constructor.
     * 
     * @param module   The AIFFModule under which this was called
     * @param hdr      The header for this chunk
     * @param dstrm    The stream from which the AIFF data are being read
     */
    public AuthorChunk(
        AiffModule module,
        ChunkHeader hdr,
        DataInputStream dstrm) 
    {
        super(module, hdr, dstrm);
        propName = "Author";
    }


}
