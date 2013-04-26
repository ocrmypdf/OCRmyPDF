/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import edu.harvard.hul.ois.jhove.*;
import java.util.*;
//import java.io.*;



/**
 * This is an abstract class for processing an HTML document that has
 * been parsed into a List of HtmlElements.  It defines common behavior
 * for all supported versions of HTML except XHTML.  Subclasses 
 * modify this base as needed.
 *
 * @author Gary McGath
 *
 */
public abstract class HtmlDocDesc {

    /** Metadata for this document. */
    private HtmlMetadata metadata;
    
    /** Generic list of supported tags.  For efficiency, this is
     * generated only once.  Subclasses will need to get a copy
     * of this list and make additions or deletions as necessary.
     * They must not modify any of the existing
     * members of the list. */
    protected static HashMap commonTags;
    
    /** List of supported tags for this version of HTML.  The subclass
     * is responsible for generating this, typically using commonTags
     * as a starting point. */
    protected Map supportedElements;
    
    /** A representation of the HTML element. */
    protected HtmlTagDesc htmlElement;
    /** A representation of the HEAD element. */
    protected HtmlTagDesc headElement;
    /** A representation of the BODY element. */
    protected HtmlTagDesc bodyElement;
    /** A representation of the FRAMESET element. */
    protected HtmlTagDesc framesetElement;
    
    
    
    private HtmlStack elementStack;
    
    /** Header tags, which are invariant for all HTML versions. */
    protected static String[] headings = 
            { "h1", "h2", "h3", "h4", "h5", "h6" };

    
    /** Consructor.   */
    public HtmlDocDesc ()
    {
    }
    
    /** Validates the document and puts interesting properties into the
     *  RepInfo.
     * 
     *  @param  elements    The element list constructed by the parser
     *  @param  info        The RepInfo object which will be populated
     *                      with properties
     */
    public boolean validate (List elements, RepInfo info) {
        // As we get to each open tag, we 
        // check it against the corresponding HtmlTagDesc.  If there isn't one, we
        // mark the document as invalid but continue anyway; we create a temporary
        // HtmlTagDesc object for the tag that we find, with the closing tag indicated
        // as optional.
        // For each open tag, we push the HtmlTagDesc object onto the stack.  We check
        // if it's in the allowed content of the enclosing element.  If not, we report it
        // as an error but continue with it anyway.  
        //
        // We special-case HTML, HEAD and BODY, which can be implied.
        // If a tag is found which requires the content model for one of
        // these, and it isn't on the stack, we just push it. 
        
        metadata = new HtmlMetadata ();
        elementStack = new HtmlStack ();
        elementStack.setHeadElement (headElement);
        elementStack.setBodyElement (bodyElement);
        elementStack.setFramesetElement (framesetElement);
        Iterator iter = elements.iterator();
        while (iter.hasNext ()) {
            JHElement elem = (JHElement) iter.next ();
            if (elem instanceof JHDoctype) {
                // Doctype requires no further processing; grammar
                // will have already caught it if it's not at the top
                continue;
            }
            else if (elem instanceof JHOpenTag) {
                doOpenTag ((JHOpenTag) elem, info);
            }
            else if (elem instanceof JHCloseTag) {
                doCloseTag ((JHCloseTag) elem, info);
            }
            else if (elem instanceof JHErrorElement) {
                doErrorElement ((JHErrorElement) elem, info);
            }
            else if (elem instanceof JHPCData) {
                doPCData ((JHPCData) elem, info, metadata);
            }
        }
        // It's a requirement that there be at least a TITLE,
        // and thus an implicit or explicit HEAD element.
        if (!elementStack.isHeadSeen ()) {
            info.setMessage(new ErrorMessage 
                ("Document must have implicit or explicit HEAD element"));
            info.setValid (false);
        }
        return true;
    }


    /** Returns the metadata for this document. */
    public HtmlMetadata getMetadata ()
    {
        return metadata;
    }

    /** Initialization called by subclass constructors after supportedElements
     *  has been assigned. */
    protected void init ()
    {
        htmlElement = (HtmlTagDesc) supportedElements.get ("html");
        headElement = (HtmlTagDesc) supportedElements.get ("head");
        bodyElement = (HtmlTagDesc) supportedElements.get ("body");
    }
    
    
        
    /* Break out open tag code */
    private void doOpenTag (JHOpenTag tag, RepInfo info)
    {
        String name = tag.getName ().toLowerCase ();
        boolean unknownTag = false;
        
        String msg = tag.getErrorMessage ();
        if (msg != null) {
            info.setMessage (new ErrorMessage
                (msg, 
                 "Name = " + name + ", Line = " + 
                     tag.getLine () + ", Column = " +
                     tag.getColumn () ));
            info.setWellFormed (false);
            // But keep going anyway!
        }
        
        /* If it's anything but an HTML tag, and the stack is empty,
         * push an "HTML" element. */
        if (elementStack.isEmpty ()) {
            if (!"html".equals (name)) {
                JHOpenTag fakeTag = new JHOpenTag ("html");
                fakeTag.setElement (htmlElement);
                elementStack.push (fakeTag);
            }
        }
        HtmlTagDesc tagDesc = 
            (HtmlTagDesc) supportedElements.get (name);
        if (tagDesc == null) {
            unknownTag = true;
        }
        // Check the context only if it's a known tag;
        // otherwise we'll issue a redundant error message.
        if (!unknownTag && !checkElementContext (tag, info)) {
            String toptag = null;
            if (!elementStack.isEmpty ()) {
                JHOpenTag top = (JHOpenTag) elementStack.top();
                toptag = top.getName();
            }
            info.setMessage (new ErrorMessage
                    ("Tag illegal in context",
                     "Name = " + name + ", " + 
                     (toptag != null ? "Container = " + toptag + ", " : "") +
                     "Line = " + tag.getLine () + ", Column = " +
                     tag.getColumn () ));
            info.setValid (false);
        }
        if (unknownTag) {
            info.setMessage (new ErrorMessage 
                    ("Unknown tag",
                     "Name = " + name + ", Line = " + 
                     tag.getLine () + ", Column = " +
                     tag.getColumn ()));
            info.setValid (false);
            // Make a temporary tag descriptor
            tagDesc = new HtmlTempTagDesc (name);
        }
        if (!unknownTag && info.getWellFormed() == RepInfo.TRUE) {
            /* Check if the attributes are valid */
            List atts = tag.getAttributes ();
            Iterator iter = atts.iterator ();
            // Create a list to accumulate all attribute names.
            List attNames = new ArrayList (atts.size ());
            while (iter.hasNext ()) {
                JHAttribute att = (JHAttribute) iter.next ();
                String attName = att.getName();
                attNames.add (attName);
                String attVal = att.getValue();
                HtmlAttributeDesc attDesc = 
                    tagDesc.namedAttDesc (attName);
                if (attDesc == null) {
                    info.setMessage ( new ErrorMessage
                        ("Undefined attribute for element",
                         "Name = " + name + ", Attribute = " + 
                         attName + ", Line = " + att.getLine () +
                          ", Column = " + att.getColumn ()));
                    info.setValid (false);
                }
                else {
                    /* Check if value is legit */
                    if (!attDesc.valueOK (attName, attVal)) {
                        info.setMessage (new ErrorMessage
                            ("Improper value for attribute",
                             "Element = " + name + ", Attribute = " + 
                             attName + ", Value = " + attVal + 
                             ", Line = " + att.getLine () + 
                             ", Column = " + att.getColumn ()));
                        info.setValid (false);
                    }
                }
                // Extract entities from attribute value
                if (attVal != null) {
                    Iterator entIter = tag.getEntities (attVal).iterator ();
                    Utf8BlockMarker utf8BM = metadata.getUtf8BlockMarker ();
                    while (entIter.hasNext ()) {
                        String ent = (String) entIter.next ();
                        metadata.addEntity (ent);
                        // If it's a numerical entity, note which UTF8 block it's in
                        try {
                            if (ent.charAt (1) == '#') {
                                int entval = Integer.parseInt
                                        (ent.substring (2, ent.length() - 1));
                                utf8BM.markBlock(entval);
                            }
                        }
                        catch (Exception e) {
                            // Any exception means it's the wrong kind of entity
                        }
                    }
                }
            }
            // Check if all required attributes were found.
            List missingAtts = tagDesc.missingRequiredAttributes(attNames);
            if (!missingAtts.isEmpty ()) {
                info.setValid (false);
                Iterator miter = missingAtts.iterator ();
                while (miter.hasNext ()) {
                    String matt = (String) miter.next ();
                    info.setMessage (new ErrorMessage
                        ("Missing required attribute",
                         "Tag = " + name + ", Attribute = " + matt + 
                         ", Line = " + tag.getLine () +
                         ", Column = " + tag.getColumn ()));
                }
            }
        }
        tag.processElement (metadata);
        // If the content is empty, then a closing tag isn't permitted
        // (SGML handbook 7.3), so we don't push the open tag.
        // But if it's a temporary tag descriptor, we don't know
        // anything about it, so all guesses are wild.  Push it anyway.
        if (tagDesc.isTemp () || !tagDesc.isContentEmpty()) {
            tag.setElement (tagDesc);
            elementStack.push (tag);
        }
    }
    
    private void doCloseTag (JHCloseTag tag, RepInfo info)
    {
        String name = tag.getName ();
        // Dig down into the stack till we find an element which
        // matches this.  If there's none, report the document
        // as not well formed.  Also allow for the special case
        // of an empty body.  (An empty head is illegal.)
        int idx = elementStack.search (name);
        if (idx == -1) {
            info.setMessage (new ErrorMessage
                ("Close tag without matching open tag",
                 "Name = " + name + ", Line = " + tag.getLine () +
                    ", Column = " + tag.getColumn ()));
            info.setValid (false);
        }
        else {
            // Pop the stack down to the level of the matching tag.
            elementStack.popTo (idx);
        }

    }
    
    private void doErrorElement (JHErrorElement elem, RepInfo info)
    {
        elem.reportError (info);
    }

    private void doPCData (JHPCData elem, RepInfo info, HtmlMetadata metadata)
    {
        // Pop any elements that have optional close tags and do not
        // allow PCDATA.
        if (elementStack.isEmpty ()) {
            // PCData before any content.  This generates an implicit
            // html and body if they haven't already been seen.
            // It also means the document isn't valid, since the title
            // should precede any PCData.
            info.setMessage(new ErrorMessage 
                ("Document must have implicit or explicit HEAD element"));
            info.setValid (false);
            return;
        }
        HtmlTagDesc top = elementStack.top ().getElement ();
        if (top.isTemp() || top.allowsPCData ()) {
            // We assume that PCData is allowed with unknown tags.
            elem.processPCData (elementStack, metadata);
            return;
        }
        // If we can pop elements with optional closing tags till we find
        // one that allows PCData, we should do that.  But popping the
        // stack empty, as could happen if we're in a HEAD element, is
        // wrong.  So we always allow two elements to remain on the stack.
        while (!top.isCloseTagRequired ()) {
            if (elementStack.size () <= 2) {
                break;
            }
            elementStack.popp ();
            top = elementStack.top ().getElement ();
            if (top.allowsPCData ()) {
                elem.processPCData (elementStack, metadata);
                return;
            }
        }
        info.setMessage (new ErrorMessage ("PCData illegal in context",
             "Line = " + 
             elem.getLine () + ", Column = " +
             elem.getColumn () ));
        info.setValid (false);
    }

    /* Returns true if the element is permissible at this point.
     * This may pop elements off the stack and push implied tags.
     */
    private boolean checkElementContext (JHOpenTag elem, RepInfo info)
    {
        /* We are guaranteed there's something on the stack
         * unless the tag is "html", but Paranoia Is A Virtue */
        String name = elem.getName ();
        if (elementStack.isEmpty ()) {
            if ("html".equals (name)) {
                return true;
            }
            else {
                // This shouldn't happen
                return false;
            }
        }
        if (elementStack.excludesTag (name)) {
            return false;
        }
        JHOpenTag top = elementStack.top ();
        for (;;) {
            if (top.canGetMore () && top.allowsTag (name, this)) {
                top.countComponent ();
                return true;
            }
            if (!top.canAdvance ()) {
                /* Can't advance, can't stay put. */
                break;
            }
            top.advanceIndex ();
        }
        
        /* Kludgy special-case code for optional tags */
        HtmlTagDesc topElem = top.getElement ();
        if (topElem == htmlElement) {
            if (!elementStack.isHeadSeen () && headElement.allowsTag (name, this)) {
                JHOpenTag fakeTag = new JHOpenTag ("head");
                fakeTag.setElement(headElement);
                elementStack.push (fakeTag);
                return true;
            }
            if (!elementStack.isBodySeen () && 
                    bodyElement != null &&
                    bodyElement.allowsTag (name, this)) {
                JHOpenTag fakeTag = new JHOpenTag ("body");
                fakeTag.setElement (bodyElement);
                elementStack.push (fakeTag);
                return true;
            }
            return false;
        }
        else if (topElem == headElement) {
            if ("body".equals (name) || "frameset".equals (name)) {
                // Pop implied head end tag.  Is this too much
                // special-casing?
                elementStack.popp ();
                elementStack.push (elem);
                return  true;
            }
            else if (!elementStack.isBodySeen () && 
                    bodyElement != null &&
                    bodyElement.allowsTag (name, this)) {
                // Similar to above case except that the head is
                // implicitly terminated.
                elementStack.popp ();
                JHOpenTag fakeTag = new JHOpenTag ("body");
                fakeTag.setElement (bodyElement);
                elementStack.push (fakeTag);
                return true;
            }
            else {
                return false;
            }
        }
        
        // Pop elements till we find a valid context.  If
        // the enclosing element doesn't have an optional close
        // tag, report an error but pop it anyway.  But first
        // check if there even is a context to which we can pop things.
        boolean complained = false;
        boolean searchStack = false;
        if (elementStack.size () > 2) {
            Iterator iter = elementStack.iterator ();
            // Discard html element
            iter.next ();
            while (iter.hasNext ()) {
                JHOpenTag otag = (JHOpenTag) iter.next ();
                if (otag.allowsTag (name, this)) {
                    searchStack = true;
                    break;
                }
            }
        }
        if (searchStack) {
            // We've established we can pop down to something.
            while (elementStack.size () > 2) {
                if (!complained) {
                    top = elementStack.top ();
                    topElem = top.getElement ();
                    if (topElem.isCloseTagRequired()) {
                        info.setValid (false);
                        info.setMessage (new ErrorMessage
                           ("Tag illegal in context",
                            "Name = " + name + ", " + 
                            "Container = " + top.getName() + ", " +
                            "Line = " + elem.getLine() + ", Column = " +
                            elem.getColumn ()));
                    }
                }
                elementStack.popp ();
                top = elementStack.top ();
                //topElem = top.getElement ();
                if (top.allowsTag (name, this)) {
                    return true;
                }
                if (elementStack.isEmpty ()) {
                    break;
                }
            }
        }
        return false;
    }

    /** Adds all the Strings in an array to the end of a List. */
    protected static void addStringsToList (String[] names, List lst)
    {
        for (int i = 0; i < names.length; i++) {
            lst.add (names[i]);
        }
    }
    
    
    /** Adds an attribute to a List, with unrestricted values and
     *  type IMPLIED. */
    protected static void addSimpleAttribute (List atts, String name)
    {
        atts.add (new HtmlAttributeDesc (name));
    }
    
    /** Adds an attribute to a List, with unrestricted values and
     *  type REQUIRED. */
    protected static void addRequiredAttribute (List atts, String name)
    {
        atts.add (new HtmlAttributeDesc (name, null, HtmlAttributeDesc.REQUIRED));
    }
    
    /** Adds an attribute to a List, with the only permitted value being
     *  the name of the attribute.  This kind of attribute is normally
     *  represented in HTML without an explicit value; in fact, some (most?)
     *  readers won't permit an explicit value. */
    protected static void addSelfAttribute (List atts, String name)
    {
        atts.add (new HtmlAttributeDesc (name,
            new String[] { name },
            HtmlAttributeDesc.IMPLIED));
    }
    
    /** Removes excluded strings from a List. */
    protected static void removeStringsFromList (List lst, String [] strs)
    {
        for (int i = 0; i < strs.length; i++) {
            lst.remove(strs[i]);
        }
    }
    
    
    /** Pushes an element onto the element stack. */
    protected void pushElementStack (JHOpenTag tag)
    {
        elementStack.push (tag);
    }
    

}
