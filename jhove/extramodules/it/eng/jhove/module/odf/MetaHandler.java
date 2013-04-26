package it.eng.jhove.module.odf;

import org.xml.sax.helpers.DefaultHandler;
import edu.harvard.hul.ois.jhove.RepInfo;
import org.xml.sax.SAXException;
import org.xml.sax.Attributes;
import java.text.SimpleDateFormat;
import java.text.ParsePosition;
import java.util.Date;

/**
 * Describe class MetaHandler here.
 *
 *
 * Created: Mon Oct 23 13:25:46 2006
 *
 * @author <a href="mailto:saint@eng.it">Gian Uberto Lauri</a>
 * @version $Revision: 1.1 $
 */
public class MetaHandler extends DefaultHandler {
    protected RepInfo info;
    protected StringBuffer tagContent;
    protected boolean isInDate=false;
    protected boolean isInCreationDate=false;
    protected SimpleDateFormat sdf1=new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss");
    /**
     * Cretes a new instance of <code>MetaHandler</code> .
     *
     */
    public MetaHandler(RepInfo info) {
	this.info= info;
    }

    /**
     *  SAX parser callback method.
     */
    public void startElement (String namespaceURI, String localName,
			      String rawName, Attributes atts)
	throws SAXException
    {
        tagContent = new StringBuffer ();
	if (rawName.equals(TAG_DATE)) {
	    isInDate=true;
	}
	if (rawName.equals(TAG_CREATION)) {
	    isInCreationDate=true;
	}

    }

    /**
     *  SAX parser callback method.
     */
    public void characters (char [] ch, int start, int length)
	throws SAXException
    {
	tagContent.append (ch, start, length);

    }

    /**
     *  SAX parser callback method.
     */
    public void endElement (String namespaceURI, String localName,
			    String rawName)
	throws SAXException
    {
	if ( isInDate ) {
	    info.setLastModified(contentToDate());
	    isInDate=false;
	}
	if ( isInCreationDate ) {
	    info.setCreated(contentToDate());
	    isInCreationDate=false;
	}


    }

    private final Date contentToDate() {
	// Open document date format is yyyy-mm-ddThh:mm:ss
	return sdf1.parse(tagContent.toString(), new ParsePosition(0));
	
    }
    private final static String TAG_DATE="dc:date";
    private final static String TAG_CREATION="meta:creation-date";
}
