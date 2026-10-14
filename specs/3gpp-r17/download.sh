#!/bin/bash
#
# Fetch the Rel-17 3GPP specs listed in README.md into this directory.
#
# The documents themselves are not committed: they are public, large
# (about 120 MB unpacked) and always reproducible from the 3GPP archive.
# The archive answers 403 to clients without a browser User-Agent.
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p zip

UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'
SPECS=(
  23228-h30 24229-hj0 23501-hf0 23502-hf0 23503-hb0 23003-hb0 24008-h90 24501-hi1
  29514-hg0 29513-he0 29214-h60 29228-h10 29229-h30 29562-ha0 29510-hg0 29505-hd0
  29519-hh0 29571-hd0 33203-h10 33102-h00 35206-h00 35208-h00
)

for f in "${SPECS[@]}"; do
  n=${f%%-*}
  series=${n:0:2}
  url="https://www.3gpp.org/ftp/Specs/archive/${series}_series/${series}.${n:2}/${f}.zip"
  if [ ! -f "zip/${f}.zip" ]; then
    curl -fsS -m 600 -A "$UA" -o "zip/${f}.zip" "$url"
  fi
  unzip -o -q "zip/${f}.zip" -d .
  echo "ok ${f}"
done
