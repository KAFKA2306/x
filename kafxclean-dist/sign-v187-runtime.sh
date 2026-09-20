#!/bin/sh
set -eu

for name in ANDROID_KEYSTORE_BASE64 ANDROID_KEYSTORE_PASSWORD ANDROID_KEY_ALIAS ANDROID_KEY_PASSWORD; do
  eval "value=\${$name:-}"
  if [ -z "$value" ]; then
    echo "missing signing variable: $name" >&2
    exit 2
  fi
done

mkdir -p /srv
rm -f /srv/*
KEYSTORE=/tmp/release.keystore
ALIGNED=/tmp/KafXClean-v1.8.7-aligned.apk
printf '%s' "$ANDROID_KEYSTORE_BASE64" | base64 -d > "$KEYSTORE"
test -s "$KEYSTORE"

ZIPALIGN="${ANDROID_HOME}/build-tools/36.0.0/zipalign"
APKSIGNER="${ANDROID_HOME}/build-tools/36.0.0/apksigner"
test -x "$ZIPALIGN"
test -x "$APKSIGNER"

"$ZIPALIGN" -p -f 4 /unsigned/KafXClean-v1.8.7-unsigned.apk "$ALIGNED"
"$APKSIGNER" sign \
  --ks "$KEYSTORE" \
  --ks-pass env:ANDROID_KEYSTORE_PASSWORD \
  --ks-key-alias "$ANDROID_KEY_ALIAS" \
  --key-pass env:ANDROID_KEY_PASSWORD \
  --out /srv/KafXClean-v1.8.7.apk \
  "$ALIGNED"

"$APKSIGNER" verify --verbose --print-certs /srv/KafXClean-v1.8.7.apk | tee /srv/APKSIGNER.txt
cd /srv
sha256sum KafXClean-v1.8.7.apk > SHA256SUMS
sha256sum -c SHA256SUMS
cat > RELEASE_METADATA.txt <<'__META__'
product=KafXClean
version=1.8.7
tag=kafxclean-v1.8.7
source_sha=8fbe83e2554d1e1f5740dae5ee42aa7068aed7e1
__META__

rm -f "$KEYSTORE" "$ALIGNED"
echo "OK: signed KafXClean v1.8.7"
exec python3 -m http.server 8000 --bind 0.0.0.0 --directory /srv
