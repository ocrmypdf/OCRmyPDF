FROM alpine:3.9 as base

FROM base as builder

ENV LANG=C.UTF-8

RUN \
  echo '@testing http://nl.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories \
  # Add runtime dependencies
  && apk add --update \
    python3-dev \
    py3-setuptools \
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
  && pip3 install pybind11 \
  # Install flask for the webservice
  && pip3 install flask \
  # Add build dependencies
  && apk add --virtual build-dependencies \
    build-base \
    git

COPY . /app

WORKDIR /app

RUN pip3 install .

FROM base

ENV LANG=C.UTF-8

RUN \
  echo '@testing http://nl.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories \
  # Add runtime dependencies
  && apk add --update \
    python3 \
    jbig2enc@testing \
    ghostscript \
    qpdf \
    tesseract-ocr \
    tesseract-ocr-data-deu \
    tesseract-ocr-data-chi_sim \
    unpaper \
    pngquant \
    libxml2 \
    libxslt \
    zlib \
    qpdf \
    libffi \
    leptonica-dev \
    binutils \
  && mkdir /app

WORKDIR /app

# Copy build artifacts (python site-packages9
COPY --from=builder /usr/lib/python3.6/site-packages /usr/lib/python3.6/site-packages
COPY --from=builder /usr/bin/ocrmypdf /usr/bin/dumppdf.py /usr/bin/latin2ascii.py /usr/bin/pdf2txt.py /usr/bin/img2pdf /usr/bin/chardetect /usr/bin/

# Copy
COPY --from=builder /app/.docker/webservice.py /app/

# Copy minimal project files to get the test suite.
COPY --from=builder /app/setup.cfg /app/setup.py /app/README.md /app/
COPY --from=builder /app/requirements /app/requirements
COPY --from=builder /app/tests /app/tests
COPY --from=builder /app/src /app/src
# Copy PKG-INFO from build artifact in app dir to make setuptools-scm happy
RUN cp /usr/lib/python3.6/site-packages/ocrmypdf-*.egg-info/PKG-INFO /app

ENTRYPOINT ["/usr/bin/ocrmypdf"]
