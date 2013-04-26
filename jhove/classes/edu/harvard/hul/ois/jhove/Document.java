/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2003 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove;

import java.util.*;

/** 
 *  This class encapsulates information about format specification documents.
 *
 *  @see  DocumentType
 */
public class Document
{
    private List _author;
    private String _date;
    private String _edition;
    private String _enum;
    private List _identifier;
    private String _note;
    private String _pages;
    private List _publisher;
    private String _title;
    private DocumentType _type;

    /**
     *  Creates a Document with a given title and one of the predefined
     *  DocumentTypes.
     */
    public Document (String title, DocumentType type)
    {
    _title = title;
    _type  = type;

    _author     = new ArrayList ();
    _identifier = new ArrayList ();
    _publisher  = new ArrayList ();
    }

    /**
     *  Returns a List of Agents, each representing an author of this
     *  Document.
     *  Returns an empty list if no authors have been listed.
     *
     *  @see Agent
     */
    public List getAuthor ()
    {
    return _author;
    }
    
    /**
     *  Returns the date of this Document
     */
    public String getDate ()
    {
    return _date;
    }

    /**
     *   Returns informaton on the edition of this Document
     */
    public String getEdition ()
    {
    return _edition;
    }

    /**
     *  Returns the enumeration (e.g., serial volume and number)
     *  of this Document
     */
    public String getEnumeration ()
    {
    return _enum;
    }

    /**
     *  Returns the list of formal Identifiers for this Document.
     *  If no Identifiers are given, returns an empty list.
     */
    public List getIdentifier ()
    {
    return _identifier;
    }

    /**
     *  Returns the note associated with this Document
     */
    public String getNote ()
    {
    return _note;
    }

    /**
     *  Returns pagination information for this Document
     */
    public String getPages ()
    {
    return _pages;
    }

    /**
     *  Returns a List of Agents, each representing a publisher of this
     *  Document.  If no publishers are listed, returns an empty list.
     */
    public List getPublisher ()
    {
    return _publisher;
    }

    /**
     *  Returns the title of this Document 
     */
    public String getTitle ()
    {
    return _title;
    }

    /**
     *  Returns one of the predefined DocumentTypes as the type of
     *  this Document
     */
    public DocumentType getType ()
    {
    return _type;
    }

    /**
     *  Adds an author to the list of authors
     */
    public void setAuthor (Agent author)
    {
    _author.add (author);
    }

    /**
     *  Sets the date of this Document
     */
    public void setDate (String date)
    {
    _date = date;
    }

    /**
     *  Sets edition information for this Document
     */
    public void setEdition (String edition)
    {
    _edition = edition;
    }

    /**
     *  Sets enumeration information (e.g., serial volume and number)
     *  for this Document
     */
    public void setEnumeration (String enm)
    {
    _enum = enm;
    }

    /**
     *  Adds an Identifier to the list of identifiers
     */
    public void setIdentifier (Identifier identifier)
    {
    _identifier.add (identifier);
    }

    /**
     *  Sets a note giving additional information about this Document
     */
    public void setNote (String note)
    {
    _note = note;
    }

    /**
     *  Sets pagination information for this Document
     */
    public void setPages (String pages)
    {
    _pages = pages;
    }

    /**
     *  Adds a publisher to the list of publishers
     */
    public void setPublisher (Agent publisher)
    {
    _publisher.add (publisher);
    }
}
