# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This is a simple web service/HTTP wrapper for OCRmyPDF.

This may be more convenient than the command line tool for some Docker users.
Note that OCRmyPDF uses Ghostscript, which is licensed under AGPLv3+. While
OCRmyPDF is under GPLv3, this file is distributed under the Affero GPLv3+ license,
to emphasize that SaaS deployments should make sure they comply with
Ghostscript's license as well as OCRmyPDF's.
"""

from __future__ import annotations

import os
import subprocess
import sys
from functools import partial
from operator import getitem
from pathlib import Path
from tempfile import NamedTemporaryFile

import pikepdf
import streamlit as st

from ocrmypdf._defaults import DEFAULT_ROTATE_PAGES_THRESHOLD


def get_host_url_with_port(port: int) -> str:
    """Get the host URL for the web service. Hacky."""
    host_url = st.context.headers["host"]
    try:
        host, _streamlit_port = host_url.split(":", maxsplit=1)
    except ValueError:
        host = host_url
    return f"//{host}:{port}"  # Use the same protocol


st.title("OCRmyPDF Web Service")

uploaded = st.file_uploader("Upload input PDF or image", type=["pdf"], key="file")

mode = st.selectbox("Mode", options=["normal", "skip-text", "force-ocr", "redo-ocr"])

pages = st.text_input(
    "Pages", value="", help="Comma-separated list of pages to process"
)

with st.expander("Input options"):
    invalidate_digital_signatures = st.checkbox(
        "Invalidate digital signatures", value=False
    )
    language = st.selectbox("Language", options=["eng", "deu", "fra", "spa"])

    image_dpi = st.slider(
        "Image DPI", value=300, key="image_dpi", min_value=1, max_value=5000, step=50
    )
with st.expander("Preprocessing"):
    skip_big = st.checkbox("Skip OCR on big pages", value=False, key="skip_big")
    oversample = st.slider("Oversample", min_value=0, max_value=5000, value=0, step=50)
    rotate_pages = st.checkbox("Rotate pages", value=False, key="rotate")
    deskew = st.checkbox("Deskew pages", value=False, key="deskew")
    clean = st.checkbox("Clean pages before OCR", value=False, key="clean")
    clean_final = st.checkbox("Clean final", value=False, key="clean_final")
    remove_vectors = st.checkbox("Remove vectors", value=False, key="remove_vectors")


with st.expander("Output options"):
    output_type = st.selectbox(
        "Output type", options=["pdfa", "pdf", "pdfa-1", "pdfa-2", "pdfa-3", "none"]
    )

    pdf_renderer = st.selectbox(
        "PDF renderer", options=["auto", "hocr", "hocrdebug", "sandwich"]
    )

    optimize = st.selectbox("Optimize", options=["0", "1", "2", "3"])

    st.selectbox("PDF/A compression", options=["auto", "jpeg", "lossless"])

with st.expander("Metadata"):
    title = author = keywords = subject = None
    if uploaded:
        with pikepdf.open(uploaded) as pdf, pdf.open_metadata() as meta:
            st.code(str(meta), language="xml")
            title = st.text_input("Title", value=meta.get('dc:title', ''))
            author = st.text_input("Author", value=meta.get('dc:creator', ''))
            keywords = st.text_input("Keywords", value=meta.get('dc:subject', ''))
            subject = st.text_input("Subject", value=meta.get('dc:description', ''))


with st.expander("Optimization after OCR"):
    jpeg_quality = st.slider(
        "JPEG quality", min_value=0, max_value=100, value=75, key="jpeg_quality"
    )
    png_quality = st.slider(
        "PNG quality", min_value=0, max_value=100, value=75, key="png_quality"
    )
    jbig2_lossy = st.checkbox("JBIG2 lossy (dangerous)", value=False, key="jbig2_lossy")
    jbig2_threshold = st.number_input("JBIG2 threshold", value=0, key="jbig2_threshold")

with st.expander("Advanced options"):
    jobs = st.slider(
        "Threads",
        min_value=1,
        max_value=os.cpu_count(),
        value=os.cpu_count(),
        key="threads",
    )
    max_image_mpixels = st.number_input(
        "Max image size",
        value=250.0,
        min_value=0.0,
        help="Maximum image size in megapixels",
    )
    rotate_pages_threshold = st.number_input(
        "Rotate pages threshold",
        value=DEFAULT_ROTATE_PAGES_THRESHOLD,
        min_value=0.0,
        max_value=1000.0,
        help="Threshold for automatic page rotation",
    )
    fast_web_view = st.number_input(
        "Fast web view",
        value=1.0,
        min_value=0.0,
        help="Linearize files above this size in MB",
    )
    continue_on_soft_render_error = st.checkbox(
        "Continue on soft render error", value=True
    )
    verbose_labels = ["quiet", "default", "debug", "debug_all"]
    verbose = st.selectbox(
        "Verbosity level",
        options=[-1, 0, 1, 2],
        index=1,
        format_func=partial(getitem, verbose_labels),
    )

if uploaded:
    args = []
    if mode and mode != 'normal':
        args.append(f"--{mode}")
    if language:
        args.append(f"--language={language}")
    if not uploaded.name.lower().endswith(".pdf") and image_dpi:
        args.append(f"--image-dpi={image_dpi}")
    if skip_big:
        args.append("--skip-big")
    if oversample:
        args.append(f"--oversample={oversample}")
    if rotate_pages:
        args.append("--rotate-pages")
    if deskew:
        args.append("--deskew")
    if clean:
        args.append("--clean")
    if clean_final:
        args.append("--clean-final")
    if remove_vectors:
        args.append("--remove-vectors")
    if output_type:
        args.append(f"--output-type={output_type}")
    if pdf_renderer:
        args.append(f"--pdf-renderer={pdf_renderer}")
    if optimize:
        args.append(f"--optimize={optimize}")
    if title:
        args.append(f"--title={title}")
    if author:
        args.append(f"--author={author}")
    if keywords:
        args.append(f"--keywords={keywords}")
    if subject:
        args.append(f"--subject={subject}")
    if pages:
        args.append(f"--pages={pages}")
    if max_image_mpixels:
        args.append(f"--max-image-mpixels={max_image_mpixels}")
    if rotate_pages_threshold:
        args.append(f"--rotate-pages-threshold={rotate_pages_threshold}")
    if fast_web_view:
        args.append(f"--fast-web-view={fast_web_view}")
    if continue_on_soft_render_error:
        args.append("--continue-on-soft-render-error")
    if verbose:
        args.append(f"--verbose={verbose}")
    if optimize > '0' and jpeg_quality:
        args.append(f"--jpeg-quality={jpeg_quality}")
    if optimize > '0' and png_quality:
        args.append(f"--png-quality={png_quality}")
    if jbig2_lossy:
        args.append("--jbig2-lossy")
    if jbig2_threshold:
        args.append(f"--jbig2-threshold={jbig2_threshold}")
    if jobs:
        args.append(f"--jobs={jobs}")
    input_file = NamedTemporaryFile(delete=True, suffix=f"_{uploaded.name}")
    input_file.write(uploaded.getvalue())
    input_file.flush()
    input_file.seek(0)
    args.append(str(input_file.name))
    output_file = NamedTemporaryFile(delete=True, suffix=".pdf")
    args.append(str(output_file.name))

    st.session_state['running'] = (
        'run_button' in st.session_state and st.session_state.run_button
    )
    if st.button(
        "Run OCRmyPDF",
        disabled=st.session_state.get("running", False),
        key='run_button',
    ):
        st.session_state['running'] = True
        args = [sys.executable, '-u', '-m', "ocrmypdf"] + args

        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with st.container(border=True):
            while proc.poll() is None:
                line = proc.stderr.readline()
                if line:
                    st.html("<code>" + line.decode().strip() + "</code>")

        if proc.returncode != 0:
            st.error(f"ocrmypdf failed with exit code {proc.returncode}")
            st.session_state['running'] = False
            st.stop()

        if Path(output_file.name).stat().st_size == 0:
            st.error("No output PDF file was generated")
            st.stop()

        st.download_button(
            label="Download output PDF",
            data=output_file.read(),
            file_name=uploaded.name,
            mime="application/pdf",
        )
        st.session_state['running'] = False
