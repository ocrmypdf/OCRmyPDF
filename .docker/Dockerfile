# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

FROM ubuntu:24.04 AS base

ENV LANG=C.UTF-8
ENV TZ=UTC
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
  python3 \
  python-is-python3

FROM base AS builder

# Note we need leptonica here to build jbig2
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential autoconf automake libtool \
  libleptonica-dev \
  zlib1g-dev \
  libffi-dev \
  ca-certificates \
  curl \
  git \
  libcairo2-dev \
  pkg-config

# Compile and install jbig2
# Needs libleptonica-dev, zlib1g-dev
RUN \
  mkdir jbig2 \
  && curl -L https://github.com/agl/jbig2enc/archive/c0141bf.tar.gz | \
  tar xz -C jbig2 --strip-components=1 \
  && cd jbig2 \
  && ./autogen.sh && ./configure && make && make install \
  && cd .. \
  && rm -rf jbig2

COPY . /app

WORKDIR /app

RUN curl -LsSf https://astral.sh/uv/0.4.27/install.sh | sh

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Instead of restarting the shell, use uv directly from its installed location.
RUN /root/.cargo/bin/uv sync --extra test --extra webservice --extra watcher

FROM base

RUN apt-get update && apt-get install -y software-properties-common

RUN add-apt-repository -y ppa:alex-p/tesseract-ocr-devel

RUN apt-get update && apt-get install -y --no-install-recommends \
  ghostscript \
  fonts-droid-fallback \
  jbig2dec \
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

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:${PATH}"

ENTRYPOINT ["/app/.venv/bin/ocrmypdf"]

