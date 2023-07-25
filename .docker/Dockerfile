# SPDX-FileCopyrightText: 2022 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

FROM ubuntu:22.04 as base

ENV LANG=C.UTF-8
ENV TZ=UTC
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
  python3 \
  libqpdf-dev \
  zlib1g \
  liblept5

FROM base as builder

# Note we need leptonica here to build jbig2
RUN apt-get update && apt-get install -y --no-install-recommends \
  python3-dev \
  python3-distutils \
  ca-certificates \
  curl \
  git \
  libcairo2-dev \
  pkg-config

# Get the latest pip
RUN curl https://bootstrap.pypa.io/get-pip.py | python3

COPY . /app

WORKDIR /app

RUN pip3 install --no-cache-dir .[test,webservice,watcher]

FROM base

# For Tesseract 5
RUN apt-get update && apt-get install -y --no-install-recommends \
  software-properties-common gpg-agent
RUN add-apt-repository -y ppa:alex-p/tesseract-ocr-devel
RUN add-apt-repository -y ppa:alex-p/jbig2enc

RUN apt-get update && apt-get install -y --no-install-recommends \
  ghostscript \
  fonts-droid-fallback \
  jbig2dec \
  jbig2enc \
  img2pdf \
  libsm6 libxext6 libxrender-dev \
  pngquant \
  tesseract-ocr \
  tesseract-ocr-chi-sim \
  tesseract-ocr-deu \
  tesseract-ocr-eng \
  tesseract-ocr-fra \
  tesseract-ocr-por \
  tesseract-ocr-spa \
  unpaper \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/ /usr/local/lib/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY --from=builder /app/misc/webservice.py /app/
COPY --from=builder /app/misc/watcher.py /app/

# Copy minimal project files to get the test suite.
COPY --from=builder /app/pyproject.toml /app/README.md /app/
COPY --from=builder /app/tests /app/tests

ENTRYPOINT ["/usr/local/bin/ocrmypdf"]
