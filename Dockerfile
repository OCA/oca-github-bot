FROM ubuntu:18.04
LABEL maintainer="Odoo Community Association (OCA)"

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    HOME=/opt/app/run \
    # Add the isolated oca_github_bot python libraries
    PATH=/opt/app/bin:$PATH

# Files for the installation of the oca_github_bot app
COPY ./requirements.txt /tmp
COPY . /tmp


RUN set -x \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
                                        ca-certificates \
                                        curl \
                                        git \
                                        python3-venv \
                                        rsync \
                                        openssh-client \
  # the main branch bot needs several command line tools from in OCA/maintainer-tools
  # we install them in a separate virtualenv to avoid polluting our main environment
  && python3 -m venv /opt/ocamt \
  && . /opt/ocamt/bin/activate \
  && pip install wheel \
  && pip install -e git+https://github.com/OCA/maintainer-tools@73c47b6835bee3ab0eeeff7c463de6b9c085abbc#egg=oca-maintainers-tools \
  && ln -s /opt/ocamt/bin/oca-gen-addons-table /usr/local/bin/ \
  && ln -s /opt/ocamt/bin/oca-gen-addon-readme /usr/local/bin/ \
  && ln -s /opt/ocamt/bin/oca-gen-addon-icon /usr/local/bin/ \
  && ln -s /opt/ocamt/bin/oca-towncrier /usr/local/bin/ \
  && pip install 'setuptools-odoo>=2.5.0' \
  && ln -s /opt/ocamt/bin/setuptools-odoo-make-default /usr/local/bin/ \
  && deactivate \
  # isolate from system python libraries
  && python3 -m venv /opt/app \
  # install oca_github_bot app
  && . /opt/app/bin/activate \
  && pip install --no-cache-dir -r /tmp/requirements.txt \
  && pip install /tmp \
  && deactivate \
  && rm -fr /tmp/* \
  # make work and home directory
  && chmod ogu+rwx /opt/app/run \
  # clean up
  && apt-get autoclean \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app/run
