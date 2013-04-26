package it.eng.jhove.module.odf;

import com.thaiopensource.util.PropertyMapBuilder;
import com.thaiopensource.validate.SchemaReader;
import com.thaiopensource.validate.ValidateProperty;
import com.thaiopensource.validate.ValidationDriver;
import com.thaiopensource.validate.rng.RngProperty;
import com.thaiopensource.xml.sax.ErrorHandlerImpl;
import java.io.IOException;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import java.io.OutputStream;

import java.io.InputStream;


/**
 * JingDriver is a wrapper to use Jing as a library and not as an
 * application without changing jing own source code.
 *
 * Created: Fri Oct 20 14:22:14 2006
 *
 * @author <a href="mailto:saint@eng.it">Gian Uberto Lauri</a>
 * @version $Revision: 1.1 $
 */
public class JingDriver {

    /**
     * <code>doValidation</code> preform a relaxed ng validation using jing
     * code (-i option, since we had some barfing with Oasis nrg during
     * pre-tests)
     *
     * @param schema a <code>String</code> relaxed nrg schema against who
     * the file is to be validated.
     * @param xmlFileName a <code>String</code> xml file to validate
     * @param boust a <code>ByteArrayOutputStream</code> byte output stream
     * to collect jing barfing...
     * @return a <code>boolean</code> true if the file is valid, false
     * otherwise.
     */
    public boolean doValidation(InputStream schema,
				String xmlFileName,
				OutputStream boust) {
	ErrorHandlerImpl eh = new ErrorHandlerImpl(System.out);
	PropertyMapBuilder properties = new PropertyMapBuilder();
	ValidateProperty.ERROR_HANDLER.put(properties, eh);
	RngProperty.CHECK_ID_IDREF.add(properties);
	SchemaReader sr = null;

	// Simulate -i option, since without the program barfs on
	// Oasis Open Document nrg.
	properties.put(RngProperty.CHECK_ID_IDREF, null);

	boolean hadError = false;
	try {
	    ValidationDriver driver = new ValidationDriver(properties.toPropertyMap(), sr);
	    InputSource in = new InputSource(schema);
	    if (driver.loadSchema(in)) {

		if (!driver.validate(ValidationDriver.uriOrFileInputSource(xmlFileName)))
		    hadError = true;
	    }
	    else
		hadError = true;
	}
	catch (SAXException e) {
	    hadError = true;
	    eh.printException(e);
	}
	catch (IOException e) {
	    hadError = true;
	    eh.printException(e);
	}
	return ! hadError;
    }
}
