# OCRmyPDF
#
FROM ubuntu:19.10 as base

FROM base as builder

ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential autoconf automake libtool \
  libleptonica-dev \
  zlib1g-dev \
  python3 \
  python3-distutils \
  ca-certificates \
  curl \
  git

# Get the latest pip (Ubuntu version doesn't support manylinux2010)
RUN \
  curl https://bootstrap.pypa.io/get-pip.py | python3

# Compile and install jbig2
# Needs libleptonica-dev, zlib1g-dev
RUN \
  mkdir jbig2 \
  && curl -L https://github.com/agl/jbig2enc/archive/0.29.tar.gz | \
  tar xz -C jbig2 --strip-components=1 \
  && cd jbig2 \
  && ./autogen.sh && ./configure && make && make install \
  && cd .. \
  && rm -rf jbig2

COPY . /app

WORKDIR /app

RUN pip3 install --no-cache-dir \
  -r requirements/main.txt \
  -r requirements/webservice.txt \
  -r requirements/test.txt \
  -r requirements/watcher.txt \
  .

FROM base

ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
  ghostscript \
  img2pdf \
  liblept5 \
  libsm6 libxext6 libxrender-dev \
  zlib1g \
  pngquant \
  python3 \
  qpdf \
  tesseract-ocr \
  tesseract-ocr-chi-sim \
  tesseract-ocr-deu \
  tesseract-ocr-eng \
  tesseract-ocr-fra \
  tesseract-ocr-por \
  tesseract-ocr-spa \
  unpaper

WORKDIR /app

COPY --from=builder /usr/local/lib/ /usr/local/lib/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY --from=builder /app/misc/webservice.py /app/
COPY --from=builder /app/misc/watcher.py /app/

# Copy minimal project files to get the test suite.
COPY --from=builder /app/setup.cfg /app/setup.py /app/README.md /app/
COPY --from=builder /app/requirements /app/requirements
COPY --from=builder /app/tests /app/tests
COPY --from=builder /app/src /app/src

ENTRYPOINT ["/usr/local/bin/ocrmypdf"]
