package it.eng.jhove.module.odf;

import edu.harvard.hul.ois.jhove.ErrorMessage;
import edu.harvard.hul.ois.jhove.InfoMessage;
import edu.harvard.hul.ois.jhove.JhoveBase;
import edu.harvard.hul.ois.jhove.JhoveException;
import edu.harvard.hul.ois.jhove.Module;
import edu.harvard.hul.ois.jhove.ModuleBase;
import edu.harvard.hul.ois.jhove.OutputHandler;
import it.eng.jhove.Booolean;
import it.eng.jhove.RepInfo;
import it.eng.jhove.NullHandler;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.RandomAccessFile;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipException;
import java.util.zip.ZipFile;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.parsers.SAXParserFactory;
import org.xml.sax.SAXException;
import org.xml.sax.XMLReader;
import org.xml.sax.helpers.XMLReaderFactory;


/**
 * Class OdfModule A module for Jhove - JSTOR/Harvard Object
 * Validation Environment intended to recognize and validate ODF files
 * formatted according to the definition in "Open Document Format for
 * Office Applications (OpenDocument) v1.0"
 *
 *
 * Created: Fri Oct 20 15:59:25 2006
 *
 * @author <a href="mailto:saint@eng.it">Gian Uberto Lauri</a>
 * @version $Revision: 1.1 $
 */
public class OdfModule extends ModuleBase implements Module {


    /**
     * Crea una nuova istanza di <code>OdfModule</code> .
     *
     */
    public OdfModule() {
		super (NAME, RELEASE, DATE, FORMAT, COVERAGE, MIMETYPES, WELLFORMED,
			   VALIDITY, REPINFO, NOTE, RIGHTS, RANDOM);

    }

    /**
     * <code>init</code>
     *
     * @param string a <code>String</code>
     * @exception Exception
     */
    public final void init(final String string) throws Exception {

    }

    /**
     * <code>initParse</code> initializes the status of the parser.
     *
     */
    public final void initParse() {
		super.initParse();
    }

    /**
     * <code>parse</code>
     *
     * @param inputStream an <code>InputStream</code>
     * @param repInfo a <code>RepInfo</code>
     * @param n an <code>int</code>
     * @return an <code>int</code>
     * @exception IOException
     */
    public final int parse(final InputStream inputStream,
						   final RepInfo repInfo,
						   final int n) throws IOException {
		boolean alreadyNonPreservable=false;

		initParse();
		repInfo.setFormat(FORMAT[0]);
		repInfo.setModule (this);

		// First step. To work with ZIP classes you need a File, not a
		// stream. But you have a stream and this stream could arrive
		// from far far away... Solution, build yourself a nice
		// temporary file. Well'use quite some within this module...

		String tempdir = _je.getTempDirectory();
		File tempFile = null;
		if (tempdir == null) {
			tempFile = File.createTempFile("odfTemp", ".zip");

		}
		else {
			tempFile = File.createTempFile("odfTemp", ".zip",
										   new File(tempdir));

		}


		tempFile.deleteOnExit();

		FileOutputStream fous = new FileOutputStream(tempFile);

		byte b[] = new byte[1];

		while (inputStream.read(b) == 1) {
			fous.write(b);
		}

		fous.close();

		// ------------ Now let's begin
		ZipFile zipf=null;
//  Map componentFiles = new HashMap();

		FileInputStream fins = new FileInputStream(tempFile);

		boolean matchesP = doTheCheck((InputStream)fins);

		fins.close();

		if (!matchesP) {
			repInfo.setWellFormed(false);
			return(0);
		}

		try {

			zipf = new ZipFile(tempFile);

			ZipEntry mimeTypeZE = zipf.getEntry(MIMETYPE);

			if (mimeTypeZE == null) {
				repInfo.setValid(false);
				repInfo.setWellFormed(false);
				repInfo.setMessage(new ErrorMessage("Corrupted or invaild ODF Package: mimetype comonent is missing."));
				zipf.close();
				return 0;

			}

			ZipEntry manifestZE = zipf.getEntry(MANIFEST);
			if (manifestZE == null) {
				repInfo.setValid(false);
				repInfo.setWellFormed(false);
				repInfo.setMessage(new ErrorMessage("Corrupted or invaild ODF Package: manifest is missing."));
				zipf.close();
				return 0;

			}

			if (! setProfileMime(repInfo, zipf, mimeTypeZE)) {
				repInfo.setValid(false);
				repInfo.setWellFormed(true);
				repInfo.setMessage(new ErrorMessage("Invalid ODF Package, unexpected type: " + repInfo.getMimeType()));
				zipf.close();
				return 0;

			}
			repInfo.setSigMatch(_name);

			// Process Manifest
			String manifestFileName = dumpPart(manifestZE, zipf);
			JingDriver jd = new JingDriver();

			ByteArrayOutputStream errorStream = new ByteArrayOutputStream(1024);

			if (! jd.doValidation(getResource(SCHEMA_MANIFEST),
								  manifestFileName,
								  errorStream) ) {
				StringBuffer buf = new StringBuffer("Invalid ODF Package, manifest failed Relaxed NG validation: " );
				buf.append(errorStream.toString());
				repInfo.setValid(false);
				repInfo.setWellFormed(false);
				repInfo.setMessage(new ErrorMessage(buf.toString()));
			}

			XMLReader parser = getXmlParser();
			List elementList = new ArrayList();
			Booolean isEncrypted = new Booolean(false,"");
			ManifestHandler manifestHandler = new ManifestHandler(elementList,
																  isEncrypted);

			parser.setContentHandler (manifestHandler);

			/*
			 * Attempt to set schema awareness to avoid validation
			 * errors.
			 */
			try {
				parser.setFeature("http://xml.org/sax/features/validation",
								  false);
				parser.setFeature("http://xml.org/sax/features/namespace-prefixes",
								  true);
				parser.setProperty ("http://java.sun.com/xml/jaxp/" +
									"properties/schemaLanguage",
									"http://www.w3.org/2001/XMLSchema");
			}
			catch (SAXException e)
			{}

			try {
				parser.parse (manifestFileName);

			} catch (SAXException excptn) {
				repInfo.setValid(false);
				repInfo.setWellFormed(false);
				repInfo.setMessage(new ErrorMessage("Mmalformed manifest : " +
													excptn.getMessage()));
				zipf.close();
				return 0;

			}
			// Process components
			JhoveBase jhoveBase;
			try {

				jhoveBase = new JhoveBase();
				jhoveBase.init(_je.getConfigFile(),
							   _je.getSaxClass());

			} catch (JhoveException excptn) {

				repInfo.setValid(false);
				repInfo.setWellFormed(false);
				repInfo.setMessage(new ErrorMessage("Can't instance engine to analyze package parts. Cause : " +
													excptn.getMessage()));
				zipf.close();
				return 0;
			}

			for (Iterator iter = elementList.iterator(); iter.hasNext();) {
				ManifestEntry mnfe = (ManifestEntry) iter.next();

				/*
				 * If the size field is set then the data is
				 * encrypted, therefore we can't process it. If the
				 * type equals application/binary (not a IANA
				 * registered one!) then the data is skipped as
				 * application specific.
				 */
				if (mnfe.size != 0) {
					StringBuffer tmp = new StringBuffer("Warning, part ");
					tmp.append(mnfe.fullPath);
					tmp.append(" is encrypted, validation skipped.");
					repInfo.setMessage(new InfoMessage(tmp.toString()));
				}
				else if (mimeTypeMap.get(mnfe.mediaType) != null &&
						 ! mnfe.fullPath.equals(SKIP_ROOT)) {
					String subDocName;
					int idxof = mnfe.fullPath.indexOf("/");
					if (idxof<1) {

						subDocName= mnfe.fullPath.substring(0, idxof);

					}
					else {

						subDocName = mnfe.fullPath;

					}

					RepInfo subDoc = new RepInfo(subDocName);
					subDoc.setModule(this);
					subDoc.setFormat("ODF");
					subDoc.setProfile((String)mimeTypeMap.get(mnfe.mediaType));
					subDoc.setMimeType(mnfe.mediaType);
					subDoc.setValid(true);
					subDoc.setWellFormed(true);
					subDoc.setConsistent(true);
					repInfo.putEmbeddedRepInfo(subDocName, subDoc);
				}
				else if ( mnfe.mediaType.equals("") ||
						  mnfe.mediaType.equals(SKIP_TYPE) ||
						  mnfe.mediaType.startsWith(SKIP_APP)) {

				}
				else {
					ZipEntry part = zipf.getEntry(mnfe.fullPath);
					if (part==null) {
						// Manifest holds information of "virtual"
						// file entries, like Configurations2 (a directory)
						break;
					}

					// good for processing
					if (! part.isDirectory() &&
						part.getSize() > 0) {
						String partFileName = dumpPart(part, zipf);

						if (mnfe.mediaType.equals(XRNG_TYPE)) {
							if (! jd.doValidation(getResource(SCHEMA_OPENDOCUMENT),
												  partFileName,
												  errorStream)) {

								NullHandler nullHandler = new NullHandler();

								try {
									jhoveBase.dispatch(_app,
													   null,
													   null,
													   nullHandler,
													   null,
													   new String[] {partFileName});

									String partDocName;
									int idxofp = mnfe.fullPath.indexOf("/");
									if (idxofp<1) {

										partDocName = mnfe.fullPath;

									}
									else {

										partDocName= mnfe.fullPath.substring(0, idxofp-1);

									}

									RepInfo current = repInfo.getEmbeddedRepInfo(partDocName);
									if (current==null) {
										current=repInfo;
									}


									for (Iterator iter2 = nullHandler.getRepInfos(); iter2.hasNext();) {
										if ( ((RepInfo)iter2.next()).getWellFormed() != RepInfo.TRUE) {
											repInfo.setValid(false);
										}
									}

									if (repInfo.getValid() == RepInfo.TRUE && ! alreadyNonPreservable) {
										alreadyNonPreservable=true;
										repInfo.setProfile((String)mimeTypeMap.get(repInfo.getMimeType()));
									}
									else {
										StringBuffer buf = new StringBuffer("Invalid ODF Package, component ");
										buf.append(mnfe.fullPath);
										buf.append(" failed both Relaxed NG and normal XML validation therefore" );
										buf.append(" is not well formed.");
										repInfo.setValid(false);
										repInfo.setMessage(new ErrorMessage(buf.toString()));
									}



								} catch (Exception excptn) {
									StringBuffer buf = new StringBuffer("Invalid ODF Package, component ");
									buf.append(mnfe.fullPath);
									buf.append(" failed both Relaxed NG and normal XML validation " );
									buf.append(" due this error: ");
									buf.append(excptn.getMessage());
									repInfo.setValid(false);
									repInfo.setMessage(new ErrorMessage(buf.toString()));
								}
							}
							if (mnfe.fullPath.equals(META_FILE)) {
								MetaHandler metaHandler = new MetaHandler(repInfo);

								parser.setContentHandler (metaHandler);

								try {
									parser.parse (partFileName);

								} catch (SAXException excptn) {
									repInfo.setValid(false);
									repInfo.setMessage(new ErrorMessage("malformed meta.xml: " +
																		excptn.getMessage()));
								}

							}
						}
						else if (mnfe.mediaType.startsWith(IMG_TYPE)) {
							// For the files in the Picture directory
							NullHandler nullHandler = new NullHandler();

							try {
								jhoveBase.dispatch(_app,
												   null,
												   null,
												   nullHandler,
												   null,
												   new String[] {partFileName});

							} catch (Exception excptn) {
								StringBuffer xxx = new StringBuffer("File ");
								xxx.append(mnfe.fullPath);
								xxx.append("analysis failed. Cause: ");
								xxx.append(excptn.getMessage());
								repInfo.setMessage(new ErrorMessage(xxx.toString()));
							}


							String partDocName;
							int idxofp = mnfe.fullPath.indexOf("/");
							if (idxofp<10) {

								partDocName = mnfe.fullPath;

							}
							else {

								partDocName= mnfe.fullPath.substring(0, idxofp-1);

							}

							RepInfo current = repInfo.getEmbeddedRepInfo(partDocName);
							if (current==null) {
								current=repInfo;
							}


							for (Iterator iter2 = nullHandler.getRepInfos(); iter2.hasNext();) {
								current.addContainedRepInfo((RepInfo)iter2.next());
							}

						}



					} // End "good for processing"

				}

			} // end of the loop on the manifest.


		} catch (ZipException excptn) {
			repInfo.setValid(false);
			repInfo.setWellFormed(false);
			repInfo.setMessage(new ErrorMessage("Invalid or corrupted ODF Package: " +
												excptn.getMessage()));
		} catch (IOException excptn) {
			repInfo.setValid(false);
			repInfo.setWellFormed(false);
			repInfo.setMessage(new ErrorMessage("Error during ODF analysis: " +
												excptn.getMessage()));
		} catch (IllegalStateException excptn) {
			repInfo.setValid(false);
			repInfo.setWellFormed(false);
			repInfo.setMessage(new ErrorMessage("Unexpected end of stream: " +
												excptn.getMessage()));

		}
		catch (Throwable excptn) {
			// TODO remove after debugging
			excptn.printStackTrace();
		}
		finally {
			try {
				zipf.close();
			} catch (Throwable excptn) {

			}

		}

		// ------------ no other passes needed.
		return 0;
    }

    /**
     * <code>parse</code>
     *
     * @param randomAccessFile a <code>RandomAccessFile</code>
     * @param repInfo a <code>RepInfo</code>
     * @exception IOException
     */
    public final void parse(final RandomAccessFile randomAccessFile,
							final RepInfo repInfo) throws IOException {
		// Not used
    }

    /**
     * <code>param</code>
     *
     * @param string a <code>String</code>
     * @exception Exception
     */
    public final void param(final String string) throws Exception {

    }

    /**
     * <code>getDefaultParams</code>
     *
     * @return a <code>List</code>
     */
    public final List getDefaultParams() {
		return null;
    }

    /**
     * <code>checkSignatures</code> Checs for a valid Open Document Format file:
     * the string "PK" at position 0, the string "mimetype" at position 30.
     *
     * @param file a <code>File</code>
     * @param inputStream an <code>InputStream</code>
     * @param repInfo a <code>RepInfo</code>
     * @exception IOException
     */
    public final void checkSignatures(final File file,
									  final InputStream inputStream,
									  final RepInfo repInfo) throws IOException {

		// If we got this far, take note that the signature is OK.
		repInfo.setConsistent (doTheCheck(inputStream));


    }

    private final boolean doTheCheck(final InputStream inputStream)
		throws IOException{
		DataInputStream dis = getBufferedDataStream (inputStream, (_app != null) ?
													 _je.getBufferSize () : 0);
		boolean rv = true;
		for (int i = 0; i < 38; i++) {
			int c = readUnsignedByte(dis,this);
			rv &= ( header[i] == ' '  ||  header[i] == c );
		}
		return rv;
    }

    /**
     * <code>checkSignatures</code> Not used
     *
     * @param file a <code>File</code>
     * @param randomAccessFile a <code>RandomAccessFile</code>
     * @param repInfo a <code>RepInfo</code>
     * @exception IOException
     */
    public final void checkSignatures(final File file,
									  final RandomAccessFile randomAccessFile,
									  final RepInfo repInfo)
		throws IOException {
    }

    /**
     * <code>show</code>
     *
     * @param outputHandler an <code>OutputHandler</code>
     */
    public final void show(final OutputHandler outputHandler) {

    }


    /**
     * <code>setVerbosity</code>
     *
     * @param n an <code>int</code>
     */
    public final void setVerbosity(final int n) {

    }


    private final boolean setProfileMime(RepInfo repInfo, ZipFile zipf, ZipEntry zipnt)
		throws IOException, ZipException, IllegalStateException {
		ByteArrayOutputStream buf = new ByteArrayOutputStream();

		InputStream inst = new BufferedInputStream(zipf.getInputStream(zipnt));

		byte b[] = new byte[1];

		while (inst.read(b,0,1) != -1) {
			buf.write(b);
		}
		inst.close();

		repInfo.setMimeType(buf.toString());

		repInfo.setProfile((String)mimeTypeMap.get(repInfo.getMimeType()));

		return (repInfo.getProfile() != null);
    }


    private final String dumpPart(ZipEntry zent, ZipFile zfle)
		throws IOException, ZipException{
		String name = zent.getName().replace('/', '_');

		File fout = File.createTempFile(name, ".odfpart");
		String returnName = fout.getAbsolutePath();
		fout.deleteOnExit();

		OutputStream fous = new BufferedOutputStream( new FileOutputStream(fout));
		InputStream inst = new BufferedInputStream(zfle.getInputStream(zent));

		byte b[] = new byte[1];

		while (inst.read(b) != -1) {
			fous.write(b);
		}
		inst.close();
		fous.close();
		return returnName;
    }

    private final InputStream getResource(String resourceName) {
		StringBuffer buf = new StringBuffer(RESOURCES);
		buf.append(resourceName);
		return getClass().getResourceAsStream(buf.toString());
    }

    private XMLReader getXmlParser()
		throws IOException {
		String  saxClass   = JhoveBase.getSaxClassFromProperties ();
		XMLReader parser = null;
		try {
			if (saxClass == null) {
				/* Use Java 1.4 methods to create default parser.
				 */
				SAXParserFactory factory =
					SAXParserFactory.newInstance();
				factory.setNamespaceAware (true);
				parser = factory.newSAXParser ().getXMLReader ();
			}
			else {
				parser = XMLReaderFactory.createXMLReader (saxClass);
			}
		}
		catch (ParserConfigurationException e) {
			// If we can't get a SAX parser, we're stuck.
			throw new IOException ("SAX parser not found: " +
								   saxClass +": "+ e.getMessage());
		}
		catch (SAXException excptn) {
			throw new IOException ("SAX parser not found: " +
								   saxClass +": "+ excptn.getMessage());
		}

		return parser;
    }


    private static final String NAME = "ODF-engineering";
    private static final String RELEASE = "1.0";
    private static final int DATE[] = {2006, 9, 25};
    private static final String FORMAT[] = {
		"ODF",
		"Open Document Format for Office Applications 1.0"
    };
    private static final String MIMETYPES[] = {"application/vnd.oasis.opendocument.text",
											   "application/vnd.oasis.opendocument.text-template",
											   "application/vnd.oasis.opendocument.graphics",
											   "application/vnd.oasis.opendocument.graphics-template",
											   "application/vnd.oasis.opendocument.presentation",
											   "application/vnd.oasis.opendocument.presentation-template",
											   "application/vnd.oasis.opendocument.spreadsheet",
											   "application/vnd.oasis.opendocument.spreadsheet-template",
											   "application/vnd.oasis.opendocument.chart",
											   "application/vnd.oasis.opendocument.chart-template",
											   "application/vnd.oasis.opendocument.image",
											   "application/vnd.oasis.opendocument.image-template",
											   "application/vnd.oasis.opendocument.formula",
											   "application/vnd.oasis.opendocument.formula-template",
											   "application/vnd.oasis.opendocument.text-master",
											   "application/vnd.oasis.opendocument.text-web"};

    private static final String COVERAGE = "ODF";
    private static final String WELLFORMED = null;
    private static final String VALIDITY = null;
    private static final String REPINFO = null;
    private static final String NOTE = "Work in progress";
    private static final String RIGHTS =
		"Copyright 2006 Engineering Ingengeria Informatica S.p.a." +
		"Released under the GNU Lesser General Public License." +
		"Cryptoserver Library Copyright Engiweb Security, all rights reserved";
    private static final boolean RANDOM = false;

    private static final String PROFILES[] = {"Open Document Format Text Document",
											  "Open Document Format Text Document Template",
											  "Open Document Format Drawing",
											  "Open Document Format Drawing Template",
											  "Open Document Format Presentation Document",
											  "Open Document Format Presentation Document Template",
											  "Open Document Format Spreadsheet",
											  "Open Document Format Spreadsheet Template",
											  "Open Document Format Chart",
											  "Open Document Format Spreadsheet Chart Template",
											  "Open Document Format Image",
											  "Open Document Format Image Template",
											  "Open Document Format Mathematic Formula",
											  "Open Document Format Mathematic Formula Template",
											  "Open Document Format Global Text Document",
											  "Open Document Format HTML Text Document Template"};

    private static final Map mimeTypeMap = new HashMap();

    static {
		for (int i = 0; i < MIMETYPES.length; i++) {
			mimeTypeMap.put(MIMETYPES[i],PROFILES[i]);
		}
    }

    // Magic number
    private static final int header[] =new int[]{'P', 'K', ' ', ' ',
												 ' ', ' ', ' ', ' ',
												 ' ', ' ', ' ', ' ',
												 ' ', ' ', ' ', ' ',
												 ' ', ' ', ' ', ' ',
												 ' ', ' ', ' ', ' ',
												 ' ', ' ', ' ', ' ',
												 ' ', ' ', 'm', 'i',
												 'm', 'e', 't', 'y',
												 'p', 'e'};

    // These are the name of the mandatory ZipEntries in an Open
    // Document Format file.
    private final static String MIMETYPE="mimetype";
    private final static String MANIFEST="META-INF/manifest.xml";

    // Schemas for the Relax NG validation
    private final static String SCHEMA_MANIFEST = "OpenDocument-manifest-schema-v1.0-os.rng";
    private final static String SCHEMA_OPENDOCUMENT = "OpenDocument-schema-v1.0-os.rng";
    private final static String RESOURCES = "resources/";

    // Media types that need "special processing"
    private final static String
    SKIP_TYPE = "application/binary";   // this is a non standard media
    // type that has to be skipped

    private final static String
    XRNG_TYPE = "text/xml";     // all the xml file in a Open
    // Document file are to be
    // validated againist
    // SCHEMA_OPENDOCUMENT

    private final static String
    SKIP_APP = "application/";      // Application specific binary
    // stuff, i.e. substitutes for
    // a faster OLE display or

    private final static String
    IMG_TYPE = "image/";        // Images have their own
    // processing...

    // Special contents
    private final static String META_FILE = "meta.xml";
    private final static String SKIP_ROOT = "/";

}


// package access structure.
final class ManifestEntry {
    final String mediaType;
    final String fullPath;
    final int size;

    ManifestEntry(String mediaType, String fullPath, int size) {
		this.mediaType = mediaType;
		this.fullPath = fullPath;
		this.size = size;
    }

}
