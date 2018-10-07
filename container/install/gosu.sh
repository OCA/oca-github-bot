#!/bin/bash
set -Eeuxo pipefail

pushd /usr/local/bin
curl -o gosu -SL "https://github.com/tianon/gosu/releases/download/1.10/gosu-amd64"
echo '5b3b03713a888cee84ecbf4582b21ac9fd46c3d935ff2d7ea25dd5055d302d3c  gosu' | sha256sum -c -
chmod +x gosu
popd

# verify that the binary works
gosu nobody true
