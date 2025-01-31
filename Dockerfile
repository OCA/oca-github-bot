FROM ubuntu:24.04
LABEL maintainer="Odoo Community Association (OCA)"

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive

ARG PY=3.12

# binutils is needed for the ar command, used by pypandoc.ensure_pandoc_installed()
RUN set -x \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    binutils \
    ca-certificates \
    curl \
    git \
    python${PY}-venv \
    rsync \
    openssh-client \
  && rm -rf /var/lib/apt/lists/*

# The main branch bot needs several other command line tools from in OCA/maintainer-tools
# we install them in a separate virtualenv to avoid polluting our main environment.

# Other oca maintainer tools that are less sensitive to changes. The README generator is
# not as sensitive as before because it now stores a hash of the fragments in the
# generated README.rst, so it will only regenerate if the fragments have changed.
RUN set -x \
  && python${PY} -m venv /ocamt \
  && /ocamt/bin/pip install --no-cache-dir -U pip wheel
RUN set -x \
  && /ocamt/bin/pip install --no-cache-dir -e git+https://github.com/OCA/maintainer-tools@fbdc8945feabe1f6f3091c1b2d517b6c4160bc2b#egg=oca-maintainers-tools \
  && ln -s /ocamt/bin/oca-gen-addons-table /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-gen-addon-readme /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-gen-addon-icon /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-gen-metapackage /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-towncrier /usr/local/bin/ \
  && ln -s /ocamt/bin/setuptools-odoo-make-default /usr/local/bin/ \
  && ln -s /ocamt/bin/whool /usr/local/bin

# isolate from system python libraries
RUN set -x \
  && python${PY} -m venv /app \
  && /app/bin/pip install --no-cache-dir -U pip wheel
ENV PATH=/app/bin:$PATH

# install oca_github_bot dependencies, in a separate layer for improved caching
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# install oca_github_bot app
COPY . /app/src/oca-github-bot
RUN pip install --no-cache-dir -e /app/src/oca-github-bot

# make work and home directory
RUN mkdir /app/run && chmod ogu+rwx /app/run
ENV HOME=/app/run
WORKDIR /app/run
