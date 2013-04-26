package it.eng.jhove.module.png;

import edu.harvard.hul.ois.jhove.Agent;
import edu.harvard.hul.ois.jhove.AgentType;
import edu.harvard.hul.ois.jhove.Checksummer;
import edu.harvard.hul.ois.jhove.Document;
import edu.harvard.hul.ois.jhove.DocumentType;
import edu.harvard.hul.ois.jhove.ErrorMessage;
import edu.harvard.hul.ois.jhove.ExternalSignature;
import edu.harvard.hul.ois.jhove.Identifier;
import edu.harvard.hul.ois.jhove.IdentifierType;
import edu.harvard.hul.ois.jhove.InfoMessage;
import edu.harvard.hul.ois.jhove.InternalSignature;
import edu.harvard.hul.ois.jhove.ModuleBase;
import edu.harvard.hul.ois.jhove.OutputHandler;
import edu.harvard.hul.ois.jhove.Property;
import edu.harvard.hul.ois.jhove.PropertyType;
import edu.harvard.hul.ois.jhove.RepInfo;
import edu.harvard.hul.ois.jhove.Signature;
import edu.harvard.hul.ois.jhove.SignatureType;
import edu.harvard.hul.ois.jhove.SignatureUseType;
import it.eng.jhove.*;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.RandomAccessFile;
import java.util.GregorianCalendar;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.zip.DataFormatException;
import java.util.zip.Inflater;
import java.util.zip.CRC32;

/*
 * This is a module for Jhove - JSTOR/Harvard Object Validation
 * Environment
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or (at
 * your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
 * USA
 *
 */

/**
 * Class <code>PngModule</code> A module for Jhove - JSTOR/Harvard
 * Object Validation Environment intended to recognize and validate
 * PNG files formatted according to the <a
 * href="http://www.w3.org/TR/PNG/">W3C Functional
 * specification. ISO/IEC 15948:2003 (E)</a>
 *
 * This implementation lacks the control of IDATA content against the
 * palette size
 *
 * For  some   reason,  it  needs  java.util.zip.CRC32   for  the  CRC
 * computation instead of using Jhove own.
 *
 * Created: Mon Sep 25 12:07:29 2006
 *
 * @author <a href="mailto:saint@eng.it">Gian Uberto Lauri</a>
 * @version $Revision: 1.1 $
 */

// TODO write the IDATA decompression algorithm to validate the
// contents against the palette size.
// This requires placing the IDATA data on a separate stream in
// order to rebuild the compressed stream. A temporary file is
// advisable since the data size could grow to invade the core of even
// the stronger application servers.
public class PngModule extends ModuleBase {

    public static final boolean PNG_ENDIANITY=true;
    /**
     * Crea una nuova istanza di <code>PngModule</code> .
     *
     */
    public PngModule() {
		super (NAME, RELEASE, DATE, FORMAT, COVERAGE, MIMETYPE, WELLFORMED,
			   VALIDITY, REPINFO, NOTE, RIGHTS, RANDOM);

		keywordList = new HashMap();

		keywordList.put("Title",
						new Booolean(false,"Title"));           //  Short (one line) title or caption for image
		keywordList.put("Author",
						new Booolean(false,"Author"));          //  Name of image's creator
		keywordList.put("Description",
						new Booolean(false,"Description"));     //  Description of image (possibly long)
		keywordList.put("Copyright",
						new Booolean(false,"Copyright"));       //  Copyright notice
		keywordList.put(CREATION_TIME_KEYWORD,
						new Booolean(false,CREATION_TIME_KEYWORD)); //  Time of original image creation
		keywordList.put("Software",
						new Booolean(false,"Software"));        //  Software used to create the image
		keywordList.put("Disclaimer",
						new Booolean(false,"Disclaimer"));      //  Legal disclaimer
		keywordList.put("Warning",
						new Booolean(false,"Warning"));         //  Warning of nature of content
		keywordList.put("Source",
						new Booolean(false,"Source"));          //  Device used to create the image
		keywordList.put("Comment",
						new Booolean(false,"Comment"));         //  Miscellaneous comment
    }
    // Implementation of edu.harvard.hul.ois.jhove.Module

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
		expectingIHDR = RepInfo.TRUE;
		expectingPLTE = RepInfo.UNDETERMINED;
		expectingIDAT = RepInfo.TRUE;
		expectingIEND = RepInfo.TRUE;
		expecting_cHRM = RepInfo.UNDETERMINED;
		expecting_gAMA = RepInfo.UNDETERMINED;
		expecting_iCCP = RepInfo.UNDETERMINED;
		expecting_sBIT = RepInfo.UNDETERMINED;
		expecting_sRGB = RepInfo.UNDETERMINED;
		expecting_tEXt = RepInfo.UNDETERMINED;
		expecting_zTXt = RepInfo.UNDETERMINED;
		expecting_iTXt = RepInfo.UNDETERMINED;
		expecting_bKGD = RepInfo.UNDETERMINED;
		expecting_hIST = RepInfo.UNDETERMINED;
		expecting_pHYs = RepInfo.UNDETERMINED;
		expecting_sPLT = RepInfo.UNDETERMINED;
		expecting_tIME = RepInfo.UNDETERMINED;
		expecting_tRNS = RepInfo.UNDETERMINED;

		paletteSize = 0;
		maxPaletteSize = 0;
		shortPalette = false;
		colorDepth = 0;

		for (Iterator i = keywordList.values().iterator(); i.hasNext(); ) {
			((Booolean) i.next()).setFlag(false);
		}

    }

    /**
     * <code>parse</code> Parse the content of a stream PNG image and
     * store the results in RepInfo
     *
     * @param inputStream an <code>InputStream</code> An InputStream,
     * positioned at its beginning, which is generated from the object
     * to be parsed. If multiple calls to <code>parse</code> are made
     * on the basis of a nonzero value being returned, a new
     * InputStream must be provided each time.
     * @param repInfo a <code>RepInfo</code> A fresh (on the first
     * call) RepInfo object which will be modified to reflect the
     * results of the parsing If multiple calls to parse are made on
     * the basis of a nonzero value being returned, the same RepInfo
     * object should be passed with each call.
     * @param n an <code>int</code> Must be 0 in first call to
     * <code>parse<code>. If <code>parse<code> returns a nonzero
     * value, it must be called again with parseIndex equal to that
     * return value.
     * @return an <code>int</code>
     * @exception IOException
     */
    public final int parse(final InputStream inputStream,
						   final RepInfo repInfo,
						   final int n) throws IOException {

		StringBuffer sigName = new StringBuffer();

		initParse();

		// I have to pass it to each method, WHY SHOULD I USE a class
		// instance ???
		DataInputStream dstream = getBufferedDataStream (inputStream,
														 _app != null ?
														 _je.getBufferSize () : 0);
		Agent agent = new Agent ("Harvard University Library",
								 AgentType.EDUCATIONAL);
		agent.setAddress ("Engineering Ingegneria Informatica S.p.a., " +
						  "Direzione Supporto e Servizi Tecnologici, " +
						  "Corso Stati Uniti 23/A, 25100 Padova.");
		agent.setTelephone ("+39 (49) 8283-411");
		agent.setEmail("saint@eng.it");
		_vendor = agent;

		Document doc = new Document ("PNG (Portable Network Graphics): a file format (pronounced \"ping\"), for a lossless, portable, compressed individual computer graphics image transmitted across the Internet. Indexed-colour, greyscale, and truecolour images are supported, with optional transparency",
									 DocumentType.REPORT);
		agent = new Agent ("W3 Consortium",
						   AgentType.STANDARD);
		agent.setAddress ("E.M.E.A.: ERCIM, 2004 route des Lucioles, BP 93, 06902 Sophia-Antipolis Cedex, France\nJapan & Korea: Keio University, 5322 Endo, Fujisawa, Kanagawa 252-8520 Japan\nAll other countries: MIT, 32 Vassar Street, Room 32-G515, Cambridge, MA 02139 USA");
		agent.setTelephone ("E.M.E.A. : +33.4.92.38.75.90\nJapan & Korea: +81.466.49.1170\nAll other countries: +1.617.253.2613");
		agent.setWeb ("http://www.w3.org/");
		doc.setAuthor (agent);
		doc.setDate ("2003-11-10");
		doc.setIdentifier (new Identifier ("http://www.w3.org/Graphics/GIF/spec-gif87.txt",
										   IdentifierType.URL));
		_specification.add (doc);

		Signature sig = new InternalSignature ("PNG", SignatureType.MAGIC,
											   SignatureUseType.MANDATORY, 0);
		_signature.add (sig);

		sig = new ExternalSignature (".png", SignatureType.EXTENSION,
									 SignatureUseType.OPTIONAL);
		_signature.add (sig);

		_bigEndian = false;
		// end of parsing prologue.
		if (! checkSignBytes(dstream,SIGNATURE)) {
			repInfo.setMessage(new ErrorMessage ("Bad PNG Header", 0));
			repInfo.setWellFormed (RepInfo.FALSE);
			return 0;
		}
		repInfo.setFormat("PNG");

		// If we got this far, take note that the signature is OK.
		repInfo.setSigMatch(_name);
		repInfo.setModule(this);
		// First chunk MUST be IHDR
		int declChunkLen = (int)(readUnsignedInt(dstream, PNG_ENDIANITY, this)
								 &0x7FFFFFFF);
		chcks.reset();

		int chunkSig = (int)(readUnsignedInt(dstream, PNG_ENDIANITY, this)&0x7FFFFFFF);
		chcks.update(int2byteArray(chunkSig));

		if (chunkSig != IHDR_HEAD_SIG ) {
			repInfo.setWellFormed(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("IHDR header not found where expected." ));
			return 0;
		}
		else {
			checkIHDR(dstream,repInfo,declChunkLen);

			if (somethingWrongP(repInfo))
				return 0;

			// not sure it's useful...
			expectingIHDR = RepInfo.FALSE;
		}

		// The IHDR is where it should be and it's fine, now let's
		// handle the other chunks.



		while (expectingIEND == RepInfo.TRUE) {
			declChunkLen = (int)(readUnsignedInt(dstream, PNG_ENDIANITY, this)
								 &0x7FFFFFFF);
			// Each chunk has its checsum;
			chcks.reset();

			chunkSig = (int)(readUnsignedInt(dstream, PNG_ENDIANITY, this)&0x7FFFFFFF);
			chcks.update(int2byteArray(chunkSig));

			switch (chunkSig) {

			case IHDR_HEAD_SIG:
				repInfo.setWellFormed(RepInfo.FALSE);
				repInfo.setMessage(new ErrorMessage("Duplicated IHDR chunk." ));
				break;

			case PLTE_HEAD_SIG:
				if (expectingPLTE == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Unexpected or duplicated PLTE chunk." ));

					break;
				}
				checkPLTE(dstream,repInfo,declChunkLen);
				expectingPLTE = RepInfo.FALSE;

				break;

			case IDAT_HEAD_SIG:
				if (expectingPLTE == RepInfo.TRUE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Expected PLTE chunk not found." ));

					break;
				}

				checkChunk(dstream, repInfo, declChunkLen,"IDAT");
				expectingIDAT = RepInfo.FALSE;
				break;

			case IEND_HEAD_SIG:
				if (expectingPLTE == RepInfo.TRUE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Expected PLTE chunk not found." ));

					break;
				}
				if (expectingIDAT == RepInfo.TRUE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("No IDAT chunk found." ));

					break;
				}
				checkChunk(dstream, repInfo, declChunkLen,"IEND");
				expectingIEND = RepInfo.FALSE;
				break;

			case cHRM_HEAD_SIG:
				if (expectingPLTE == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("cHRM chunk found after PLTE one." ));

					break;
				}
				if (expectingIDAT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("cHRM chunk found after IDAT ones." ));


					break;
				}
				if (expecting_cHRM == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Extra cHRM chunk found." ));


					break;
				}

				checkChunk(dstream, repInfo, declChunkLen,"cHRM");
				expecting_cHRM = RepInfo.FALSE;

				break;

			case gAMA_HEAD_SIG:
				if (expectingPLTE == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("gAMA chunk found after PLTE one." ));

					break;
				}
				if (expectingIDAT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("gAMA chunk found after IDAT ones." ));

					break;
				}
				if (expecting_gAMA == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Extra gAMA chunk found." ));

					break;
				}

				checkChunk(dstream, repInfo, declChunkLen,"gAMA");
				expecting_gAMA = RepInfo.FALSE;

				break;

			case iCCP_HEAD_SIG:

				if (expectingPLTE == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("iCCP chunk found after PLTE one." ));

					break;
				}
				if (expectingIDAT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("iCCP chunk found after IDAT ones." ));

					break;
				}
				if (expecting_iCCP == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Extra iCCP chunk found." ));

					break;
				}
				if (expecting_sRGB == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("iCCP chunk with sRGB chunk found." ));

					break;
				}

				checkChunk(dstream, repInfo, declChunkLen,"iCCP");
				expecting_iCCP = RepInfo.FALSE;
				expecting_sRGB = RepInfo.FALSE;
				break;

			case sBIT_HEAD_SIG:
				if (expectingPLTE == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("sBIT chunk found after PLTE one." ));

					break;
				}
				if (expectingIDAT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("sBIT chunk found after IDAT ones." ));

					break;
				}
				if (expecting_sBIT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Extra sBIT chunk found." ));

					break;
				}

				checkChunk(dstream, repInfo, declChunkLen,"sBIT");
				expecting_sBIT = RepInfo.FALSE;


				break;

			case sRGB_HEAD_SIG:
				if (expectingPLTE == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("sRGB chunk found after PLTE one." ));

					break;
				}
				if (expectingIDAT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("sRGB chunk found after IDAT ones." ));

					break;
				}
				if (expecting_sRGB == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Extra sRGB chunk found." ));

					break;
				}
				if (expecting_iCCP == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("iCPP chunk after sRGB chunk found." ));

					break;
				}

				checkChunk(dstream, repInfo, declChunkLen,"sRGB");
				expecting_sRGB = RepInfo.FALSE;
				expecting_iCCP = RepInfo.FALSE;

				break;

			case tEXt_HEAD_SIG:

				checkChunk(dstream, repInfo, declChunkLen,"tEXT");
				break;

			case zTXt_HEAD_SIG:

				checkChunk(dstream, repInfo, declChunkLen,"zEXT");
				break;

			case iTXt_HEAD_SIG:

				checkChunk(dstream, repInfo, declChunkLen,"iEXT");
				break;

			case bKGD_HEAD_SIG:

				if (expectingPLTE == RepInfo.TRUE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("gAMA chunk found before PLTE one." ));


					break;
				}
				if (expectingIDAT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("gAMA chunk found after IDAT ones." ));

					break;
				}
				if (expecting_gAMA == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Extra gAMA chunk found." ));

					break;
				}

				checkChunk(dstream, repInfo, declChunkLen,"bKGRD");
				expecting_gAMA = RepInfo.FALSE;
				break;

			case hIST_HEAD_SIG:

				if (expectingPLTE == RepInfo.TRUE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("hIST chunk found before PLTE one." ));

					break;
				}
				if (expectingIDAT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("hIST chunk found after IDAT ones." ));

					break;
				}
				if (expecting_hIST == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Extra hIST chunk found." ));

					break;
				}

				checkChunk(dstream, repInfo, declChunkLen,"hIST");
				expecting_hIST = RepInfo.FALSE;
				break;

			case tRNS_HEAD_SIG:

				if (expectingPLTE == RepInfo.TRUE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("tRNS chunk found before PLTE one." ));

					break;
				}
				if (expectingIDAT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("tRNS chunk found after IDAT ones." ));

					break;
				}
				if (expecting_tRNS == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Extra tRNS chunk found." ));

					break;
				}

				checkChunk(dstream, repInfo, declChunkLen,"tRNS");
				expecting_tRNS = RepInfo.FALSE;
				break;

			case pHYs_HEAD_SIG:

				if (expectingIDAT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("pHYs chunk found after IDAT ones." ));

					break;
				}
				if (expecting_pHYs == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Extra pHYs chunk found." ));

					break;
				}

				checkChunk(dstream, repInfo, declChunkLen,"pHYs");
				expecting_pHYs = RepInfo.FALSE;
				break;

			case sPLT_HEAD_SIG:

				if (expectingIDAT == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("sPLT chunk found after IDAT ones." ));

					break;
				}
				checkChunk(dstream, repInfo, declChunkLen,"sPLT");

				break;

			case tIME_HEAD_SIG:
				if (expecting_tIME == RepInfo.FALSE) {
					repInfo.setWellFormed(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Extra tIME chunk found." ));

					break;
				}

				checktIME(dstream, repInfo, declChunkLen);
				expecting_tIME = RepInfo.FALSE;
				break;

			default:
				// Some strong choices. Reject undefined non ancillary chunks
				if (( chunkSig & ( PROP_ANCILLARY  ) ) == 0) {
					repInfo.setValid(RepInfo.FALSE);
					repInfo.setMessage(new ErrorMessage("Unknown non ancillary chunk found. Datastream not interpretable!" ));

					break;

				}

				sigName.delete(0, sigName.length());

				sigName.append((char)((chunkSig & 0x7F000000) >>> 24) );
				sigName.append((char)((chunkSig & 0x007F0000) >>> 16) );
				sigName.append((char)((chunkSig & 0x00007F00) >>> 8) );
				sigName.append((char)((chunkSig & 0x0000007F)) );
				// a private chunk, check the CRC
				checkChunk(dstream, repInfo, declChunkLen, sigName.toString());
				break;
			}


			if (somethingWrongP(repInfo))
				return 0;

		}


		// epilogue
		if (expectingPLTE == RepInfo.TRUE) {
			repInfo.setWellFormed(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("PLTE chunk not found (but was expected)." ));

		}


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
		// Not implemented.
    }

    /**
     * <code>applyDefaultParams</code>
     *
     * @exception Exception
     */
    public final void applyDefaultParams() throws Exception {

    }

    /**
     * <code>resetParams</code>
     *
     * @exception Exception
     */
    public final void resetParams() throws Exception {

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
     * <code>setVerbosity</code>
     *
     * @param n an <code>int</code>
     */
    public final void setVerbosity(final int n) {

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
     * <code>checkSignatures</code>
     *
     * @param file a <code>File</code>
     * @param inputStream an <code>InputStream</code>
     * @param repInfo a <code>RepInfo</code>
     * @exception IOException
     */
    public final void checkSignatures(final File file,
									  final InputStream inputStream,
									  final RepInfo repInfo) throws IOException {
		DataInputStream dis = getBufferedDataStream (inputStream, _app != null ?
													 _je.getBufferSize () : 0);
		if (! checkSignBytes(dis,SIGNATURE)) {
			repInfo.setConsistent (false);
			return;
		}
    }

    /**
     * <code>checkSignatures</code> Not used
     *
     * @param file a <code>File</code>
     * @param stream a <code>InputStream</code>
     * @param repInfo a <code>RepInfo</code>
     * @exception IOException
     */
    public final void checkSignatures(final File file,
									  final RandomAccessFile stream,
									  final RepInfo repInfo)
		throws IOException {
		// Not used.
    }

    /**
     * <code>show</code>
     *
     * @param outputHandler an <code>OutputHandler</code>
     */
    public final void show(final OutputHandler outputHandler) {

    }


    private final boolean checkSignBytes(final DataInputStream inputStream,
										 final int sigBytes[])
		throws IOException {
		int max = sigBytes.length;
		int c;
		boolean rv = true;

		for (int i = 0; i < max; i++) {
			c = readUnsignedByte(inputStream,this);
			rv &= (c == sigBytes[i]);
		}

		return rv;
    }


    private final void checkIHDR(final DataInputStream inputStream,
								 final RepInfo repInfo,
								 final int declChunkLen)
		throws IOException {

		// W3C recommendations states that height and width are integers that
		// range from 0 to 2^31
		int tmp = (int)(readUnsignedInt(inputStream, PNG_ENDIANITY, this)&0xFFFFFFFF);
		chcks.update(int2byteArray(tmp));

		if (tmp == 0) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("Illegal 0 value for height." ));

		}

		tmp = (int)(readUnsignedInt(inputStream, PNG_ENDIANITY, this)&0xFFFFFFFF);
		chcks.update(int2byteArray(tmp));

		if (tmp == 0) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("Illegal 0 value for width." ));

		}

		tmp = readUnsignedByte(inputStream, this);
		chcks.update((byte)tmp);

		int colorType = readUnsignedByte(inputStream, this);
		chcks.update((byte)colorType);

		switch (colorType) {
		case 0:
			if (tmp != 1 &&
				tmp != 2 &&
				tmp != 4 &&
				tmp != 8 &&
				tmp != 16) {
				repInfo.setValid(RepInfo.FALSE);
				repInfo.setMessage(new ErrorMessage("In IHDR, illegal value for bit depth for colour type " +

													colorType + ": " +tmp ));

			}
			repInfo.setProfile("PNG GrayScale");

			expectingPLTE=RepInfo.FALSE;
		case 3:
			if (tmp != 1 &&
				tmp != 2 &&
				tmp != 4 &&
				tmp != 8 ) {
				repInfo.setValid(RepInfo.FALSE);
				repInfo.setMessage(new ErrorMessage("In IHDR, illegal value for bit depth for colour type " +
													colorType + ": " +tmp ));

			}
			// We need to find a palette!
			expectingPLTE = RepInfo.TRUE;
			colorDepth = tmp;
			maxPaletteSize = 1 << tmp ;
			repInfo.setProfile("PNG Indexed");

			break;
		case 4:
			expectingPLTE=RepInfo.FALSE;
			if (tmp != 8 &&
				tmp != 16) {
				repInfo.setValid(RepInfo.FALSE);
				repInfo.setMessage(new ErrorMessage("In IHDR, valore illegale per la profondita` dei bit per il colour type " +
													colorType + ": " +tmp ));

			}

			repInfo.setProfile("PNG GrayScale with Alpha");
			break;
		case 6:
			expectingPLTE=RepInfo.FALSE;
			expecting_tRNS=RepInfo.FALSE;
			if (tmp != 8 &&
				tmp != 16) {
				repInfo.setValid(RepInfo.FALSE);
				repInfo.setMessage(new ErrorMessage("In IHDR, valore illegale per la profondita` dei bit per il colour type " +
													colorType + ": " +tmp ));

			}
			repInfo.setProfile("PNG Truecolor with Alpha");
			break;
		case 2:
			expectingPLTE=RepInfo.FALSE;
			expecting_tRNS=RepInfo.FALSE;
			if (tmp != 8 &&
				tmp != 16) {
				repInfo.setValid(RepInfo.FALSE);
				repInfo.setMessage(new ErrorMessage("In IHDR, valore illegale per la profondita` dei bit per il colour type " +
													colorType + ": " +tmp ));

			}

			repInfo.setProfile("PNG Truecolor");
			break;
		default:
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("In IHDR, valore illegale per il colour type (" +
												colorType +")"));

			break;
		}

		// Compression
		tmp = readUnsignedByte(inputStream, this);
		chcks.update((byte)tmp);

		if (tmp!=0) {
			repInfo.setMessage(new InfoMessage("Attenzione, tipo di compressine " +
											   tmp + " not conforme alla raccommandazione del W3C."));
		}


		// filtering
		tmp = readUnsignedByte(inputStream, this);
		chcks.update((byte)tmp);

		if (tmp!=0) {
			repInfo.setMessage(new InfoMessage("Attenzione, tipo di filtro " +
											   tmp + " no ancora standardizzato dal W3C."));
		}

		// interlace

		tmp = readUnsignedByte(inputStream, this);
		chcks.update((byte)tmp);

		if (tmp!=0 && tmp!=1) {
			repInfo.setMessage(new InfoMessage("Attenzione, tipo di interlacciamento " +
											   tmp + " no ancora standardizzato dal W3C."));
		}

		long crc32 = readUnsignedInt(inputStream, PNG_ENDIANITY, this);

		if (crc32 != chcks.getValue()) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("Errore CRC nel chunk IHDR" ));
		}

    }

    private final void checkPLTE(final DataInputStream inputStream,
								 final RepInfo repInfo,
								 final int declChunkLen)
		throws IOException {

		if ((declChunkLen % 3) != 0) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("Lunghezza PLTE non valida." ));
		}


		// Scan the palette
		paletteSize=0;

		for (int i = 0; i < declChunkLen; i++) {
			int tmp = readUnsignedByte(inputStream, this);
			chcks.update((byte)tmp);

			tmp = readUnsignedByte(inputStream, this);
			chcks.update((byte)tmp);

			tmp = readUnsignedByte(inputStream, this);
			chcks.update((byte)tmp);

			paletteSize++;

		}

		if (paletteSize > maxPaletteSize) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("Too many palette items in PLTE chunk" ));


		}
		shortPalette = (paletteSize < maxPaletteSize);
		long crc32 = readUnsignedInt(inputStream, PNG_ENDIANITY, this);

		if (crc32 != chcks.getValue()) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("CRC Error in PLTE chunk" ));

		}
    }

    private final void checktIME(final DataInputStream inputStream,
								 final RepInfo repInfo,
								 final int declChunkLen)
		throws IOException {
		int yhrHigh = readUnsignedByte(inputStream, this);
		chcks.update((byte)yhrHigh);

		int yhrLow = readUnsignedByte(inputStream, this);
		chcks.update((byte)yhrLow);

		int month = readUnsignedByte(inputStream, this);
		chcks.update((byte)month);

		if (month < 1 || month > 12) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("Illegal month value in tIME chunk"));

		}

		int day = readUnsignedByte(inputStream, this);
		chcks.update((byte)day);

		if (day < 1 || day > 31) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("Illegal day value in tIME chunk"));

		}

		int hour = readUnsignedByte(inputStream, this);
		chcks.update((byte)hour);

		if (hour < 0 || hour > 23) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("Illegal hour value in tIME chunk"));

		}

		int minute = readUnsignedByte(inputStream, this);
		chcks.update((byte)minute);

		if (minute < 0 || minute > 59) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("Illegal minute value in tIME chunk"));

		}

		int second = readUnsignedByte(inputStream, this);
		chcks.update((byte)second);

		if (second < 0 || second > 60) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("Illegal second value in tIME chunk"));

		}

		long crc32 = readUnsignedInt(inputStream, PNG_ENDIANITY, this);

		if (crc32 != chcks.getValue()) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("CRC Error in tIME chunk" ));

		}

		// Some operations to deal with GregorianCalendar class, that
		// has 0 base  month numbering and doesn't like leap seconds
		second = (second == 60) ? 59 : second;
		month--;
		repInfo.setLastModified(new GregorianCalendar((yhrHigh<<8)+yhrLow ,
													  month,
													  day,
													  hour,
													  minute,
													  second).getTime());

    }


    private final void checktEXT(final DataInputStream inputStream,
								 final RepInfo repInfo,
								 int declChunkLen)
		throws IOException {
		int c=-1;
		int keywordLen=0;
		StringBuffer buf = new StringBuffer();

		while (keywordLen < MAX_KEYWORD_LEN) {
			c = readUnsignedByte(inputStream, this);
			chcks.update((byte)c);

			declChunkLen--;

			if (c==0) {
				break;
			}

			keywordLen++;
			buf.append((char)c);
		}


		if (keywordLen == MAX_KEYWORD_LEN) {
			// we hit MAX_KEYWORD_LEN, let's check if there's the
			// mandatory 0 byte
			c = readUnsignedByte(inputStream, this);
			chcks.update((byte)c);
			declChunkLen--;

			if (c != 0) {
				// segnalare errore e scartare
				repInfo.setValid(RepInfo.FALSE);
				repInfo.setMessage(new ErrorMessage("Missing 0 byte after keyword"));

				checkChunk(inputStream, repInfo, declChunkLen, "tEXT");
				buf.append((char)c);

			}


			return;
		}

		String keyword = buf.toString();

		// so far we got a keyword and the null ( 0 ) separator, lets'
		// get the value, set a property and check that everything is
		// OK with the CRC.

		buf.delete(0, buf.length() );

		while (declChunkLen > 0) {
			c = readUnsignedByte(inputStream, this);
			chcks.update((byte)c);
			declChunkLen--;

		}

		String value = buf.toString();

		Property p = new Property(keyword,
								  PropertyType.STRING,
								  value);
		repInfo.setProperty(p);
		Booolean bol = (Booolean)keywordList.get(keyword);

		if (bol != null) {
			bol.setFlag(true);
		}

		long crc32 = readUnsignedInt(inputStream, PNG_ENDIANITY, this);

		if (crc32 != chcks.getValue()) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("CRC Error in tEXT chunk" ));

		}


    }

    private final void checkChunk(final DataInputStream inputStream,
								  final RepInfo repInfo,
								  int declChunkLen,
								  final String chunkSig)
		throws IOException {
		int read = 0;

		while (read < declChunkLen) {
			int tmp = readUnsignedByte(inputStream, this);
			chcks.update((byte)tmp);
			read++;
		}
		long crc32 = readUnsignedInt(inputStream, PNG_ENDIANITY, this);

		if (crc32 != chcks.getValue()) {
			repInfo.setValid(RepInfo.FALSE);
			repInfo.setMessage(new ErrorMessage("CRC Error in " + chunkSig +" chunk" ));

		}

    }

    // Utility predicate
    private final boolean somethingWrongP(RepInfo repInfo) {
		return repInfo.getWellFormed() == RepInfo.FALSE ||
			repInfo.getValid() == RepInfo.FALSE;
    }

    private final String getCompressedString(DataInputStream dis,
											 int bytesToRead)
		throws IOException, DataFormatException {
		ByteArrayOutputStream bous = new ByteArrayOutputStream();
		Inflater pump = new Inflater();
		byte o[] = new byte[1024];

		while (bytesToRead > 0) {
			int c = 0;

			while (c < 1024 && bytesToRead > 0) {
				o[c++] = (byte)(readUnsignedByte(dis,this));
				bytesToRead--;
			}

			pump.setInput(o);

			c=1;
			while (!pump.needsInput() && c > 0) {
				c = pump.inflate(o);

				if (c>0)
					bous.write(o,0,c);
			}


		}

		return bous.toString("ISO-8859-1");

    }

    // Turns an 32 bit integer intto a byte array
    private final byte[] int2byteArray(int a)
	{
		byte b[]=new byte[]{0,0,0,0};

		b[3]=(byte)(a&0xFF);
		a=a>>8;

		b[2]=(byte)(a&0xFF);
		a=a>>8;

		b[1]=(byte)(a&0xFF);
		a=a>>8;

		b[0]=(byte)(a&0xFF);

		return b;

    }


//    private final Checksummer chcks = new Checksummer();

    // Strangely, it seems it doesn't work with the other checksummer...
    private final CRC32 chcks = new CRC32();

    // PNG signature
    private static final int SIGNATURE[] = {137, 80, 78, 71, 13, 10, 26, 10};

    // Module instantiation constants.
    private static final String NAME = "PNG-engineering";
    private static final String RELEASE = "1.0";
    private static final int DATE[] = {2006, 9, 25};
    private static final String FORMAT[] = {
		"PNG",
		"Portable Network Graphics"
	};
    private static final String MIMETYPE[] = {"image/png"};
    private static final String COVERAGE = "PNG";
    private static final String WELLFORMED = null;
    private static final String VALIDITY = null;
    private static final String REPINFO = null;
    private static final String NOTE = "Work in progress";
    private static final String RIGHTS =
		"Copyright 2006 Engineering Ingengeria Informatica S.p.a." +
		"Released under the GNU Lesser General Public License." +
		"Cryptoserver Library Copyright Engiweb Security, all rights reserved";
    private static final boolean RANDOM = false;

    /*
     * Chunk signatures.
     *
     * Java *IS* Big Endian, PNG chunk signatures are 4 byte strings we
     * *CAN* read into an int variable since all of them have bit 7
     * set to 0.
     *
     * Therefore we can check each chunk signature against int
     * constants (one opcode executed, no loops).
     *
     * About names: these name violate the Java naming rules for
     * constants, but I prefer to keep the PNG chunk name cases, since
     * they are meaningful for the properties of each chunk.
     */
    private final static int IHDR_HEAD_SIG = 0x49484452;
    private final static int PLTE_HEAD_SIG = 0x504c5445;
    private final static int IDAT_HEAD_SIG = 0x49444154;
    private final static int IEND_HEAD_SIG = 0x49454e44;
    private final static int cHRM_HEAD_SIG = 0x6348524d;
    private final static int gAMA_HEAD_SIG = 0x67414d41;
    private final static int iCCP_HEAD_SIG = 0x69434350;
    private final static int sBIT_HEAD_SIG = 0x73424954;
    private final static int sRGB_HEAD_SIG = 0x73524742;
    private final static int tEXt_HEAD_SIG = 0x74455874;
    private final static int zTXt_HEAD_SIG = 0x7a545874;
    private final static int iTXt_HEAD_SIG = 0x69545874;
    private final static int bKGD_HEAD_SIG = 0x624b4744;
    private final static int hIST_HEAD_SIG = 0x68495354;
    private final static int pHYs_HEAD_SIG = 0x70485973;
    private final static int sPLT_HEAD_SIG = 0x73504c54;
    private final static int tIME_HEAD_SIG = 0x74494d45;
    private final static int tRNS_HEAD_SIG = 0x74524e53;
    // Property bit masks
    private final static int PROP_SAFE_TO_COPY = 0x00000020;
    private final static int PROP_PRIVATE = 0x00002000;
    private final static int PROP_RESERVED = 0x00200000;
    private final static int PROP_ANCILLARY = 0x20000000;

    // Maximum keyword lenght
    private final static int MAX_KEYWORD_LEN = 79;

    // Standard keyword for the creation timestamp
    private final static String CREATION_TIME_KEYWORD = "Creation Time";

    /*------------------------------------------------------------------*
      |******************************************************************|
      |*                                                                *|
      |* Parser inner state flags.                                      *|
      |*                                                                *|
      |* The state is represented by a score of flags associated to the *|
      |* chunks that should appear no more than once. The code uses the *|
      |* flags to manage the partial ordering in the chunk layout       *|
      |*                                                                *|
      |* Flags have the  value RepInfo.UNDETERMINED  when the chunk may *|
      |* either appear or not,  RepInfo.TRUE when the chunk is expected *|
      |* but has  yet to be found, RepInfo.FALSE when  the chunk should *|
      |* not appear any more. Istantiation values are for documentation *|
      |* purpose only and are repeated in the initParse() method.       *|
      |*                                                                *|
      |******************************************************************|
      *------------------------------------------------------------------*/

    /*
     * Starting chunk, must be the first one, expected.
     */
    private int expectingIHDR = RepInfo.TRUE;

    /*
     * This is 3 state flag: it is unknown until you know you need to
     * find the PLTE chunk, when it turs to RepInfo.TRUE or/and you
     * know you should not find such block any more (i.e. from color
     * type and bit depth or because you already got this chunk.
     */
    private int expectingPLTE = RepInfo.UNDETERMINED;

    /*
     * Data chunk, turns to RepInfo.false upon finding the firs chunk
     * of this type
     */
    private int expectingIDAT = RepInfo.TRUE;

    /*
     * Ending chunk, this flag is used to handle the end of file
     * condition, if it happens when the flag is RepInfo.TRUE; then
     * the file is not well formed.
     */
    private int expectingIEND = RepInfo.TRUE;

    // non critical chunks

    private int expecting_cHRM = RepInfo.UNDETERMINED;
    private int expecting_gAMA = RepInfo.UNDETERMINED;
    private int expecting_iCCP = RepInfo.UNDETERMINED;
    private int expecting_sBIT = RepInfo.UNDETERMINED;
    private int expecting_sRGB = RepInfo.UNDETERMINED;
    private int expecting_tEXt = RepInfo.UNDETERMINED;
    private int expecting_zTXt = RepInfo.UNDETERMINED;
    private int expecting_iTXt = RepInfo.UNDETERMINED;
    private int expecting_bKGD = RepInfo.UNDETERMINED;
    private int expecting_hIST = RepInfo.UNDETERMINED;
    private int expecting_pHYs = RepInfo.UNDETERMINED;
    private int expecting_sPLT = RepInfo.UNDETERMINED;
    private int expecting_tIME = RepInfo.UNDETERMINED;
    private int expecting_tRNS = RepInfo.UNDETERMINED;

    // Palette size, in colours
    private int maxPaletteSize = 0;
    private int paletteSize = 0;
    private boolean shortPalette = false;
    private int colorDepth = 0;

    private Map keywordList;

    private final static String PNG_PROFILES[] =
		new String[] { "PNG GrayScale",             // 0
					   "Unused",                    // 1
					   "PNG Truecolor",             // 2
					   "PNG Indexed",               // 3
					   "PNG GrayScale with Alpha",  // 4
					   "Unused",                    // 5
					   "PNG Truecolor with Alpha"}; // 6

}
