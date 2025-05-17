#!/usr/bin/env python3

"""Google Cloud Vision to hOCR converter module.

This module converts Google Cloud Vision API responses to hOCR format,
which is an open standard for representing OCR results.
"""

import argparse
import json
import logging
import math
import sys
from html import escape
from string import Template

__all__ = ['GCVAnnotation', 'fromResponse']

log = logging.getLogger(__name__)


class GCVAnnotation:
    """Handles conversion of Google Cloud Vision annotations to hOCR format.

    This class processes the raw GCV response and generates properly formatted
    hOCR elements with appropriate coordinate transformations and text content.
    """
    page_height = None
    page_width = None
    dpi_x = 72.0
    dpi_y = 72.0

    templates = {
        'ocr_page': Template("""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="$lang" lang="$lang">
  <head>
    <title>HOCR File</title>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
    <meta name='ocr-system' content='gcv2hocr.py' />
    <meta name='ocr-langs' content='$lang' />
    <meta name='ocr-number-of-pages' content='1' />
    <meta name='ocr-capabilities'
          content='ocr_page ocr_carea ocr_par ocr_line ocrx_word ocrp_lang'/>
  </head>
  <body>
    <div class='ocr_page' lang='$lang'
         title='image "$title";bbox 0 0 $page_width_pt $page_height_pt'>
      <div class='ocr_carea' lang='$lang'
           title='bbox $x0 $y0 $x1 $y1'>$content</div>
    </div>
  </body>
</html>
    """),
        # Updated baseline value in title
        'ocr_line': Template("""\
            <span class='ocr_line' id='$htmlid'
                  title='bbox $x0 $y0 $x1 $y1; baseline $baseline_str; x_fsize $fsize'>
              $content
            </span>"""),
        'ocrx_word': Template("""\
            <span class='ocrx_word' id='$htmlid'
                  title='bbox $x0 $y0 $x1 $y1'>$content</span>"""),
        'ocr_carea': Template("""\
            <div class='ocr_carea' id='$htmlid'
                 title='bbox $x0 $y0 $x1 $y1'>$content</div>"""),
        'ocr_par': Template("""\
            <p class='ocr_par' dir='ltr' id='$htmlid'
               title='bbox $x0 $y0 $x1 $y1'>$content</p>""")
    }

    def __init__(self,
                 htmlid=None,
                 ocr_class=None,
                 lang='unknown',
                 page_height_px=None,
                 page_width_px=None,
                 content=None,
                 box=None, # GCV vertices in pixels
                 raw_vertices=None, # Store raw vertices for baseline calc if needed
                 title='',
                 savefile=False):
        """Initialize a GCVAnnotation object.

        Args:
            htmlid (str, optional): HTML element ID. Defaults to None.
            ocr_class (str, optional): OCR element class type. Defaults to None.
            lang (str, optional): Language code. Defaults to 'unknown'.
            page_height_px (int, optional): Page height in pixels. Defaults to None.
            page_width_px (int, optional): Page width in pixels. Defaults to None.
            content (list, optional): OCR content elements. Defaults to None.
            box (list, optional): Bounding box vertices in pixels. Defaults to None.
            raw_vertices (list, optional): Raw vertex data for baseline calculation.
            Defaults to None.
            title (str, optional): Title attribute. Defaults to ''.
            savefile (bool, optional): Whether to save to file. Defaults to False.
        """
        if content is None:
            self.content = []
        else:
            self.content = content
        self.title = title
        self.htmlid = htmlid
        self.page_height_px = page_height_px
        self.page_width_px = page_width_px
        self.lang = lang
        self.ocr_class = ocr_class
        self.raw_vertices = raw_vertices if ocr_class == 'ocrx_word' else None

        try:
            effective_page_height = (
                self.page_height_px if self.page_height_px is not None else 0
            )
            if effective_page_height <= 0 and ocr_class != 'ocr_page':
                 self.x0, self.y0, self.x1, self.y1 = 0, 0, 0, 0
                 if ocr_class != 'ocr_page':
                     return


            if not box or len(box) < 4:
                 self.x0, self.y0, self.x1, self.y1 = 0, 0, 0, 0

                 return

            x_coords = [int(float(v.get('x', 0))) for v in box if v and 'x' in v]
            y_coords = [int(float(v.get('y', 0))) for v in box if v and 'y' in v]

            if not x_coords or not y_coords:
                 log.warning(
                    f"Could not extract valid coords for {ocr_class} {htmlid}. "
                    "Using 0s."
                 )
                 self.x0, self.y0, self.x1, self.y1 = 0, 0, 0, 0
            else:
                 gcv_x_min = min(x_coords)
                 gcv_y_min = min(y_coords)
                 gcv_x_max = max(x_coords)
                 gcv_y_max = max(y_coords)

                 dpi_x = (
                    GCVAnnotation.dpi_x
                    if GCVAnnotation.dpi_x and GCVAnnotation.dpi_x > 0
                    else 72.0
                 )
                 dpi_y = (
                    GCVAnnotation.dpi_y
                    if GCVAnnotation.dpi_y and GCVAnnotation.dpi_y > 0
                    else 72.0
                 )


                 pt_x0 = gcv_x_min * 72.0 / dpi_x
                 pt_x1 = gcv_x_max * 72.0 / dpi_x
                 page_h_pt = effective_page_height * 72.0 / dpi_y
                 pt_y_bottom = page_h_pt - (gcv_y_max * 72.0 / dpi_y)
                 pt_y_top = page_h_pt - (gcv_y_min * 72.0 / dpi_y)

                 self.x0 = max(0, pt_x0)
                 self.y0 = max(0, pt_y_bottom)
                 self.x1 = max(0, pt_x1)
                 self.y1 = max(0, pt_y_top)

                 if self.y1 < self.y0:
                     log.warning(
                        f"Calculated invalid point height for {ocr_class} {htmlid} "
                        f"(y1 < y0): {self.y1} < {self.y0}. Setting y1=y0."
                     )
                     self.y1 = self.y0
                 if self.x1 < self.x0:
                      log.warning(
                        f"Calculated invalid point width for {ocr_class} {htmlid} "
                        f"(x1 < x0): {self.x1} < {self.x0}. Setting x1=x0."
                     )
                      self.x1 = self.x0

        except (ValueError, TypeError, IndexError, KeyError) as e:
            log.error(
                f"Error processing boundingBox for {ocr_class} {htmlid}: {box}. "
                f"Error: {e}",
                exc_info=True
            )
            self.x0, self.y0, self.x1, self.y1 = 0, 0, 0, 0


    def maximize_bbox(self):
        """Recalculates the bounding box (in points) based on child content."""
        if not self.content or not isinstance(self.content, list):
            return
        try:
            children_with_coords = [
                w for w in self.content
                if (hasattr(w, 'x0') and hasattr(w, 'y0') and
                    hasattr(w, 'x1') and hasattr(w, 'y1'))
            ]

            if not children_with_coords:
                return

            all_x0 = [w.x0 for w in children_with_coords]
            all_y0 = [w.y0 for w in children_with_coords]
            all_x1 = [w.x1 for w in children_with_coords]
            all_y1 = [w.y1 for w in children_with_coords]

            if all_x0 and all_y0 and all_x1 and all_y1:
                 self.x0 = min(all_x0)
                 self.y0 = min(all_y0)
                 self.x1 = max(all_x1)
                 self.y1 = max(all_y1)
            else:
                 log.warning(
                     f"Could not maximize bbox for {self.ocr_class} {self.htmlid} "
                     "despite having children (coord issue?)."
                 )
        except Exception as e:
             log.error(
                 f"Error during maximize_bbox for {self.ocr_class} {self.htmlid}: {e}",
                 exc_info=True
             )


    def __repr__(self):
        content_repr = (
            self.content
            if isinstance(self.content, str)
            else f"[{len(self.content)} items]"
        )
        return (
            f"<{self.ocr_class} id={self.htmlid} "
            f"bbox=[{self.x0:.1f} {self.y0:.1f} {self.x1:.1f} {self.y1:.1f}]>"
            f"{content_repr}</{self.ocr_class}>"
        )

    def render(self):
        rendered_content = ""
        if isinstance(self.content, list):
            rendered_content = "".join(map(lambda x: x.render(), self.content))
        elif isinstance(self.content, str):
            rendered_content = escape(str(self.content))

        page_width_pt = (self.page_width_px or 0) * 72.0 / (GCVAnnotation.dpi_x or 72.0)
        page_height_pt = (
            self.page_height_px or 0) * 72.0 / (GCVAnnotation.dpi_y or 72.0
        )

        template_vars = {
            'lang': self.lang if self.lang else 'unknown',
            'title': self.title if self.title else '',
            'page_width_pt': page_width_pt,
            'page_height_pt': page_height_pt,
            'page_width': self.page_width_px if self.page_width_px is not None else 0,
            'page_height': (
                self.page_height_px if self.page_height_px is not None else 0
            ),
            'x0': self.x0, 'y0': self.y0, 'x1': self.x1, 'y1': self.y1,
            'htmlid': self.htmlid if self.htmlid else '',
            'content': rendered_content
        }

        # --- Add estimated font size and baseline for ocr_line ---
        if self.ocr_class == 'ocr_line':
             line_height_pt = self.y1 - self.y0
             estimated_fsize_pt = (
                max(1, math.ceil(line_height_pt / 1.3)) if line_height_pt > 0 else 1
             )
             template_vars['fsize'] = estimated_fsize_pt

             # --- Calculate Baseline ---
             baseline_offset = 0 # Default offset
             avg_word_bottom_y_px = 0
             if isinstance(self.content, list):
                  word_bottoms_px = []
                  for word in self.content:
                       if (
                            word.ocr_class == 'ocrx_word' and
                            word.raw_vertices and
                            len(word.raw_vertices) >= 4
                        ):
                            # GCV vertices: 0=TL, 1=TR, 2=BR, 3=BL
                            try:
                                 bottom_y = (
                                    int(float(word.raw_vertices[2].get('y', 0))) +
                                    int(float(word.raw_vertices[3].get('y', 0)))
                                 ) / 2.0
                                 word_bottoms_px.append(bottom_y)
                            except (ValueError, TypeError, IndexError, KeyError):
                                 pass # Ignore words with bad vertices

                  if word_bottoms_px:
                       avg_word_bottom_y_px = (
                        sum(word_bottoms_px) / len(word_bottoms_px)
                       )
                       page_h_pt_eff = (
                        (self.page_height_px or 0) * 72.0
                        / (GCVAnnotation.dpi_y or 72.0)
                       )
                       avg_baseline_y_pt = (
                            page_h_pt_eff
                            - (avg_word_bottom_y_px * 72.0
                            / (GCVAnnotation.dpi_y or 72.0))
                        )

                       baseline_offset = avg_baseline_y_pt - self.y0


             template_vars['baseline_str'] = f"0 {baseline_offset:.2f}"

        else:
             template_vars['fsize'] = 0
             template_vars['baseline_str'] = "0 0"

        try:
            template_vars['x0'] = int(round(template_vars['x0']))
            template_vars['y0'] = int(round(template_vars['y0']))
            template_vars['x1'] = int(round(template_vars['x1']))
            template_vars['y1'] = int(round(template_vars['y1']))
            template_vars['page_width_pt'] = int(round(template_vars['page_width_pt']))
            template_vars['page_height_pt'] = int(
                round(template_vars['page_height_pt'])
            )
            template_vars['fsize'] = int(round(template_vars['fsize']))

            return (
                self.__class__.templates[self.ocr_class].substitute(template_vars)
            )
        except KeyError as e:
            if str(e) == "'baseline_str'" and self.ocr_class != 'ocr_line':
                 del template_vars['baseline_str'] # Remove if not needed
                 return (
                    self.__class__.templates[self.ocr_class]
                    .substitute(template_vars)
                 )
            elif str(e) == "'fsize'" and self.ocr_class != 'ocr_line':
                 del template_vars['fsize'] # Remove if not needed
                 return (
                    self.__class__.templates[self.ocr_class]
                    .substitute(template_vars)
                 )
            else:
                 log.error(
                    f"Template key error for class: {self.ocr_class}. "
                    f"Missing key: {e}. "
                    f"Vars: {template_vars.keys()}"
                 )
                 return ""
        except Exception as e:
            log.error(
                f"Error rendering template for {self.ocr_class} {self.htmlid}: {e}",
                exc_info=True
            )
            return ""


# --- Modified fromResponse to accept and set DPI ---
def fromResponse(
    resp,
    file_name,
    baseline_tolerance=2,
    image_dpi_x=None,
    image_dpi_y=None,
    **kwargs
):
    """Convert Google Cloud Vision API response to hOCR format.

    Args:
        resp (dict): The GCV API response dictionary
        file_name (str): Name of the input image file
        baseline_tolerance (int, optional): Y-axis tolerance for line detection.
        Defaults to 2.
        image_dpi_x (float, optional): Image horizontal DPI. Defaults to None.
        image_dpi_y (float, optional): Image vertical DPI. Defaults to None.
        **kwargs: Additional keyword arguments

    Returns:
        GCVAnnotation: An hOCR page object containing the OCR results
    """
    page = None
    GCVAnnotation.dpi_x = image_dpi_x if image_dpi_x and image_dpi_x > 0 else 72.0
    GCVAnnotation.dpi_y = image_dpi_y if image_dpi_y and image_dpi_y > 0 else 72.0
    log.debug(
        f"Using DPI for hOCR conversion: dx={GCVAnnotation.dpi_x}, "
        f"dy={GCVAnnotation.dpi_y}"
    )

    try:
        if 'responses' not in resp or not resp['responses']:
             log.warning(
                f"Invalid GCV response structure for {file_name}. "
                "Generating empty page."
             )
             page = GCVAnnotation(
                ocr_class='ocr_page',
                htmlid='page_0',
                box=None,
                title=file_name,
                page_width_px=0,
                page_height_px=0
             )
             return page

        annotation = resp['responses'][0].get('fullTextAnnotation')
        if not annotation:
             log.warning(
                f"No 'fullTextAnnotation' found in GCV response for {file_name}. "
                "Generating empty page."
             )
             page = GCVAnnotation(
                ocr_class='ocr_page',
                htmlid='page_0',
                box=None,
                title=file_name,
                page_width_px=0,
                page_height_px=0
             )
             return page

        # --- Page Loop ---
        for page_id, page_json in enumerate(annotation.get('pages', [])):
            current_page_height_px = page_json.get('height')
            current_page_width_px = page_json.get('width')
            if current_page_height_px is None or current_page_width_px is None:
                 log.error(
                    f"Missing page dimensions (pixels) for page {page_id}. "
                    "Cannot process."
                 )
                 continue

            log.debug(
                f"Processing page {page_id}: width={current_page_width_px}px, "
                f"height={current_page_height_px}px"
            )

            page_box_vertices = [
                {"x": 0, "y": 0},
                {"x": current_page_width_px, "y": 0},
                {"x": current_page_width_px, "y": current_page_height_px},
                {"x": 0, "y": current_page_height_px},
            ]

            page = GCVAnnotation(
                ocr_class='ocr_page',
                htmlid=f'page_{page_id + 1}',
                box=page_box_vertices,
                title=file_name,
                page_width_px=current_page_width_px,
                page_height_px=current_page_height_px,
                lang=annotation.get('language', 'unknown')
            )

            page_carea = GCVAnnotation(
                ocr_class='ocr_carea',
                htmlid=f'carea_page_{page_id + 1}',
                box=page_box_vertices,
                page_width_px=current_page_width_px,
                page_height_px=current_page_height_px
            )
            page.content.append(page_carea)

            # --- Block Loop ---
            for block_id, block_json in enumerate(page_json.get('blocks', [])):
                # --- Paragraph Loop ---
                for paragraph_id, paragraph_json in enumerate(
                    block_json.get('paragraphs', [])
                ):
                    par_box_vertices = paragraph_json.get(
                        'boundingBox', {}
                    ).get(
                        'vertices', []
                    )
                    par = GCVAnnotation(
                        ocr_class='ocr_par',
                        htmlid=f"par_{page_id + 1}_{block_id + 1}_{paragraph_id + 1}",
                        box=par_box_vertices,
                        page_width_px=current_page_width_px,
                        page_height_px=current_page_height_px
                    )
                    page_carea.content.append(par)

                    current_line = None

                    # --- Word Loop ---
                    for word_id, word_json in enumerate(
                    paragraph_json.get('words', [])):
                        word_box_vertices = word_json.get(
                            'boundingBox', {}
                        ).get('vertices', [])
                        word_text = ''.join(
                            symbol.get('text', '')
                            for symbol in word_json.get('symbols', [])
                        )

                        # --- Line Handling Logic ---
                        if current_line is None:
                             current_line = GCVAnnotation(
                                ocr_class='ocr_line',
                                htmlid=f"line_{par.htmlid}_{word_id + 1}",
                                box=word_box_vertices,
                                page_width_px=current_page_width_px,
                                page_height_px=current_page_height_px
                            )
                             par.content.append(current_line)

                        # Store raw vertices with the word object
                        word = GCVAnnotation(
                            ocr_class='ocrx_word',
                            htmlid=f"word_{current_line.htmlid}_{word_id + 1}",
                            content=word_text,
                            box=word_box_vertices,
                            raw_vertices=word_box_vertices,
                            page_width_px=current_page_width_px,
                            page_height_px=current_page_height_px
                        )
                        current_line.content.append(word)

                        line_break_detected = False
                        for symbol in word_json.get('symbols', []):
                            detected_break = symbol.get(
                                'property', {}
                            ).get(
                                'detectedBreak', {}
                            )
                            break_type = detected_break.get('type')
                            if break_type in ["LINE_BREAK", "EOL_SURE_SPACE"]:
                                line_break_detected = True
                                break

                        if line_break_detected:
                            if current_line:
                                 current_line.maximize_bbox()
                            current_line = None

                    if current_line:
                        current_line.maximize_bbox()

            for p in page_carea.content:
                 if p.ocr_class == 'ocr_par':
                      p.maximize_bbox()

            # Maximize the main carea box
            page_carea.maximize_bbox()

            break # Process only the first page

    except Exception as e:
        log.error(f"Error in fromResponse function: {e}", exc_info=True)
        page = GCVAnnotation(
            ocr_class='ocr_page',
            htmlid='page_error',
            box=None,
            title=file_name,
            page_width_px=0,
            page_height_px=0
        )

    if page is None:
         log.warning("fromResponse resulted in None page, creating empty fallback.")
         page = GCVAnnotation(
            ocr_class='ocr_page',
            htmlid='page_fallback',
            box=None,
            title=file_name,
            page_width_px=0,
            page_height_px=0
         )

    return page


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('gcv_file', help='GCV JSON file, "-" for STDIN')
    parser.add_argument(
        "--baseline", "-B",
        help="Baseline offset",
        metavar="pn pn-1 ...",
        default="0 0"
    )
    parser.add_argument(
        "--baseline-tolerance", "-T",
        help="Y Tolerance to recognize same line. Default: 2",
        metavar="INT",
        type=int,
        default=2
    )
    parser.add_argument(
        "--savefile",
        help="Save to this file instead of outputting to stdout"
    )
    parser.add_argument("--dpi-x", help="Image DPI X", type=float, default=72.0)
    parser.add_argument("--dpi-y", help="Image DPI Y", type=float, default=72.0)

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    try:
        if args.gcv_file == '-':
            instream = sys.stdin
        else:
            instream = open(args.gcv_file, encoding='utf-8')
        resp_main = json.load(instream)
        resp_wrapped = {"responses": [resp_main]}
        page = fromResponse(
            resp_wrapped,
            str(args.gcv_file.rsplit('.', 1)[0]),
            image_dpi_x=args.dpi_x,
            image_dpi_y=args.dpi_y,
            **args.__dict__
        )

        if page:
            rendered_hocr = page.render()
            if args.savefile:
                with open(args.savefile, 'w', encoding="utf-8") as outfile:
                    outfile.write(rendered_hocr)
                log.info(f"hOCR saved to {args.savefile}")
            else:
                 print(rendered_hocr)
        else:
             log.error("Failed to generate hOCR page object.")

    except FileNotFoundError:
        log.error(f"Input file not found: {args.gcv_file}")
    except json.JSONDecodeError:
         log.error(f"Invalid JSON in file: {args.gcv_file}")
    except Exception as e:
         log.error(f"An unexpected error occurred: {e}", exc_info=True)
