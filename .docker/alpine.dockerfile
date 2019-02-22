FROM python:3-alpine

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
    leptonica-dev \
    libffi-dev \
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

# Delete build dependencies
RUN \
  rm -rf /app \
  && mkdir /app \
  && apk del build-dependencies \
  && rm -rf /var/cache/apk/* \
  && rm -rf /root/.cache

ENTRYPOINT ["/usr/local/bin/ocrmypdf"]
