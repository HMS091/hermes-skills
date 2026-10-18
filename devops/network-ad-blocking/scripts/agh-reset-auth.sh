#!/bin/sh
# AdGuard Home: disable web auth (users: []) so the owner can set a new password.
#
# Use when the dashboard password is lost and there is no shell credential:
# run it as root on the host (Synology: Control Panel -> Task Scheduler ->
# Create -> Scheduled Task -> User-defined script, user = root).
#
# Output goes to $1 (default /tmp/agh-reset.txt) because Task Scheduler does not
# show stdout; have the user open that file in File Station afterwards.
#
# users: [] == authentication disabled (AdGuard Home wiki). Everything else in
# the YAML is preserved. Backup + health check + automatic rollback included.

OUT=${1:-/tmp/agh-reset.txt}
exec >"$OUT" 2>&1

echo "== AdGuard Home auth reset $(date) =="

DOCKER=$(command -v docker 2>/dev/null || echo /usr/local/bin/docker)

CONF=$(find /volume1/docker /volume1/@docker /var/packages /opt/adguardhome -name 'AdGuardHome.yaml' 2>/dev/null | head -n1)
if [ -z "$CONF" ]; then
  echo "FAIL: AdGuardHome.yaml not found in the usual places."
  echo "Ask the user for the container's mounted conf dir (docker inspect <name> | grep -i source)."
  exit 1
fi
echo "conf: $CONF"

BAK="$CONF.bak.$(date +%Y%m%d%H%M%S)"
cp -a "$CONF" "$BAK" || { echo "FAIL: backup"; exit 1; }
echo "backup: $BAK"

# Collapse the users: block into users: [] keeping its indentation.
awk '{ if ($0 ~ /^[[:space:]]*users:[[:space:]]*$/) { i=index($0,"u")-1; print substr($0,1,i) "users: []"; skip=1; next }
       if (skip) { if ($0 ~ /^[[:space:]]*$/) next; match($0,/^[[:space:]]*/); if (RLENGTH <= i) skip=0; else next }
       print }' "$BAK" > "$CONF.new"
if [ ! -s "$CONF.new" ]; then
  echo "FAIL: rewrite produced empty file, config untouched"; rm -f "$CONF.new"; exit 1
fi
mv "$CONF.new" "$CONF" || { echo "FAIL: replace"; cp -a "$BAK" "$CONF"; exit 1; }
echo "users -> []"

C=$($DOCKER ps --format '{{.Names}}' 2>/dev/null | grep -iE 'adguard')
if [ -n "$C" ]; then
  for n in $C; do $DOCKER restart "$n" >/dev/null && echo "restarted container: $n"; done
elif command -v synopkg >/dev/null 2>&1; then
  synopkg restart AdGuardHome >/dev/null && echo "restarted package: AdGuardHome"
else
  echo "WARN: no adguard container/package found — restart it manually"
fi

sleep 6
# /control/status: 200 = auth off, 403 = still required. `/` returns 200 either way.
if curl -sf -o /dev/null --max-time 5 http://127.0.0.1:3000/control/status; then
  echo "OK: open http://<nas-ip>:3000 — no login — Settings -> General -> set a new password"
else
  echo "FAIL: panel did not answer without auth, rolling back"
  cp -a "$BAK" "$CONF"
  for n in $C; do $DOCKER restart "$n" >/dev/null 2>&1; done
  exit 1
fi
