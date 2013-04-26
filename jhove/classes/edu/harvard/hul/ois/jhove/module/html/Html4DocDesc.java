/**********************************************************************
 * Jhove - JSTOR/Harvard Object Validation Environment
 * Copyright 2004 by JSTOR and the President and Fellows of Harvard College
 **********************************************************************/

package edu.harvard.hul.ois.jhove.module.html;
import java.util.*;

/**
 * Abstract class for common features of HTML 4.0 and 4.01 
 * documents.
 *
 * @author Gary McGath
 *
 */
public abstract class Html4DocDesc extends HtmlDocDesc {

    /** Names of font-related elements. */
    protected static String[] fontMarkup;
    /** Names of phrase elements. */
    protected static String[] phraseMarkup;
    /** Names of special elements. */
    protected static String[] specialMarkup;
    /** Names of form elements. */
    protected static String[] formMarkup;
    /** Names of list elements. */
    protected static String[] listMarkup;

    /** List of block elements. */
    protected static List blockContent;
    /** List of flow elements. */
    protected static List flowContent;
    /** List of inline elements. */
    protected static List inlineContent;
    /** List consisting of the LI element. */
    protected static List listContent;
    /** List of elements for the BODY element and some other elements. */
    protected static List bodyContent;


    /** Core attributes list. */
    protected static List coreAttrs;
    /** Internationalization attributes list. */
    protected static List i18nAttrs;
    /** Event attributes list. */
    protected static List eventAttrs;
    /** Big attributes list.  The dtd calls this "attrs", but here
     * it's called lotsaAttrs to avoid confusion with common
     * local variables. */
    protected static List bigAttrs;
    /** Big attributes plus reserved attributes. */
    protected static List biggerAttrs;
    /** Attributes described as "reserved for future use." */
    protected static List reservedAttrs;

    /** Horizontal alignment attribute for cells. */
    protected static HtmlAttributeDesc halignAtt;
    /** Vertical alignment attribute for cells. */
    protected static HtmlAttributeDesc valignAtt;

    /** Attributes for TH and TD elements */
    protected static List thtdAtts;

    /** Initialization code.  This is called from the static initializer
     *  of our subclasses. */
    protected static void classInit4 (Map stSupportedElements)
    {
        phraseMarkup = new String[]
            { "em", "strong", "dfn", "code", "samp", "kbd", "var", "cite",
              "abbr", "acronym" };
        formMarkup = new String[]
            { "input", "select", "textarea", "label", "button" };

        /* Core attrs list, used for various elements */
        coreAttrs = new ArrayList (4);
        addSimpleAttribute (coreAttrs, "id");
        addSimpleAttribute (coreAttrs, "class");
        addSimpleAttribute (coreAttrs, "style");
        addSimpleAttribute (coreAttrs, "title");

        /* Internationalization attrs list */
        i18nAttrs = new ArrayList (2);
        addSimpleAttribute (i18nAttrs, "lang");
        i18nAttrs.add (new HtmlAttributeDesc ("id", 
            new String[] {"ltr", "rtl"},
            HtmlAttributeDesc.IMPLIED));

        /* Event attrs list */
        eventAttrs = new ArrayList (10);
        addSimpleAttribute (eventAttrs, "onclick");
        addSimpleAttribute (eventAttrs, "ondblclick");
        addSimpleAttribute (eventAttrs, "onmousedown");
        addSimpleAttribute (eventAttrs, "onmouseup");
        addSimpleAttribute (eventAttrs, "onmouseover");
        addSimpleAttribute (eventAttrs, "onmousemove");
        addSimpleAttribute (eventAttrs, "onmouseout");
        addSimpleAttribute (eventAttrs, "onkeypress");
        addSimpleAttribute (eventAttrs, "onkeydown");
        addSimpleAttribute (eventAttrs, "onkeyup");

        bigAttrs = new ArrayList 
            (coreAttrs.size() + i18nAttrs.size() + eventAttrs.size());
        bigAttrs.addAll (coreAttrs);
        bigAttrs.addAll (i18nAttrs);
        bigAttrs.addAll (eventAttrs);

        /* Attributes described as "reserved for future use." */
        reservedAttrs = new ArrayList (3);
        addSimpleAttribute (reservedAttrs, "datasrc");
        addSimpleAttribute (reservedAttrs, "datafld");
        addSimpleAttribute (reservedAttrs, "dataformatas");  // yes, spelled that way

        /* Big attributes plus reserved attributes. */
        biggerAttrs = new ArrayList (bigAttrs.size() + 3);
        biggerAttrs.addAll (bigAttrs);
        biggerAttrs.addAll (reservedAttrs);

        /* Reusable attributes for cell alignment. */
        halignAtt = new HtmlAttributeDesc
            ("align",
             new String [] {"left", "center", "right", "justify", "char"},
             HtmlAttributeDesc.IMPLIED);
        valignAtt = 
            new HtmlAttributeDesc ("valign", 
                new String[] { "top", "middle", "bottom", "baseline" },
                HtmlAttributeDesc.IMPLIED);
    }

    /** Static initializers for each element.  If elements are common to more
     *  than one HTML version, they should be moved into the superclass. 
     *  Different initializers may have different argument lists. */

    /** Defines the ADDRESS element. */
    protected static void addAddressElement (Map stSupportedElements)
    {
        String name = "address";
        List addressContent = new ArrayList (36);
        addressContent.addAll (inlineContent);
        addressContent.add ("p");
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, true, addressContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    /** Defines the BDO element. */
    protected static void addBdoElement (Map stSupportedElements)
    {
        String name = "bdo";
        List atts = new ArrayList (coreAttrs.size () + 2);
        atts.addAll (coreAttrs);
        addSimpleAttribute (atts, "lang");
        atts.add (new HtmlAttributeDesc ("dir",
            new String[] { "ltr", "rtl" }, HtmlAttributeDesc.REQUIRED));
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, inlineContent, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the BODY element. */
    protected static void addBodyElement (Map stSupportedElements)
    {
        /* bodyContent is different for transitional and strict, but
         * the code in this function is common to both. */
        String name = "body";
        List atts = new ArrayList (bigAttrs.size () + 2);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "onload");
        addSimpleAttribute (atts, "onunload");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, bodyContent, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the COL element. */
    protected static void addColElement 
        (Map stSupportedElements, List cellalignAttrs)
    {
        String name = "col";
        List atts = new ArrayList (bigAttrs.size () + 8);
        atts.addAll (bigAttrs);
        atts.addAll (cellalignAttrs);
        addSimpleAttribute (atts, "span");
        addSimpleAttribute (atts, "width");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the COLGROUP element. */
    protected static void addColgroupElement 
        (Map stSupportedElements, List cellalignAttrs)
    {
        String name = "colgroup";
        List content = new ArrayList (1);
        content.add ("col");
        List atts = new ArrayList (bigAttrs.size () + 8);
        atts.addAll (bigAttrs);
        atts.addAll (cellalignAttrs);
        addSimpleAttribute (atts, "span");
        addSimpleAttribute (atts, "width");
        
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, content, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the DD element. */
    protected static void addDdElement (Map stSupportedElements)
    {
        String name = "dd";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, false, flowContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    /** Defines the DEL element. */
    protected static void addDelElement (Map stSupportedElements)
    {
        final String name = "del";
        List atts = new ArrayList (bigAttrs.size () + 2);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "cite");
        addSimpleAttribute (atts, "datetime");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, flowContent, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the DT element. */
    protected static void addDtElement (Map stSupportedElements)
    {
        String name = "dt";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, false, inlineContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    /** Defines the FIELDSET element. */
    protected static void addFieldsetElement (Map stSupportedElements)
    {
        String name = "fieldset";
        List content = new ArrayList (flowContent.size () + 3);
        content.addAll (flowContent);
        content.add (HtmlSpecialToken.PCDATA);
        content.add ("legend");

        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, true, content, bigAttrs);
        stSupportedElements.put (name, td);
    }

    /** Defines the INS element. */
    protected static void addInsElement (Map stSupportedElements)
    {
        final String name = "ins";
        List atts = new ArrayList (bigAttrs.size () + 2);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "cite");
        addSimpleAttribute (atts, "datetime");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, flowContent, atts);
        stSupportedElements.put (name, td);
    }
    
    /** Defines the LABEL element. */
    protected static void addLabelElement 
        (Map stSupportedElements)
    {
        final String name = "label";
        List atts = new ArrayList (bigAttrs.size () + 4);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "for");
        addSimpleAttribute (atts, "accesskey");
        addSimpleAttribute (atts, "onfocus");
        addSimpleAttribute (atts, "onblur");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, inlineContent, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the MAP element.
     *  HTML 4.0 and 4.01 actually have different definitions here.  4.0
     *  allows block content or AREA elements, but not a mix of the two;
     *  4.01 allows a mix of the two.  The current version of the code
     *  doesn't allow that distinction to be expressed. (There are no
     *  differences between Strict and Transitional.) */
    protected static void addMapElement (Map stSupportedElements)
    {
        final String name = "map";
        List atts = new ArrayList (bigAttrs.size () + 1);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "name");
        List mapContent = new ArrayList (1);
        mapContent.addAll (blockContent);
        mapContent.add ("area");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, mapContent, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the META element. */
    protected static void addMetaElement (Map stSupportedElements)
    {
        final String name = "meta";
        List atts = new ArrayList (3);
        addSimpleAttribute (atts, "http-equiv");
        addSimpleAttribute (atts, "name");
        addRequiredAttribute (atts, "content");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the OPTGROUP (option group) element. */
    protected static void addOptgroupElement 
        (Map stSupportedElements)
    {
        final String name = "option";
        List atts = new ArrayList (bigAttrs.size () + 2);
        atts.addAll (bigAttrs);
        addSelfAttribute (atts, "selected");
        addSimpleAttribute (atts,"label");
        List content = new ArrayList (1);
        content.add ("option");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the OPTION element. */
    protected static void addOptionElement 
        (Map stSupportedElements)
    {
        final String name = "option";
        List atts = new ArrayList (bigAttrs.size () + 4);
        atts.addAll (bigAttrs);
        addSelfAttribute (atts, "selected");
        addSelfAttribute (atts, "disabled");
        addSimpleAttribute (atts, "label");
        addSimpleAttribute (atts, "value");
        List content = new ArrayList (1);
        content.add (HtmlSpecialToken.PCDATA);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the PARAM element. */
    protected static void addParamElement (Map stSupportedElements)
    {
        final String name = "param";
        List atts = new ArrayList (2);
        addRequiredAttribute (atts, "name");
        addSimpleAttribute (atts, "value");
        atts.add (new HtmlAttributeDesc ("valuetype",
                new String [] { "data", "ref", "object" },
                HtmlAttributeDesc.OTHER ));
        addSimpleAttribute (atts, "type");
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, null, atts);
        stSupportedElements.put (name, td);
    }
    
    /** Defines the Q (short quote) element. */
    protected static void addQElement (Map stSupportedElements)
    {
        final String name = "q";
        List atts = new ArrayList (bigAttrs.size () + 1);
        atts.addAll (bigAttrs);
        addSimpleAttribute (atts, "cite");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, inlineContent, atts);
        stSupportedElements.put (name, td);   
    }

    /** Defines the SELECT element. */
    protected static void addSelectElement (Map stSupportedElements)
    {
        final String name = "select";
        List atts = new ArrayList (biggerAttrs.size () + 10);
        atts.addAll (biggerAttrs);
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "size");
        addSelfAttribute (atts, "multiple");
        addSelfAttribute (atts, "disabled");
        addSimpleAttribute (atts, "tabindex");
        addSimpleAttribute (atts, "onfocus");
        addSimpleAttribute (atts, "onblur");
        addSimpleAttribute (atts, "onchange");
        List content = new ArrayList (2);
        content.add ("option");
        content.add ("optgroup");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }


    /** Defines the SPAN element. */
    protected static void addSpanElement (Map stSupportedElements)
    {
        final String name = "span";
        HtmlTagDesc td = 
            new HtmlTagDesc (name, true, true, inlineContent, biggerAttrs);
        stSupportedElements.put (name, td);
    }


    /** Defines the STYLE element. */
    protected static void addStyleElement (Map stSupportedElements)
    {
        final String name = "style";
        List content = new ArrayList (1);
        content.add (HtmlSpecialToken.PCDATA);
        List atts = new ArrayList (6);
        atts.addAll (i18nAttrs);
        addSimpleAttribute (atts, "type");
        addSimpleAttribute (atts, "media");
        addSimpleAttribute (atts, "title");
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the SUB (subscript) element. */
    protected static void addSubElement  (Map stSupportedElements)
    {
        final String name = "sub";
        HtmlTagDesc td = new HtmlTagDesc 
                (name, true, true, inlineContent, bigAttrs);
        stSupportedElements.put (name, td);
    }

    /** Defines the SUP (superscript) element. */
    protected static void addSupElement (Map stSupportedElements)
    {
        final String name = "sup";
        HtmlTagDesc td = new HtmlTagDesc 
                (name, true, true, inlineContent, bigAttrs);
        stSupportedElements.put (name, td);
    }


    /** Defines the TEXTAREA element. */
    protected static void addTextareaElement (Map stSupportedElements)
    {
        final String name = "textarea";
        List atts = new ArrayList (biggerAttrs.size () + 12);
        addSimpleAttribute (atts, "name");
        addSimpleAttribute (atts, "rows");
        addSimpleAttribute (atts, "cols");
        addSelfAttribute (atts, "disabled");
        addSelfAttribute (atts, "readonly");
        addSimpleAttribute (atts, "tabindex");
        addSimpleAttribute (atts, "accesskey");
        addSimpleAttribute (atts, "onfocus");
        addSimpleAttribute (atts, "onblur");
        addSimpleAttribute (atts, "onselect");
        addSimpleAttribute (atts, "onchange");
        
        List content = new ArrayList (1);
        content.add (HtmlSpecialToken.PCDATA);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, content, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the TBODY element. */
    protected static void addTbodyElement (Map stSupportedElements, List cellalignAttrs)
    {
        final String name = "tbody";
        List content = new ArrayList (1);
        content.add ("tr");
        List atts = new ArrayList (bigAttrs.size () + 8);
        atts.addAll (bigAttrs);
        atts.addAll (cellalignAttrs);
        HtmlTagDesc td = new HtmlTagDesc (name, false, false, content, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the TD element.  
     *  The strict and transitional versions have
     *  different attribute sets, but this is taken care of by the
     *  initialization of thtdAtts. */
    protected static void addTdElement (Map stSupportedElements)
    {
        final String name = "td";
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, flowContent, thtdAtts);
        stSupportedElements.put (name, td);
    }
    

    /** Defines the TFOOT element. */
    protected static void addTfootElement (Map stSupportedElements, List cellalignAttrs)
    {
        final String name = "tfoot";
        List content = new ArrayList (1);
        content.add ("tr");
        List atts = new ArrayList (bigAttrs.size () + 8);
        atts.addAll (bigAttrs);
        atts.addAll (cellalignAttrs);
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, content, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the TH element.
     *  The strict and transitional versions have
     *  different attribute sets, but this is taken care of by the
     *  initialization of thtdAtts. */
    protected static void addThElement (Map stSupportedElements)
    {
        final String name = "th";
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, flowContent, thtdAtts);
        stSupportedElements.put (name, td);
    }

    /** Defines the THEAD element. */
    protected static void addTheadElement (Map stSupportedElements, List cellalignAttrs)
    {
        final String name = "thead";
        List content = new ArrayList (1);
        content.add ("tr");
        List atts = new ArrayList (bigAttrs.size () + 8);
        atts.addAll (bigAttrs);
        atts.addAll (cellalignAttrs);
        HtmlTagDesc td = new HtmlTagDesc (name, true, false, content, atts);
        stSupportedElements.put (name, td);
    }

    /** Defines the TITLE element. */
    protected static void addTitleElement (Map stSupportedElements)
    {
        /* I'm confused by the DTD for this one.
         * Content consists only of PCDATA, but certain elements are
         * specifically excluded from its content.  This seems
         * redundant. */
        String name = "title";
        List pcdataContent = new ArrayList (1);
        pcdataContent.add (HtmlSpecialToken.PCDATA);
        HtmlTagDesc td = new HtmlTagDesc (name, true, true, pcdataContent, i18nAttrs);
        stSupportedElements.put (name, td);
    }

}
