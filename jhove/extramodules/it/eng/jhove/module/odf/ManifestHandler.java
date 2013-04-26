package it.eng.jhove.module.odf;

import org.xml.sax.helpers.DefaultHandler;
import org.xml.sax.Attributes;
import org.xml.sax.SAXException;
import java.util.List;
import it.eng.jhove.Booolean;

/**
 * Describe class ManifestHandler here.
 *
 *
 * Created: Mon Oct 23 08:45:53 2006
 *
 * @author <a href="mailto:saint@eng.it">Gian Uberto Lauri</a>
 * @version $Revision: 1.1 $
 */
public class ManifestHandler extends DefaultHandler {

    private Booolean isEncrypted;
    private List entries;

    /**
     * Crea una nuova istanza di <code>ManifestHandler</code> .
     *
     */
    public ManifestHandler(List entries,
			   Booolean isEncrypted) {
	this.entries = entries;
	this.isEncrypted = isEncrypted;
    }

    /**
     * <code>startElement</code>
     *
     * @param nameSpaceUri a <code>String</code>
     * @param localName a <code>String</code>
     * @param rawName a <code>String</code>
     * @param attributes an <code>Attributes</code>
     * @exception SAXException
     */
    public final void startElement(final String nameSpaceUri,
				   final String localName,
				   final String rawName,
				   final Attributes attributes)
	throws SAXException {

	if (rawName.equals(FILE_ENTRY)) {
	    String type="";
	    String path="";
	    int size=0;

	    for (int i = 0; i < attributes.getLength(); i++) {
		if (attributes.getQName(i).equals(ATTR_MEDIA)) {
		    type = attributes.getValue(i);
		}
		if (attributes.getQName(i).equals(ATTR_PATH)) {
		    path = attributes.getValue(i);
		}
		if (attributes.getQName(i).equals(ATTR_SIZE)) {
		    size = Integer.parseInt(attributes.getValue(i));
		}


	    }
	    ManifestEntry entry = new ManifestEntry(type, path, size);
	    entries.add(entry);
	}
	else if (rawName.equals(CRYP_ENTRT)) {
	    isEncrypted.setFlag(true);
	}

    }

    private final static String FILE_ENTRY = "manifest:file-entry";

    private final static String CRYP_ENTRT = "manifest:encryption-data";

    private final static String ATTR_MEDIA = "manifest:media-type";
    private final static String ATTR_PATH  = "manifest:full-path";
    private final static String ATTR_SIZE  = "manifest:size";
}
