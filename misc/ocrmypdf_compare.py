# SPDX-FileCopyrightText: 2025 James R. Barlow
# SPDX-License-Identifier: MIT

"""Run OCRmyPDF on the same PDF with different options."""

from __future__ import annotations

import os
import shlex
from io import BytesIO
from pathlib import Path
from subprocess import check_output, run
from tempfile import TemporaryDirectory

import pikepdf
import pymupdf
import streamlit as st
from lxml import etree
from streamlit_pdf_viewer import pdf_viewer


def main():
    st.set_page_config(layout="wide")

    st.title("OCRmyPDF Compare")
    st.write("Run OCRmyPDF on the same PDF with different options.")

    uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded_pdf is None:
        return

    pdf_bytes = uploaded_pdf.read()

    with pikepdf.open(BytesIO(pdf_bytes)) as p, TemporaryDirectory() as d:
        with st.expander("PDF Metadata"):
            with p.open_metadata() as meta:
                xml_txt = str(meta)
                parser = etree.XMLParser(remove_blank_text=True)
                tree = etree.fromstring(xml_txt, parser=parser)
                st.code(
                    etree.tostring(tree, pretty_print=True).decode("utf-8"),
                    language="xml",
                )
            st.write(p.docinfo)
            st.write("Number of pages:", len(p.pages))

        col1, col2 = st.columns(2)
        with col1:
            cli1 = st.text_area(
                "Command line arguments for A",
                key="args1",
                value="ocrmypdf {in_} {out}",
            )
            env1 = st.text_area("Environment variables for A", key="env1")
            args1 = shlex.split(
                cli1.format(
                    in_=os.path.join(d, "input.pdf"),
                    out=os.path.join(d, "output1.pdf"),
                )
            )
            st.code(shlex.join(args1))
        with col2:
            cli2 = st.text_area(
                "Command line arguments for B",
                key="args2",
                value="ocrmypdf {in_} {out}",
            )
            env2 = st.text_area("Environment variables for B", key="env2")
            args2 = shlex.split(
                cli2.format(
                    in_=os.path.join(d, "input.pdf"),
                    out=os.path.join(d, "output2.pdf"),
                )
            )
            st.code(shlex.join(args2))

        if not st.button("Execute and Compare"):
            return
        with st.spinner("Executing..."):
            Path(d, "input.pdf").write_bytes(pdf_bytes)
            run(args1, env=dict(os.environ, **eval(env1 or "{}")))
            run(args2, env=dict(os.environ, **eval(env2 or "{}")))

            col1, col2 = st.columns(2)
            with col1:
                st.text(
                    "Ghostscript version A: "
                    + check_output(
                        ["gs", "--version"],
                        env=dict(os.environ, **eval(env1 or "{}")),
                        text=True,
                    )
                )
            with col2:
                st.text(
                    "Ghostscript version B: "
                    + check_output(
                        ["gs", "--version"],
                        env=dict(os.environ, **eval(env2 or "{}")),
                        text=True,
                    )
                )

            doc1 = pymupdf.open(os.path.join(d, "output1.pdf"))
            doc2 = pymupdf.open(os.path.join(d, "output2.pdf"))
            for i, page1_2 in enumerate(zip(doc1, doc2)):
                st.write(f"Page {i+1}")
                page1, page2 = page1_2
                col1, col2 = st.columns(2)
                with col1, st.container(border=True):
                    st.write(page1.get_text())
                with col2, st.container(border=True):
                    st.write(page2.get_text())

            col1, col2 = st.columns(2)
            with col1, st.expander("PDF Viewer"):
                pdf_viewer(Path(d, "output1.pdf"))
            with col2, st.expander("PDF Viewer"):
                pdf_viewer(Path(d, "output2.pdf"))


if __name__ == "__main__":
    main()
