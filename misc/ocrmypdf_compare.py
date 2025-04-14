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


def do_column(label, suffix, d):
    cli = st.text_area(
        f"Command line arguments for {label}",
        key=f"args{suffix}",
        value="ocrmypdf {in_} {out}",
    )
    env_text = st.text_area(f"Environment variables for {label}", key=f"env{suffix}")
    env = os.environ.copy()
    for line in env_text.splitlines():
        if line:
            try:
                k, v = line.split("=", 1)
            except ValueError:
                st.error(f"Invalid environment variable: {line}")
                break
            env[k] = v
    args = shlex.split(
        cli.format(
            in_=os.path.join(d, "input.pdf"),
            out=os.path.join(d, f"output{suffix}.pdf"),
        )
    )
    with st.expander("Environment variables", expanded=bool(env_text.strip())):
        st.code('\n'.join(f"{k}={v}" for k, v in env.items()))
    st.code(shlex.join(args))
    return env, args


def main():
    st.set_page_config(layout="wide")

    st.title("OCRmyPDF Compare")
    st.write("Run OCRmyPDF on the same PDF with different options.")
    st.warning("This is a testing tool and is not intended for production use.")

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
            env1, args1 = do_column("A", "1", d)
        with col2:
            env2, args2 = do_column("B", "2", d)

        if not st.button("Execute and Compare"):
            return
        with st.spinner("Executing..."):
            Path(d, "input.pdf").write_bytes(pdf_bytes)
            run(args1, env=env1)
            run(args2, env=env2)

            col1, col2 = st.columns(2)
            with col1:
                st.text(
                    "Ghostscript version A: "
                    + check_output(
                        ["gs", "--version"],
                        env=env1,
                        text=True,
                    )
                )
            with col2:
                st.text(
                    "Ghostscript version B: "
                    + check_output(
                        ["gs", "--version"],
                        env=env2,
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
