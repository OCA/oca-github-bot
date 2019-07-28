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
  && apt-get clean

# the main branch bot needs several command line tools from in OCA/maintainer-tools
# we install them in a separate virtualenv to avoid polluting our main environment
RUN set -x \
  && python3 -m venv /ocamt \
  && /ocamt/bin/pip install wheel
RUN set -x \
  && /ocamt/bin/pip install -e git+https://github.com/OCA/maintainer-tools@df806218edff4a8533201e29e2815e100df29c65#egg=oca-maintainers-tools \
  && ln -s /ocamt/bin/oca-gen-addons-table /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-gen-addon-readme /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-gen-addon-icon /usr/local/bin/
RUN set -x \
  && /ocamt/bin/pip install setuptools-odoo>=2.4.1 \
  && ln -s /ocamt/bin/setuptools-odoo-make-default /usr/local/bin/


# isolate from system python libraries
RUN python3 -m venv /app
ENV PATH=/app/bin:$PATH

# install oca_github_bot app
RUN mkdir /app/tmp
COPY ./requirements.txt /app/tmp
RUN pip install --no-cache-dir -r /app/tmp/requirements.txt
COPY . /app/tmp
RUN pip install /app/tmp && rm -fr /app/tmp

# make work and home directory
RUN mkdir /app/run && chmod ogu+rwx /app/run
ENV HOME=/app/run
WORKDIR /app/run

# run as non-root
USER 1000
