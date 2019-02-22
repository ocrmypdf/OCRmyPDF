FROM python:3-alpine as base

FROM base as builder

RUN \
  echo '@testing http://nl.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories \
  # Add runtime dependencies
  && apk add --update \
    jbig2enc@testing \
    ghostscript \
    qpdf \
    tesseract-ocr \
    unpaper \
    pngquant \
    libxml2-dev \
    libxslt-dev \
    zlib-dev \
    qpdf-dev \
    libffi-dev \
    leptonica-dev \
    binutils \
  # Install pybind11 for pikepdf
  && pip install pybind11 \
  # Add build dependencies
  && apk add --virtual build-dependencies \
    build-base \
    git

COPY . /app

WORKDIR /app

RUN pip install .

FROM base

RUN \
  echo '@testing http://nl.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories \
  # Add runtime dependencies
  && apk add --update \
    jbig2enc@testing \
    ghostscript \
    qpdf \
    tesseract-ocr \
    unpaper \
    pngquant \
    libxml2 \
    libxslt \
    zlib \
    qpdf \
    libffi \
    leptonica-dev \
    binutils

COPY --from=builder /usr/local /usr/local

ENTRYPOINT ["/usr/local/bin/ocrmypdf"]
