# © 2022 James R. Barlow: github.com/jbarlow83
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Built-in plugin to implement PDF page optimization."""

from pathlib import Path

from ocrmypdf import PdfContext, hookimpl
from ocrmypdf._concurrent import Executor
from ocrmypdf._pipeline import get_pdf_save_settings, should_linearize
from ocrmypdf.optimize import optimize


@hookimpl
def optimize_pdf(
    input_pdf: Path, output_pdf: Path, context: PdfContext, executor: Executor
) -> Path:
    save_settings = dict(
        linearize=should_linearize(input_pdf, context),
        **get_pdf_save_settings(context.options.output_type),
    )
    optimize(input_pdf, output_pdf, context, save_settings, executor)
    return output_pdf
