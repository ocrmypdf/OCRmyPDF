/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;

import java.util.*;

/**
 * This class describes the requirements of an HTML 3.2 document.
 *
 * @author Gary McGath
 *
 */
public class Html3_2DocDesc extends HtmlDocDesc {

    /* Static, private map of supported tags. 
     * For efficiency, we create a static Map
     * of supported tags just once, then assign that to stSupportedElements
     * in the constructor. */
    private static Map stSupportedElements;
    
    /* Static initializer.  A superclass is initialized before its
     * subclass, so we can count on the static initializer of HtmlDocDesc
     * to have run already.  
     * 
     * It's time to start thinking about how to factor this code.
     * Each element can be created separately, with the necessary
     * arguments passed for each one.  It would be a nice pattern if
     * all elements had the same calling sequence, but realistically
     * some are going to need extras such as special lists of names.
     * The element functions (which will all be static) should be here
     * if unique, or in the parent class if they can be used for more
     * than one version of HTML.  There should be a naming convention
     * for the functions in the parent class indicating which names
     * they can be used with.
     */
    static {
        stSupportedElements = new HashMap (280);
        String[] fontMarkup = new String[]
            { "tt", "i", "b", "u", "strike", "big", "small", "sub", "sup" };
        String[] phraseMarkup = new String[]
            { "em", "strong", "dfn", "code", "samp", "kbd", "var", "cite" };
        String[] specialMarkup = new String[]
            { "a", "img", "applet", "font", "basefont", "br", "script", "map" };
        String[] formMarkup = new String[]
            { "input", "select", "textarea" };
        String[] listMarkup = new String []
            { "ul", "ol",  "dir", "menu" };
        

        /* textContent lists all the content types which are permitted in
         * the markup elements.  For a first cut, strings signify the
         * name of the element which is permitted.  */
        List textContent = new ArrayList(35);
        addStringsToList (fontMarkup, textContent);
        addStringsToList (phraseMarkup, textContent);
        addStringsToList (specialMarkup, textContent);
        addStringsToList (formMarkup, textContent);
        textContent.add (HtmlSpecialToken.PCDATA);
        
        List blockContent = new ArrayList (20);
        addStringsToList (listMarkup, blockContent);
        String[] blockMisc = new String[]
            {"p", "pre", "dl", "div", "center",
              "blockquote", "form", "isindex", "hr", "table" };
        addStringsToList (blockMisc, blockContent);
        
        List flowContent = new ArrayList (30);
        flowContent.addAll (blockContent);
        flowContent.addAll (textContent);

        int i;
        String name;
        HtmlTagDesc td;
        
        /* Text elements */
        for (i = 0; i < fontMarkup.length; i++) {
            name = fontMarkup[i];
            td = new HtmlTagDesc (name, true, true, textContent, null);
            stSupportedElements.put (name, td);
        }
        
        /* Phrase elements. */
        for (i = 0; i < phraseMarkup.length; i++) {
            name = phraseMarkup[i];
            td = new HtmlTagDesc (name, true, true, textContent, null);
            stSupportedElements.put (name, td);
        }

        addFontElement (textContent);
        addBasefontElement ();
        addBrElement ();
        
        /* Content for the BODY element, also used for other elements */
        List bodyContent = new ArrayList (100);
        addStringsToList (headings, bodyContent);
        bodyContent.addAll (textContent);
        bodyContent.addAll (blockContent);
        bodyContent.add ("address");

        addBodyElement (bodyContent);
        addAddressElement (textContent);

        HtmlAttributeDesc halignAtt = 
            new HtmlAttributeDesc ("align", 
                new String[] { "left", "center", "right" },
                HtmlAttributeDesc.IMPLIED);
        /* Caution -- some elements' align attributes have a different
         * set of permitted values. Don't use halignAtt for these. */

        addDivElement (bodyContent,  halignAtt);
        addCenterElement (bodyContent);
        addAElement (textContent);
        addMapElement ();
        
        addAreaElement ();
        addLinkElement ();
        HtmlAttributeDesc ialignAtt = new HtmlAttributeDesc ("align",
                new String[] { "top", "middle", "bottom", "left", "right" },
                HtmlAttributeDesc.IMPLIED);
        addImgElement (ialignAtt);
        addAppletElement (ialignAtt, textContent);
        addParamElement ();
        addHrElement (halignAtt);
        addPElement (halignAtt, textContent);

        /* The heading (H1-H6) elements */
        List atts = new ArrayList (1);
        atts.add (halignAtt);
        for (i = 0; i < headings.length; i++) {
            name = headings[i];
            td = new HtmlTagDesc (name, true, true, textContent, atts);
            stSupportedElements.put (name, td);
        }

        addPreElement (textContent);
        addBlockquoteElement (bodyContent);
        addDlElement ();
        addDtElement (textContent);
        addDdElement (flowContent);

        List listContent = new ArrayList (1);
        listContent.add ("li");
        addOlElement (listContent);
        addUlElement (listContent);
        addDirElement (listContent);
        addMenuElement (listContent);
        addLiElement (flowContent);
        addFormElement (bodyContent);
        addInputElement (ialignAtt);
        addSelectElement ();
        addOptionElement ();
        addTableElement ();
        HtmlAttributeDesc valignAtt = 
            new HtmlAttributeDesc ("valign", 
                new String[] { "top", "middle", "bottom" },
                HtmlAttributeDesc.IMPLIED);
        addTrElement (halignAtt, valignAtt);

        List thtdAtts = new ArrayList (7);  // common attribute list for TH and TD
        addSelfAttribute (thtdAtts, "nowrap");
        addSimpleAttribute (thtdAtts, "rowspan");
        addSimpleAttribute (thtdAtts, "colspan");
        thtdAtts.add (halignAtt);
        thtdAtts.add (valignAtt);
        addSimpleAttribute (thtdAtts, "width");
        addSimpleAttribute (thtdAtts, "height");
        
        addThElement (bodyContent, thtdAtts);
        addTdElement (bodyContent, thtdAtts); 
        addCaptionElement (textContent, valignAtt);
        
        addHeadElement ();
        addTitleElement ();
        addIsindexElement ();
        addBaseElement ();
        addMetaElement ();
        addScriptElement ();
        addStyleElement ();
         
        /* The HTML element */
        name = "html";
        List htmlContent = new ArrayList (2);
        htmlContent.add ("head");
        htmlContent.add ("body");
        td = new HtmlTagDesc (name, false, false, htmlContent, null);
        td.setAttributes (new String[] {"version" });
        stSupportedElements.put (name, td);
    } 

    /** Constructor. */
    public Html3_2DocDesc ()
    {
        // publish stSupportedElements to superclass
        supportedElements = stSupportedElements;
        init ();
    }
    
    /** Static initializers for each element.  If elements are common to more
     *  than one HTML version, they should be moved into the superclass. 
     *  Different initializers may have different argument lists. */
    private static void addAddressElement (List textContent)
    {
        String name = "address";
        List addressContent = new ArrayList (36);
        addressContent.addAll (textContent);
        addressContent.add ("p");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, addressContent, null);
        stSupportedElements.put (name, td);
    }
    
    /* Initializer for "A" (anchor) element. */
    private static void addAElement (List textContent)
    {
        /* The Anchor (A) element */
        String name = "a";
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, textContent, null);
        td.setAttributes (new String[]
            {"name", "href", "rel", "rev", "title" });
        td.setExcludedContent(new String[] { "a" });
        stSupportedElements.put (name, td);
   
    }

    /* Initializer for APPLET element. */
    private static void addAppletElement 
        (HtmlAttributeDesc ialignAtt, List textContent)
    {
        String name = "applet";
        List atts = new ArrayList (9);
        addSimpleAttribute (atts, "codebase");
        atts.add (new HtmlAttributeDesc 
            ("code", null, HtmlAttributeDesc.REQUIRED));
        addSimpleAttribute (atts, "alt");
        addSimpleAttribute (atts, "name");
        atts.add (new HtmlAttributeDesc 
            ("width", null, HtmlAttributeDesc.REQUIRED));
        atts.add (new HtmlAttributeDesc 
            ("height", null, HtmlAttributeDesc.REQUIRED));
        atts.add (ialignAtt);
        addSimpleAttribute (atts, "hspace");
        addSimpleAttribute (atts, "vspace");
        List appletContent = new ArrayList (36);
        appletContent.addAll (textContent);
        appletContent.add ("param");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, appletContent, atts);
        stSupportedElements.put (name, td);
   
    }
    
    private static void addAreaElement ()
    {
        String name = "area";
        List atts = new ArrayList (5);
        atts.add (new HtmlAttributeDesc ("shape", 
            new String[] {"rect", "circle", "poly" },
            HtmlAttributeDesc.REQUIRED));
        addSimpleAttribute (atts, "coords");
        addSimpleAttribute (atts, "href");
        atts.add (new HtmlAttributeDesc ("nohref", 
            new String[] {"nohref"}, 
            HtmlAttributeDesc.IMPLIED));
        atts.add (new HtmlAttributeDesc ("alt",
            null,
            HtmlAttributeDesc.REQUIRED));
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    private static void addBaseElement ()
    {
        String name = "base";
        List atts = new ArrayList (1);
        addSimpleAttribute (atts, "href");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }
    private static void addBasefontElement ()
    {
        String name = "basefont";
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, null);
        td.setAttributes (new String[] {"size"});
        stSupportedElements.put (name, td);
    }
    
    private static void addBlockquoteElement (List bodyContent)
    {
        /* The BLOCKQUOTE element */
        String name = "blockquote";
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, bodyContent, null);
        stSupportedElements.put (name, td);
    }

    private static void addBodyElement (List bodyContent)
    {
        String name = "body";
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, bodyContent, null);
        td.setAttributes (new String []
            {"bgcolor", "text", "link", "vlink", "alink", "background" });
        stSupportedElements.put (name, td);
   
    }

    private static void addBrElement ()
    {
        String name = "br";
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, null);
        stSupportedElements.put (name, td);
    }
    
    private static void addCaptionElement (List textContent, 
                HtmlAttributeDesc valignAtt)
    {
        String name = "caption";
        List atts = new ArrayList (1);
        atts.add (valignAtt);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, textContent, atts);
        stSupportedElements.put (name, td);
    }
    private static void addCenterElement (List bodyContent)
    {
        String name = "center";
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, bodyContent, null);
        stSupportedElements.put (name, td);
    }

    private static void addDdElement (List flowContent)
    {
        String name = "dd";
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, flowContent, null);
        stSupportedElements.put (name, td);
    }

    private static void addDirElement (List listContent)
    {
        String name = "dir";
        List atts = new ArrayList (1);
        addSelfAttribute (atts, "compact");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, listContent, atts);
        stSupportedElements.put (name, td);
    }

    private static void addDivElement (List bodyContent, HtmlAttributeDesc halignAtt)
    {
        String name = "div";
        List atts = new ArrayList (1);
        atts.add (halignAtt);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, bodyContent, atts);
        stSupportedElements.put (name, td);
    }

    private static void addDlElement ()
    {
        String name = "dl";
        List dlContent = new ArrayList (2);
        addStringsToList(new String[] { "dt", "dd" }, dlContent);
        List atts = new ArrayList (1);
        addSelfAttribute(atts, "compact");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, dlContent, atts);
        stSupportedElements.put (name, td);
    }
    
    private static void addDtElement (List textContent)
    {
        String name = "dt";
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, textContent, null);
        stSupportedElements.put (name, td);
    }

    private static void addFontElement (List textContent)
    {
        String name = "font";
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, textContent, null);
        td.setAttributes (new String[] {"size", "color"});
        stSupportedElements.put (name, td);
   
    }

    private static void addFormElement (List bodyContent)
    {
        final String name = "form";
        List atts = new ArrayList (3);
        addSimpleAttribute (atts, "action");
        atts.add (new HtmlAttributeDesc ("method", null,
                HtmlAttributeDesc.OTHER));
        atts.add (new HtmlAttributeDesc ("enctype", null,
                HtmlAttributeDesc.OTHER));
        List formContent = new ArrayList (bodyContent.size ());
        formContent.addAll (bodyContent);
        removeStringsFromList (formContent, new String[] { "form" });
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, formContent, atts);
        stSupportedElements.put (name, td);
    }
    
    private static void addHeadElement ()
    {
        String name = "head";
        String[] headMisc = new String[] 
            {"script", "style", "meta", "link" };
        List headContent = new ArrayList (7);
        headContent.add ("title");
        headContent.add ("isindex");
        headContent.add ("base");
        HtmlTagDesc td = new HtmlTagDesc (name, false, false, headContent, null);
        stSupportedElements.put (name, td);
        /* Attributes TITLE (required), ISINDEX (optional), and BASE (optional)
         * are supposed to come in that order, ahead of anything else.
         * For the moment, just toss them in with the rest. */
        addStringsToList (headMisc, headContent);
    }

    private static void addHrElement (HtmlAttributeDesc halignAtt)
    {
        String name = "hr";
        List atts = new ArrayList (4);
        
        atts.add (halignAtt);
        addSelfAttribute (atts, "noshade");
        addSimpleAttribute (atts, "size");
        addSimpleAttribute (atts, "width");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    private static void addImgElement (HtmlAttributeDesc ialignAtt)
    {
        String name = "img";
        List atts = new ArrayList (10);
        addRequiredAttribute (atts, "src");
        addSimpleAttribute (atts, "alt");
        atts.add (ialignAtt);
        addSimpleAttribute (atts, "height");
        addSimpleAttribute (atts, "width");
        addSimpleAttribute (atts, "border");
        addSimpleAttribute (atts, "hspace");
        addSimpleAttribute (atts, "vspace");
        addSimpleAttribute (atts, "usemap");
        addSelfAttribute (atts, "ismap");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    private static void addInputElement (HtmlAttributeDesc ialignAtt)
    {
        final String name = "input";
        List atts = new ArrayList (8);
        atts.add (new HtmlAttributeDesc ("type", 
            new String[] {"text", "password", "checkbox", "radio", "submit", 
                        "reset", "file", "hidden", "image"},
            HtmlAttributeDesc.OTHER));
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "value");
        addSelfAttribute (atts, "checked");
        addSimpleAttribute (atts, "size");
        addSimpleAttribute (atts, "maxlength");
        addSimpleAttribute (atts, "src");
        atts.add (ialignAtt);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, null, atts);
        stSupportedElements.put (name, td);
    }
    
    private static void addIsindexElement ()
    {
        final String name = "isindex";
        List atts = new ArrayList (1);
        addSimpleAttribute (atts, "prompt");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    private static void addLiElement (List flowContent)
    {
        final String name = "li";
        List atts = new ArrayList (2);
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "value");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, flowContent, atts);
        stSupportedElements.put (name, td);   
    }

    private static void addLinkElement ()
    {
        final String name = "link";
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, null);
        td.setAttributes (new String []
            { "href", "rel", "rev", "title" });
        stSupportedElements.put (name, td);
   
    }

    private static void addMapElement ()
    {
        final String name = "map";
        List atts = new ArrayList (1);
        addSimpleAttribute (atts, "name");
        List mapContent = new ArrayList (1);
        mapContent.add ("area");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, mapContent, atts);
        stSupportedElements.put (name, td);
    }

    private static void addMenuElement (List listContent)
    {
        final String name = "menu";
        List atts = new ArrayList (1);
        addSelfAttribute (atts, "compact");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, listContent, atts);
        stSupportedElements.put (name, td);
    }

    private static void addMetaElement ()
    {
        final String name = "meta";
        List atts = new ArrayList (3);
        addSimpleAttribute (atts, "http-equiv");
        addSimpleAttribute (atts, "name");
        addRequiredAttribute (atts, "content");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    private static void addOlElement (List listContent)
    {
        final String name = "ol";
        List atts = new ArrayList (3);
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "start");
        addSelfAttribute (atts, "compact");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, listContent, atts);
        stSupportedElements.put (name, td);
    }

    private static void addOptionElement ()
    {
        final String name = "option";
        List atts = new ArrayList (2);
        addSelfAttribute (atts, "selected");
        addSimpleAttribute (atts,"value");
        List content = new ArrayList (1);
        content.add (HtmlSpecialToken.PCDATA);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }

    private static void addPElement (HtmlAttributeDesc halignAtt, List textContent)
    {
        final String name = "p";
        List atts = new ArrayList (1);
        atts.add (halignAtt);
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, textContent, atts);
        stSupportedElements.put (name, td);
    }

    private static void addParamElement ()
    {
        final String name = "param";
        List atts = new ArrayList (2);
        addRequiredAttribute (atts, "name");
        addSimpleAttribute (atts, "value");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }
    
    private static void addPreElement (List textContent)
    {
        final String name = "pre";
        List atts = new ArrayList (1);
        addSimpleAttribute(atts, "width");
        List preContent = new ArrayList (35);
        preContent.addAll(textContent);
        /* Take out excluded elements */
        removeStringsFromList (preContent,
            new String []
             {"img", "big", "small", "sub", "sup", "font"});
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, preContent, atts);
        stSupportedElements.put (name, td);   
    }

    private static void addScriptElement ()
    {
        /* In HTML 3.2, this is just a placeholder */
        final String name = "script";
        List content = new ArrayList (1);
        content.add (HtmlSpecialToken.PCDATA);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, null);
        stSupportedElements.put (name, td);
    }

    private static void addSelectElement ()
    {
        final String name = "select";
        List atts = new ArrayList (3);
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "size");
        addSelfAttribute (atts, "multiple");
        List content = new ArrayList (1);
        content.add ("option");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }

    private static void addStyleElement ()
    {
        /* In HTML 3.2, this is just a placeholder */
        final String name = "style";
        List content = new ArrayList (1);
        content.add (HtmlSpecialToken.PCDATA);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, null);
        stSupportedElements.put (name, td);
    }

    private static void addTableElement ()
    {
        final String name = "table";
        List atts = new ArrayList (5);
        atts.add (new HtmlAttributeDesc ("align",
            new String[] {"left", "center", "right"},
            HtmlAttributeDesc.IMPLIED));
        addSimpleAttribute (atts, "width");
        addSimpleAttribute (atts, "border");
        addSimpleAttribute (atts, "cellspacing");
        addSimpleAttribute (atts, "cellpadding");
        List content = new ArrayList (2);
        content.add ("caption");
        content.add ("tr");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }
    
    private static void addTextareaElement ()
    {
        final String name = "textarea";
        List atts = new ArrayList (3);
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "rows");
        addSimpleAttribute (atts, "cols");
        
        List content = new ArrayList (1);
        content.add (HtmlSpecialToken.PCDATA);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }
    
    private static void addTdElement (List bodyContent, List thtdAtts)
    {
        final String name = "td";
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, bodyContent, thtdAtts);
        stSupportedElements.put (name, td);
    }
    
    private static void addThElement (List bodyContent, List thtdAtts)
    {
        final String name = "th";
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, bodyContent, thtdAtts);
        stSupportedElements.put (name, td);
    }

    private static void addTitleElement ()
    {
        /* I'm confused by the DTD for this one.
         * Content consists only of PCDATA, but certain elements are
         * specifically excluded from its content.  This seems
         * redundant. */
        String name = "title";
        List pcdataContent = new ArrayList (1);
        pcdataContent.add (HtmlSpecialToken.PCDATA);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, pcdataContent, null);
        stSupportedElements.put (name, td);
    }

    private static void addTrElement 
        (HtmlAttributeDesc halignAtt, HtmlAttributeDesc valignAtt)
    {
        final String name = "tr";
        List atts = new ArrayList (2);
        atts.add (halignAtt);
        atts.add (valignAtt);
        List content = new ArrayList (2);
        content.add ("th");
        content.add ("td");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, content, atts);
        stSupportedElements.put (name, td);
    }

    private static void addUlElement (List listContent)
    {
        final String name = "ul";
        List atts = new ArrayList (2);
        addSimpleAttribute (atts, "type");
        addSelfAttribute (atts, "compact");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, listContent, atts);
        stSupportedElements.put (name, td);
    }


}
