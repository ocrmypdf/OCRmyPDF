from __future__ import annotations

import warnings

with warnings.catch_warnings():
    # reportlab uses deprecated load_module
    # shim can be removed when we require reportlab >= 3.7
    warnings.filterwarnings(
        'ignore', category=DeprecationWarning, message=r".*load_module.*"
    )
    from reportlab.lib.colors import black, cyan, magenta, red
    from reportlab.lib.units import inch
    from reportlab.pdfgen.canvas import Canvas
