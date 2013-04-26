/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

import java.io.FilterInputStream;
import java.io.InputStream;

/**
 * This is a stub which may be implemented in the future.
 * It appears to be unnecessary for object streams and cross-reference
 * streams created by any version of Acrobat through 7.0, and we
 * don't look at other types of streams.
 *
 * @author Gary McGath
 *
 */
public class RunLengthFilterStream extends FilterInputStream {

    /**
     * @param in
     */
    public RunLengthFilterStream(InputStream in) {
        super(in);
    }

}
