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

RUN apt-get update && apt-get install -y --no-install-recommends \
  python3-pip \
  python3-venv \
  git \
  curl

COPY . /app

WORKDIR /app

RUN curl -LsSf https://astral.sh/uv/0.4.27/install.sh | sh

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Instead of restarting the shell, use uv directly from its installed location.
RUN /root/.cargo/bin/uv sync --extra test --extra webservice --extra watcher

FROM base

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

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:${PATH}"

ENTRYPOINT ["/app/.venv/bin/ocrmypdf"]

