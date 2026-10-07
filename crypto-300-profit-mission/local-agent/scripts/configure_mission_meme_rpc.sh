#!/bin/bash
set -euo pipefail

APP_SUPPORT="${APP_SUPPORT:-$HOME/Library/Application Support/FrankMeme}"
RPC_FILE="$APP_SUPPORT/solana_rpc_urls"

mkdir -p "$APP_SUPPORT"
chmod 700 "$APP_SUPPORT"

if [ -n "${SOLANA_RPC_URLS:-}" ]; then
  VALUE="$SOLANA_RPC_URLS"
else
  read -r -s -p "Paste authenticated Solana RPC HTTPS endpoint (or comma-separated endpoints): " VALUE
  echo
fi

VALUE="${VALUE//$'\r'/}"
VALUE="${VALUE//$'\n'/}"
[ -n "$VALUE" ] || { echo "ERROR: SOLANA_RPC_URLS_EMPTY" >&2; exit 1; }

IFS=',' read -r -a ENDPOINTS <<< "$VALUE"
[ "${#ENDPOINTS[@]}" -ge 1 ] || { echo "ERROR: SOLANA_RPC_URLS_EMPTY" >&2; exit 1; }

for endpoint in "${ENDPOINTS[@]}"; do
  [[ "$endpoint" == https://* ]] || {
    echo "ERROR: RPC_ENDPOINT_MUST_USE_HTTPS" >&2
    exit 1
  }
  [[ "$endpoint" != *[[:space:]]* ]] || {
    echo "ERROR: RPC_ENDPOINT_CONTAINS_WHITESPACE" >&2
    exit 1
  }
done

umask 077
TMP="$RPC_FILE.tmp.$$"
trap 'rm -f "$TMP"' EXIT
printf '%s\n' "$VALUE" > "$TMP"
chmod 600 "$TMP"
mv "$TMP" "$RPC_FILE"
trap - EXIT

echo "Authenticated Solana RPC: CONFIGURED"
echo "Stored at: $RPC_FILE"
echo "Permissions: $(stat -f '%Lp' "$RPC_FILE" 2>/dev/null || echo UNKNOWN)"
echo "Secret value: NOT PRINTED"
