/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.pdf;

/**
 *  Class for Tokens which represent hexadecimally encoded PDF strings. 
 *  This class really has no justification as a separate entity.  Except
 *  for the way they're written, hexadecimal strings aren't different in
 *  any way from other strings.
 *
 *  @deprecated
 */
 public class Hexadecimal
    extends Literal
{
    /** Creates an instance of a hexadecimal string literal */
    public Hexadecimal ()
    {
        super ();
    }
}
