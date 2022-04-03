FROM ubuntu:20.04
LABEL maintainer="Odoo Community Association (OCA)"

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive

RUN set -x \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    python3-venv \
    rsync \
    openssh-client \
  && rm -rf /var/lib/apt/lists/*

# The main branch bot needs several other command line tools from in OCA/maintainer-tools
# we install them in a separate virtualenv to avoid polluting our main environment.

# Install a specific version of readme and icon generator, to ensure stability
# as any tiny change in generated output may create many commits on all addons.
# TODO: this particular version of maintainer tool does not install with
# the latest pip version due to https://github.com/OCA/maintainer-tools/pull/483
# so we don't upgrade pip. Be careful when changing this as it will regenerate
# all html readmes.
RUN set -x \
  && python3 -m venv /ocamt-readme \
  && /ocamt-readme/bin/pip install --no-cache-dir -U wheel
RUN set -x \
  && /ocamt-readme/bin/pip install --no-cache-dir -e git+https://github.com/OCA/maintainer-tools@73c47b6835bee3ab0eeeff7c463de6b9c085abbc#egg=oca-maintainers-tools \
  && ln -s /ocamt-readme/bin/oca-gen-addon-readme /usr/local/bin/ \
  && ln -s /ocamt-readme/bin/oca-gen-addon-icon /usr/local/bin/

# Other oca maintainer tools that are less sensitive to changes
RUN set -x \
  && python3 -m venv /ocamt \
  && /ocamt/bin/pip install --no-cache-dir -U pip wheel
RUN set -x \
  && /ocamt/bin/pip install --no-cache-dir -e git+https://github.com/OCA/maintainer-tools@7214f9584abebfc503968547d06a2c9377a083b9#egg=oca-maintainers-tools \
  && ln -s /ocamt/bin/oca-gen-addons-table /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-towncrier /usr/local/bin/
RUN set -x \
  && /ocamt/bin/pip install --no-cache-dir 'setuptools-odoo>=3.0.3' \
  && ln -s /ocamt/bin/setuptools-odoo-make-default /usr/local/bin/

# isolate from system python libraries
RUN set -x \
  && python3 -m venv /app \
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
