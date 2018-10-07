#!/bin/bash
set -Eeuxo pipefail

apt-get clean
rm -rf /var/lib/apt/lists/* /root/.cache/pip/*
