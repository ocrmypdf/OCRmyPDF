##############################################################################
# Copyright (c) 2013: fritz-hh from Github (https://github.com/fritz-hh)
#
# Copyright (c) 2010: Jonathan Brinley from Github (https://github.com/jbrinley/HocrConverter)
# Initial version by Jonathan Brinley, jonathanbrinley@gmail.com
##############################################################################
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch
from lxml import etree as ElementTree
import Image, re, sys
import argparse

class hocrTransform():
	"""
	A class for converting documents from the hOCR format.
	For details of the hOCR format, see:
	http://docs.google.com/View?docid=dfxcv4vc_67g844kf
	"""
	def __init__(self, hocrFileName, dpi):
		self.dpi = dpi
		self.boxPattern = re.compile('bbox((\s+\d+){4})')

		self.hocr = ElementTree.ElementTree()
		self.hocr.parse(hocrFileName)
 
		# if the hOCR file has a namespace, ElementTree requires its use to find elements
		matches = re.match('({.*})html', self.hocr.getroot().tag)
		self.xmlns = ''
		if matches:
			self.xmlns = matches.group(1)
			
		# get dimension in pt (not pixel!!!!) of the OCRed image
		for div in self.hocr.findall(".//%sdiv[@class='ocr_page']"%(self.xmlns)):
			coords = self.element_coordinates(div)
			self.width = self.px2pt(coords[2]-coords[0])
			self.height = self.px2pt(coords[3]-coords[1])
			break # there shouldn't be more than one, and if there is, we don't want it
			
		# no width and heigh definition in the ocr_image element of the hocr file
		if self.width is None:
			print "No page dimension found in the hocr file"
			sys.exit(1)

	def __str__(self):
		"""
		Return the textual content of the HTML body
		"""
		if self.hocr is None:
			return ''
		body = self.hocr.find(".//%sbody"%(self.xmlns))
		if body:
			return self._get_element_text(body).encode('utf-8') # XML gives unicode
		else:
			return ''
  
	def _get_element_text(self, element):
		"""
		Return the textual content of the element and its children
		"""
		text = ''
		if element.text is not None:
			text = text + element.text
		for child in element.getchildren():
			text = text + self._get_element_text(child)
		if element.tail is not None:
			text = text + element.tail
		return text
    
	def element_coordinates(self, element):
		"""
		Returns a tuple containing the coordinates of the bounding box around
		an element
		"""
		out = (0,0,0,0)
		if 'title' in element.attrib:
			matches = self.boxPattern.search(element.attrib['title'])
			if matches:
				coords = matches.group(1).split()
				out = (int(coords[0]),int(coords[1]),int(coords[2]),int(coords[3]))
		return out
    
	def px2pt(self, pxl):
		"""
		Returns the length in pt given length in pxl
		"""
		return float(pxl)/self.dpi*inch
			
	def to_pdf(self, outFileName, imageFileName, showBoundingboxes, fontname="Helvetica"):
		"""
		Creates a PDF file with an image superimposed on top of the text.
		Text is positioned according to the bounding box of the lines in
		the hOCR file.
		The image need not be identical to the image used to create the hOCR file.
		It can have a lower resolution, different color mode, etc.
		"""
		# create the PDF file
		pdf = Canvas(outFileName, pagesize=(self.width, self.height), pageCompression=1) # page size in points (1/72 in.)
		
		# draw bounding box for each paragraph
		pdf.setStrokeColorRGB(0,1,1)	# light blue for bounding box of paragraph
		pdf.setFillColorRGB(0,1,1)	# light blue for bounding box of paragraph
		pdf.setLineWidth(0)		# no line for bounding box
		for elem in self.hocr.findall(".//%sp[@class='%s']" % (self.xmlns, "ocr_par")):
		
			elemtxt=self._get_element_text(elem).rstrip()
			if len(elemtxt) == 0:
				continue

			coords = self.element_coordinates(elem)
			x1=self.px2pt(coords[0])
			y1=self.px2pt(coords[1])
			x2=self.px2pt(coords[2])
			y2=self.px2pt(coords[3])
			
			# draw the bbox border
			if showBoundingboxes == True:
				pdf.rect(x1, self.height-y2, x2-x1, y2-y1, fill=1)		
		
		
		# check if element with class 'ocrx_word' are available
		# otherwise use 'ocr_line' as fallback
		elemclass="ocr_line"
		if self.hocr.find(".//%sspan[@class='ocrx_word']" %(self.xmlns)) is not None:
			elemclass="ocrx_word"

		# itterate all text elements
		pdf.setStrokeColorRGB(1,0,0)	# light green for bounding box of word/line
		pdf.setLineWidth(0.5)		# bounding box line width
		pdf.setDash(6,3)		# bounding box is dashed
		pdf.setFillColorRGB(0,0,0)	# text in black
		for elem in self.hocr.findall(".//%sspan[@class='%s']" % (self.xmlns, elemclass)):

			elemtxt=self._get_element_text(elem).rstrip()
			if len(elemtxt) == 0:
				continue

			coords = self.element_coordinates(elem)
			x1=self.px2pt(coords[0])
			y1=self.px2pt(coords[1])
			x2=self.px2pt(coords[2])
			y2=self.px2pt(coords[3])
			
			# draw the bbox border
			if showBoundingboxes == True:
				pdf.rect(x1, self.height-y2, x2-x1, y2-y1, fill=0)

			text = pdf.beginText()
			fontsize=self.px2pt(coords[3]-coords[1])
			text.setFont(fontname, fontsize)

			# set cursor to bottom left corner of bbox (adjust for dpi)
			text.setTextOrigin(x1, self.height-y2)
       
			# scale the width of the text to fill the width of the bbox
			text.setHorizScale(100*(x2-x1)/pdf.stringWidth(elemtxt, fontname, fontsize))

			# write the text to the page
			text.textLine(elemtxt)
			pdf.drawText(text)

		# put the image on the page, scaled to fill the page
		if imageFileName != None:
			im = Image.open(imageFileName)		
			pdf.drawInlineImage(im, 0, 0, width=self.width, height=self.height)
			
		# finish up the page and save it
		pdf.showPage()
		pdf.save()
  
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Convert hocr file to PDF')
	parser.add_argument('-b', '--boundingboxes', action="store_true", default=False, help='Show bounding boxes borders')
	parser.add_argument('-r', '--resolution', type=int, default=300, help='Resolution of the image that was OCRed')
	parser.add_argument('-i', '--image', default=None, help='Path to the image to be placed above the text')
	parser.add_argument('hocrfile', help='Path to the hocr file to be parsed')
	parser.add_argument('outputfile', help='Path to the PDF file to be generated')
	args = parser.parse_args()

	hocr = hocrTransform(args.hocrfile, args.resolution)
	hocr.to_pdf(args.outputfile, args.image, args.boundingboxes)

	
	
