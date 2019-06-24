# OCRmyPDF
#
FROM ubuntu:19.04 as base

FROM base as builder

ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential autoconf automake libtool \
  libleptonica-dev \
  zlib1g-dev \
  ocrmypdf \
  pngquant \
  python3-pip \
  python3-venv \
  tesseract-ocr \
  unpaper \
  wget \
  git


# Compile and install jbig2
# Needs libleptonica-dev, zlib1g-dev
RUN \
  mkdir jbig2 \
  && wget -q https://github.com/agl/jbig2enc/archive/0.29.tar.gz -O - | \
  tar xz -C jbig2 --strip-components=1 \
  && cd jbig2 \
  && ./autogen.sh && ./configure && make && make install \
  && cd .. \
  && rm -rf jbig2

RUN python3 -m venv /appenv

COPY . /app

WORKDIR /app

RUN . /appenv/bin/activate; \
  pip install --upgrade pip \
  && pip install .

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
  python3-venv \
  qpdf \
  tesseract-ocr \
  tesseract-ocr-chi-sim \
  tesseract-ocr-deu \
  tesseract-ocr-eng \
  tesseract-ocr-fra \
  tesseract-ocr-por \
  tesseract-ocr-spa \
  unpaper \
  wget

# Copy
COPY --from=builder /app/misc/webservice.py /app/

# Copy minimal project files to get the test suite.
COPY --from=builder /app/setup.cfg /app/setup.py /app/README.md /app/
COPY --from=builder /app/requirements /app/requirements
COPY --from=builder /app/tests /app/tests
COPY --from=builder /app/src /app/src

COPY --from=builder /appenv /appenv
COPY --from=builder /usr/local /usr/local

ENTRYPOINT ["/appenv/bin/ocrmypdf"]
