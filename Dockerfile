FROM ubuntu:18.04
MAINTAINER Odoo Community Association (OCA)

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

# isolate from system python libraries
RUN python3 -m venv /app
ENV PATH=/app/bin:$PATH

RUN mkdir /app/tmp
COPY requirements.txt /app/tmp
RUN pip install --no-cache-dir -r /app/tmp/requirements.txt
COPY . /app/tmp
RUN pip install -e /app/tmp

COPY ./container/entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
