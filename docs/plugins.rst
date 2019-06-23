=======
Plugins
=======

You can use plugins to customize the behavior of OCRmyPDF at certain
points of interest.

Currently, it is possible to: - override the decision for whether or not
to perform OCR on a particular file - modify the image is about to be
sent for OCR

How plugins are imported
========================

Plugins are imported on demand, by the OCRmyPDF worker process that
needs to use them. As such, plugins cannot share state with each other,
and will be imported many times, once for each worker process.

Plugins currently cannot override the same hook.

How plugins are invoked
=======================

Plugins may be called from the command line:
