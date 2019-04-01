FROM ubuntu:18.04
LABEL maintainer="Odoo Community Association (OCA)"

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

COPY ./container/install /tmp/install
RUN set -x \
  && /tmp/install/pre-install.sh \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    python3-venv \
  && /tmp/install/gosu.sh \
  && /tmp/install/post-install-clean.sh \
  && rm -r /tmp/install

# the main branch bot needs several command line tools from in OCA/maintainer-tools
# we install them in a separate virtualenv to avoid polluting our main environment
RUN set -x \
  && python3 -m venv /ocamt \
  && /ocamt/bin/pip install wheel
RUN set -x \
  && /ocamt/bin/pip install git+https://github.com/OCA/maintainer-tools@d9e2c3b8dc163c8d0fcdd36278b782074c3cff12 \
  && ln -s /ocamt/bin/oca-gen-addons-table /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-gen-addon-readme /usr/local/bin/ \
  && ln -s /ocamt/bin/oca-gen-addon-icon /usr/local/bin/
RUN set -x \
  && /ocamt/bin/pip install setuptools-odoo>=2.4.1 \
  && ln -s /ocamt/bin/setuptools-odoo-make-default /usr/local/bin/


# isolate from system python libraries
RUN python3 -m venv /app
ENV PATH=/app/bin:$PATH

RUN mkdir /app/tmp
COPY ./requirements.txt /app/tmp
RUN pip install --no-cache-dir -r /app/tmp/requirements.txt
COPY . /app/tmp
RUN pip install /app/tmp && rm -fr /app/tmp

COPY ./container/entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
