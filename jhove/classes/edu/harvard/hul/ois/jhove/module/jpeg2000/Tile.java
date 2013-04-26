/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.jpeg2000;

import edu.harvard.hul.ois.jhove.*;
import java.util.*;

/**
 * Encapsulation of a JPEG 2000 tile in a codestream.
 *
 * @author Gary McGath
 *
 */
public class Tile extends MainOrTile {


    private List _tileParts;

    /* List of lengths (Long objects) found in PPT code segments */
    private List _pptLengthList;


    /**
     *  Constructor.
     */
    public Tile () 
    {
        
        _tileParts = new LinkedList ();
    }
    
    
    /** Adds a TilePart to the List of TileParts. */
    public void addTilePart (TilePart tp)
    {
        _tileParts.add (tp);
    }

    /** returns the List of TileParts.*/
    public List getTileParts ()
    {
        return _tileParts;
    }

    /** Adds a PPM tilepart header length to the list of lengths */
    public void addPPTLength (long len)
    {
        _pptLengthList.add (new Long (len));
    }

    /** Returns a Property describing the tile.
     *  The name of the Property is "Tile".  */
    public Property makeProperty ()
    {
        List propList = new LinkedList ();
        if (!_tileParts.isEmpty ()) {
            ListIterator tpiter = _tileParts.listIterator ();
            while (tpiter.hasNext ()) {
                TilePart tp = (TilePart) tpiter.next ();
                propList.add (tp.makeProperty ());
            }   
        }
        if (_components != null) {
            // It's possible only some components have overriding
            // properties.  Go through the array and set a stub
            // component for any that don't.
            for (int i = 0; i < _components.length; i++) {
                if (_components[i] == null) {
                    _components[i] = new Property ("Component",
                        PropertyType.PROPERTY,
                        PropertyArity.LIST,
                        new LinkedList ());
                }
            }
            propList.add (new Property ("Components",
                        PropertyType.PROPERTY,
                        PropertyArity.ARRAY,
                        _components));
        }
        if (_codProperty != null) {
            propList.add (_codProperty);
        }
        if (_qcdProperty != null) {
            propList.add (_qcdProperty);
        }
        if (_pocProperty != null) {
            propList.add (_pocProperty);
        }
        if (_packetLengthList != null && !_packetLengthList.isEmpty ()) {
            propList.add (new Property ("PacketLengths",
                        PropertyType.LONG,
                        PropertyArity.LIST,
                        _packetLengthList));
        }
        if (_pptLengthList != null && _pptLengthList.isEmpty ()) {
            propList.add (new Property ("PackedPacketHeaderLengths",
                        PropertyType.LONG,
                        PropertyArity.LIST,
                        _pptLengthList));
        }
        if (!_comments.isEmpty ()) {
            propList.add (new Property ("Comments",
                    PropertyType.PROPERTY,
                    PropertyArity.LIST,
                    _comments));
        }
        return new Property ("Tile",
                PropertyType.PROPERTY,
                PropertyArity.LIST,
                propList);
    }

}
