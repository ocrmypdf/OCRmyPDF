# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MIT

"""Compare two PDFs."""

from __future__ import annotations

import os
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pikepdf
import pymupdf
import streamlit as st
from lxml import etree
from streamlit_pdf_viewer import pdf_viewer


def do_metadata(pdf):
    with pikepdf.open(pdf) as pdf:
        with pdf.open_metadata() as meta:
            xml_txt = str(meta)
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.fromstring(xml_txt, parser=parser)
            st.code(
                etree.tostring(tree, pretty_print=True).decode("utf-8"),
                language="xml",
            )
        st.write(pdf.docinfo)
        st.write("Number of pages:", len(pdf.pages))


def main():
    st.set_page_config(layout="wide")

    st.title("PDF Compare")
    st.write("Compare two PDFs.")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_pdf1 = st.file_uploader("Upload a PDF", type=["pdf"], key='pdf1')
    with col2:
        uploaded_pdf2 = st.file_uploader("Upload a PDF", type=["pdf"], key='pdf2')
    if uploaded_pdf1 is None or uploaded_pdf2 is None:
        return

    pdf_bytes1 = uploaded_pdf1.getvalue()
    pdf_bytes2 = uploaded_pdf2.getvalue()

    with st.expander("PDF Metadata"):
        col1, col2 = st.columns(2)
        with col1:
            do_metadata(BytesIO(pdf_bytes1))
        with col2:
            do_metadata(BytesIO(pdf_bytes2))

    with TemporaryDirectory() as d:
        Path(d, "1.pdf").write_bytes(pdf_bytes1)
        Path(d, "2.pdf").write_bytes(pdf_bytes2)

        with st.expander("Text"):
            doc1 = pymupdf.open(os.path.join(d, "1.pdf"))
            doc2 = pymupdf.open(os.path.join(d, "2.pdf"))
            for i, page1_2 in enumerate(zip(doc1, doc2)):
                st.write(f"Page {i+1}")
                page1, page2 = page1_2
                col1, col2 = st.columns(2)
                with col1, st.container(border=True):
                    st.write(page1.get_text())
                with col2, st.container(border=True):
                    st.write(page2.get_text())

        with st.expander("PDF Viewer"):
            col1, col2 = st.columns(2)
            with col1:
                pdf_viewer(Path(d, "1.pdf"), key='pdf_viewer1', render_text=True)
            with col2:
                pdf_viewer(Path(d, "2.pdf"), key='pdf_viewer2', render_text=True)


if __name__ == "__main__":
    main()
