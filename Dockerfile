FROM ubuntu:18.04
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

# the main branch bot needs several command line tools from in OCA/maintainer-tools
# we install them in a separate virtualenv to avoid polluting our main environment
RUN set -x \
  && python3 -m venv /ocamt \
  && /ocamt/bin/pip install --no-cache-dir wheel
RUN set -x \
  && /ocamt/bin/pip install --no-cache-dir -e git+https://github.com/OCA/maintainer-tools@73c47b6835bee3ab0eeeff7c463de6b9c085abbc#egg=oca-maintainers-tools \
  && ln -s /ocamt/bin/oca-gen-addons-table /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-gen-addon-readme /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-gen-addon-icon /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-towncrier /usr/local/bin/
RUN set -x \
  && /ocamt/bin/pip install --no-cache-dir 'setuptools-odoo>=2.5.0' \
  && ln -s /ocamt/bin/setuptools-odoo-make-default /usr/local/bin/

# isolate from system python libraries
RUN python3 -m venv /app
ENV PATH=/app/bin:$PATH

# install oca_github_bot app
COPY . /app/src/oca-github-bot
RUN pip install --no-cache-dir -r /app/src/oca-github-bot/requirements.txt -e /app/src/oca-github-bot

# make work and home directory
RUN mkdir /app/run && chmod ogu+rwx /app/run
ENV HOME=/app/run
WORKDIR /app/run
