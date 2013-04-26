/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import java.util.*;

/**
 * Abstract class for common features of HTML 4.0 and 4.01 strict
 * documents.  The differences between 4.0 and 4.01 are minor, so
 * most of the code is found here.
 *
 * @author Gary McGath
 *
 */
public abstract class Html4StrictDocDesc extends Html4DocDesc {


    /** Code which is called from the static initializer of the
     *  subclasses.  Note that this is called before the class
     *  is instantiated, and may reference only static fields
     *  and subroutines. */
    protected static void classInit4 (Map stSupportedElements)
    {
        Html4DocDesc.classInit4(stSupportedElements);

        String name;
        HtmlTagDesc td;

        fontMarkup = new String[]
            { "tt", "i", "b", "big", "small" };
        listMarkup = new String []
            { "ul", "ol" };
        specialMarkup = new String[]
            { "a", "img", "object", "br", "script", "map", 
              "q", "sub", "sup", "span", "bdo" };
        /* inlineContent lists all the content types which are permitted in
         * the markup elements.  For a first cut, strings signify the
         * name of the element which is permitted.  */
        inlineContent = new ArrayList(35);
        addStringsToList (fontMarkup, inlineContent);
        addStringsToList (phraseMarkup, inlineContent);
        addStringsToList (specialMarkup, inlineContent);
        addStringsToList (formMarkup, inlineContent);
        inlineContent.add (HtmlSpecialToken.PCDATA);

        blockContent = new ArrayList (20);
        addStringsToList (headings, blockContent);
        addStringsToList (listMarkup, blockContent);
        String[] blockMisc = new String[]
            {"p", "pre", "dl", "div", "noscript",
              "blockquote", "form", "hr", "table", "fieldset", "address" };
        addStringsToList (blockMisc, blockContent);
        
        flowContent = new ArrayList (30);
        flowContent.addAll (blockContent);
        flowContent.addAll (inlineContent);

        /* Content for the BODY element, also used for other elements */
        bodyContent = new ArrayList (blockContent.size () + 3);
        bodyContent.addAll (blockContent);
        bodyContent.add ("script");
        bodyContent.add ("ins");
        bodyContent.add ("del");

        listContent = new ArrayList (1);
        listContent.add ("li");

        /* Text elements */
        int i;
        for (i = 0; i < fontMarkup.length; i++) {
            name = fontMarkup[i];
            td = new HtmlTagDesc (name, true, true, inlineContent, bigAttrs);
            stSupportedElements.put (name, td);
        }
        
        /* Phrase elements. */
        for (i = 0; i < phraseMarkup.length; i++) {
            name = phraseMarkup[i];
            td = new HtmlTagDesc (name, true, true, inlineContent, bigAttrs);
            stSupportedElements.put (name, td);
        }

        thtdAtts = new ArrayList (bigAttrs.size() + 7);  // common attribute list for TH and TD
        thtdAtts.addAll (bigAttrs);
        addSimpleAttribute (thtdAtts, "abbr");
        addSimpleAttribute (thtdAtts, "axis");
        addSimpleAttribute (thtdAtts, "headers");
        addSimpleAttribute (thtdAtts, "scope");
        thtdAtts.add (halignAtt);
        thtdAtts.add (valignAtt);
        addSimpleAttribute (thtdAtts, "rowspan");
        addSimpleAttribute (thtdAtts, "colspan");

    }


    /** Static initializers for each element.  If elements are common to more
     *  than one HTML version, they should be moved into the superclass. 
     *  Different initializers may have different argument lists. */

    /** Defines the A element. */
    protected static void addAElement (Map stSupportedElements)
    {
        /* The Anchor (A) element */
        String name = "a";
        List atts = new ArrayList (bigAttrs.size () + 14);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "href");
        addSimpleAttribute (atts, "hreflang");
        addSimpleAttribute (atts, "rel");
        addSimpleAttribute (atts, "rev");
        addSimpleAttribute (atts, "accesskey");
        addSimpleAttribute (atts, "shape");
        addSimpleAttribute (atts, "rect");
        addSimpleAttribute (atts, "coords");
        addSimpleAttribute (atts, "tabindex");
        addSimpleAttribute (atts, "onfocus");
        addSimpleAttribute (atts, "onblur");
        List content = new ArrayList (inlineContent.size ());
        content.addAll (inlineContent);
        content.remove ("a");
        
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }


    /** Defines the ADDRESS element. */
    protected static void addAddressElement (Map stSupportedElements)
    {
        String name = "address";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, true, inlineContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    protected static void addAreaElement 
        (Map stSupportedElements, HtmlAttributeDesc shapeAtt)
    {
        String name = "area";
        List atts = new ArrayList (5);
        atts.add (shapeAtt);
        addSimpleAttribute (atts, "coords");
        addSimpleAttribute (atts, "href");
        atts.add (new HtmlAttributeDesc ("nohref", 
            new String[] {"nohref"}, 
            HtmlAttributeDesc.IMPLIED));
        atts.add (new HtmlAttributeDesc ("alt",
            null,
            HtmlAttributeDesc.REQUIRED));
        addSimpleAttribute (atts, "tabindex");
        addSimpleAttribute (atts, "accesskey");
        addSimpleAttribute (atts, "onfocus");
        addSimpleAttribute (atts, "onblur");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addBaseElement (Map stSupportedElements)
    {
        String name = "base";
        List atts = new ArrayList (1);
        addRequiredAttribute (atts, "href");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }
    
    protected static void addBlockquoteElement (Map stSupportedElements)
    {
        String name = "blockquote";
        List content = new ArrayList (blockContent.size () + 1);
        content.addAll (blockContent);
        content.add ("script");
        List atts = new ArrayList (bigAttrs.size () + 1);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "cite");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addBrElement (Map stSupportedElements, List coreAttrs)
    {
        String name = "br";
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, coreAttrs);
        stSupportedElements.put (name, td);
    }
    
    protected static void addButtonElement 
        (Map stSupportedElements)
    {
        String name = "button";
        List content = new ArrayList (formMarkup.length + 3);
        addStringsToList(formMarkup, content);
        content.add ("form");
        content.add ("fieldset");
        List atts = new ArrayList (biggerAttrs.size () + 8);
        atts.addAll (biggerAttrs);
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "value");
        atts.add (new HtmlAttributeDesc ("type",
            new String[] {"button", "submit" , "reset"},
            HtmlAttributeDesc.OTHER));
        addSelfAttribute (atts, "disabled");
        addSimpleAttribute (atts, "tabindex");
        addSimpleAttribute (atts, "accesskey");
        addSimpleAttribute (atts, "onfocus");
        addSimpleAttribute (atts, "onblur");
    }


    protected static void addCaptionElement 
        (Map stSupportedElements, List inlineContent, 
                HtmlAttributeDesc valignAtt)
    {
        String name = "caption";
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, inlineContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    protected static void addDivElement (Map stSupportedElements)
    {
        String name = "div";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, true, flowContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    protected static void addDlElement 
        (Map stSupportedElements)
    {
        String name = "dl";
        List dlContent = new ArrayList (2);
        addStringsToList(new String[] { "dt", "dd" }, dlContent);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, dlContent, bigAttrs);
        stSupportedElements.put (name, td);
    }
    
    protected static void addHeadElement (Map stSupportedElements)
    {
        String name = "head";
        String[] headMisc = new String[] 
            {"script", "style", "meta", "link" };
        List headContent = new ArrayList (7);
        headContent.add ("title");
        headContent.add ("base");
        headContent.add ("script");
        headContent.add ("style");
        headContent.add ("meta");
        headContent.add ("link");
        headContent.add ("object");
        HtmlTagDesc td = new HtmlTagDesc (name, false, false, headContent, null);
        stSupportedElements.put (name, td);
        /* Attributes TITLE (required), ISINDEX (optional), and BASE (optional)
         * are supposed to come in that order, ahead of anything else.
         * For the moment, just toss them in with the rest. */
        addStringsToList (headMisc, headContent);
    }

    protected static void addLegendElement (Map stSupportedElements)
    {
        final String name = "label";
        List atts = new ArrayList (bigAttrs.size () + 1);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "accesskey");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, inlineContent, atts);
        stSupportedElements.put (name, td);
    }
    
    protected static void addLiElement 
        (Map stSupportedElements)
    {
        final String name = "li";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, false, flowContent, bigAttrs);
        stSupportedElements.put (name, td);   
    }


    protected static void addLinkElement 
        (Map stSupportedElements)
    {
        final String name = "link";
        List atts = new ArrayList (bigAttrs.size () + 8);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "charset");
        addSimpleAttribute (atts, "href");
        addSimpleAttribute (atts, "hreflang");
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "rel");
        addSimpleAttribute (atts, "rev");
        addSimpleAttribute (atts, "media");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addNoscriptElement (Map stSupportedElements)
    {
        final String name = "noscript";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, false, blockContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    protected static void addObjectElement  (Map stSupportedElements)
    {
        final String name = "object";
        List atts = new ArrayList (biggerAttrs.size () + 13);
        atts.addAll (biggerAttrs);
        addSelfAttribute (atts, "declare");
        addSimpleAttribute (atts, "classid");
        addSimpleAttribute (atts, "codebase");
        addSimpleAttribute (atts, "data");
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "codetype");
        addSimpleAttribute (atts, "archive");
        addSimpleAttribute (atts, "standby");
        addSimpleAttribute (atts, "height");
        addSimpleAttribute (atts, "width");
        addSimpleAttribute (atts, "usemap");
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "tabindex");
    }


    protected static void addOlElement 
        (Map stSupportedElements)
    {
        final String name = "ol";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, true, listContent, bigAttrs);
        stSupportedElements.put (name, td);
    }


    protected static void addPElement (Map stSupportedElements)
    {
        final String name = "p";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, false, inlineContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    protected static void addPreElement (Map stSupportedElements)
    {
        final String name = "pre";
        List preContent = new ArrayList (inlineContent.size ());
        preContent.addAll(inlineContent);
        /* Take out excluded elements */
        removeStringsFromList (preContent,
            new String []
             {"img", "object", "big", "small", "sub", "sup"});
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, preContent, bigAttrs);
        stSupportedElements.put (name, td);   
    }

    protected static void addScriptElement  (Map stSupportedElements)
    {
        final String name = "script";
        List content = new ArrayList (1);
        content.add (HtmlSpecialToken.PCDATA);
        List atts = new ArrayList (6);
        addSimpleAttribute (atts, "charset");
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "src");
        addSelfAttribute (atts, "defer");
        addSimpleAttribute (atts, "event");
        addSimpleAttribute (atts, "for");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }

    protected static void addTableElement (Map stSupportedElements)
    {
        final String name = "table";
        List atts = new ArrayList (biggerAttrs.size () + 8);
        atts.addAll (biggerAttrs);
        addSimpleAttribute (atts, "summary");
        addSimpleAttribute (atts, "width");
        addSimpleAttribute (atts, "border");
        atts.add (new HtmlAttributeDesc ("frame",
            new String[] { "void", "above", "below", "hsides", 
                         "lhs", "rhs", "vsides", "box", "border" },
            HtmlAttributeDesc.IMPLIED));
        atts.add (new HtmlAttributeDesc ("rules",
            new String[] { "none", "groups", "rows", "cols", "all" },
            HtmlAttributeDesc.IMPLIED));
                           
        addSimpleAttribute (atts, "rules");
        addSimpleAttribute (atts, "cellspacing");
        addSimpleAttribute (atts, "cellpadding");
        addSimpleAttribute (atts, "datapagesize");
        List[] contentArray = new List[5];
        int[] contentSequence = new int[] 
                { HtmlTagDesc.SEQ0_1, 
                  HtmlTagDesc.SEQ0_MANY, 
                  HtmlTagDesc.SEQ0_1,
                  HtmlTagDesc.SEQ0_1,
                  HtmlTagDesc.SEQ1_MANY };
        List content = new ArrayList (1);
        content.add ("caption");
        contentArray[0] = content;
        
        content = new ArrayList(2);
        content.add ("col");
        content.add ("colgroup");
        contentArray[1] = content;
        
        content = new ArrayList (1);
        content.add ("thead");
        contentArray[2] = content;
        
        content = new ArrayList (1);
        content.add ("tfoot");
        contentArray[3] = content;
        
        content = new ArrayList (1);
        content.add ("tbody");
        contentArray[4] = content;
        
        HtmlTagDesc td = new HtmlTagDesc 
            (name, true, true, contentSequence, contentArray, atts);
         stSupportedElements.put (name, td);
    }

    protected static void addTrElement (Map stSupportedElements)
    {
        final String name = "tr";
        List atts = new ArrayList (bigAttrs.size() + 3);
        atts.addAll (bigAttrs);
        atts.add (halignAtt);
        atts.add (valignAtt);
        List content = new ArrayList (2);
        content.add ("th");
        content.add ("td");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, content, atts);
        td.addImplicitContainer((HtmlTagDesc) stSupportedElements.get ("tbody"));
        stSupportedElements.put (name, td);
    }

    protected static void addUlElement (Map stSupportedElements)
    {
        final String name = "ul";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, true, listContent, bigAttrs);
        stSupportedElements.put (name, td);
    }
}
