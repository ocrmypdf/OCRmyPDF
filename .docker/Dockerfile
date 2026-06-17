# SPDX-FileCopyrightText: 2024 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

FROM ubuntu:26.04 AS base

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


WORKDIR /app

# Copy uv from ghcr
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen \
        --extra webservice --extra watcher --no-dev \
        --no-install-package pyarrow

FROM base

# Tesseract 5 ships in the Ubuntu archive as of 24.04, so no third-party PPA is
# needed. (Previously this used ppa:alex-p/tesseract-ocr5.)
RUN apt-get update && apt-get install -y --no-install-recommends \
  ghostscript \
  fonts-droid-fallback \
  fonts-noto-core \
  fonts-noto-cjk \
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

# Create a non-root user to run the application (defense in depth). The build
# stages above need root to install packages, but the entrypoint should not.
# A fixed uid/gid of 1000 keeps `--user`/`--userns keep-id` mappings predictable
# and matches the --chown below. See docs/docker.md for the volume/permissions
# implications under rootless vs rootful Docker.
# The Ubuntu base ships a default "ubuntu" user at uid/gid 1000; remove it so
# "app" can claim that uid for parity with the Alpine image.
RUN userdel -r ubuntu 2>/dev/null; groupdel ubuntu 2>/dev/null; \
  groupadd -g 1000 app \
  && useradd -u 1000 -g app -m -d /home/app app
ENV HOME=/home/app

WORKDIR /app

COPY --from=builder /usr/local/lib/ /usr/local/lib/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY --from=builder --chown=app:app /app /app

RUN rm -rf /app/.git && \
ln -s /app/misc/webservice.py /app/webservice.py && \
ln -s /app/misc/watcher.py /app/watcher.py && \
chown app:app /app

# Default working directory for bind-mounted data, so relative input/output
# paths work without passing --workdir (e.g. `-v "$PWD:/data" in.pdf out.pdf`).
# The webservice/watcher are run by absolute path (/app/*.py), unaffected by this.
RUN mkdir -p /data && chown app:app /data
WORKDIR /data

ENV PATH="/app/.venv/bin:${PATH}"

# Drop privileges: run the entrypoint (ocrmypdf, or the webservice/watcher when
# overridden) as the unprivileged app user. Override with `--user root` if you
# need root inside a running container (e.g. to apt install extra packages).
USER app

ENTRYPOINT ["/app/.venv/bin/ocrmypdf"]

