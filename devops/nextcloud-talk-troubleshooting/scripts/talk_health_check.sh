#!/bin/bash
# Read-only health check for the NAS Nextcloud Talk stack.
# Run ON the NAS (e.g. `cat talk_health_check.sh | ssh tmm@192.168.1.200 'bash -s'`).
# Answers: is the instance alive, does it have its Redis, is TURN/STUN sane,
# does the public hostname point at the CURRENT address, is the path reachable from outside.
# Safe to re-run: it only reads config, runs STUN/allocation probes and one external fetch.
set -u
D=/usr/local/bin/docker
OCC="$D exec -u www-data nextcloud php occ"
V6=$(ip -6 addr show scope global 2>/dev/null | awk '/inet6/{print $2}' | cut -d/ -f1 | head -1)
STATUS=0
say() { printf '\n=== %s\n' "$1"; }

say "containers (nextcloud / redis / coturn / signaling)"
$D ps -a --format '{{.Names}}|{{.Status}}' | grep -Ei 'nextcloud|redis|coturn|signaling' | sort

say "redis dependency from config.php"
REDISHOST=$($D exec nextcloud sh -c "grep -A3 \"'redis'\" /var/www/html/config/config.php | awk -F\"'\" '/host/{print \$4}'" 2>/dev/null)
echo "redis host = ${REDISHOST:-<none>}"
if [ -n "$REDISHOST" ]; then
  RSTATE=$($D ps -a --format '{{.Names}}|{{.Status}}' | grep "^${REDISHOST}|" || echo "$REDISHOST|MISSING")
  echo "$RSTATE"
  case "$RSTATE" in *Exited*|*MISSING*) echo "!! Nextcloud's Redis is DOWN -> this alone breaks Talk. Start it and decouple."; STATUS=1;; esac
  $D exec nextcloud php -r "\$r=new Redis(); \$r->connect('$REDISHOST',6379,3); echo 'PING='.\$r->ping().PHP_EOL;" 2>&1 | tail -1
fi

say "occ + Talk ICE config"
$OCC status 2>&1 | head -3
$OCC talk:turn:list 2>&1 | tail -8
$OCC talk:stun:list 2>&1 | tail -4
$OCC config:app:get spreed stun_servers 2>&1 | tail -1

say "coturn listeners (need v4 AND v6: :::3478 tcp + udp6)"
netstat -tuln 2>/dev/null | awk '$4 ~ /:(3478|3479)$/ {print $1, $4}' | sort -u

if [ -n "$V6" ]; then
  say "coturn STUN probes (v4 LAN + v6 global $V6)"
  timeout 12 $D exec talk-coturn turnutils_stunclient -p 3478 192.168.1.200 2>&1 | tail -1
  timeout 12 $D exec talk-coturn turnutils_stunclient -p 3478 "$V6" 2>&1 | tail -1
  say "TURN allocation (judge by the coturn log line, NOT by uclient loss stats)"
  SEC=$($D exec nextcloud_db sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -N -B nextcloud -e "select configvalue from oc_appconfig where appid=0x737072656564 and configkey=0x7475726e5f73657276657273"' 2>/dev/null | python3 -c 'import sys,json;
d=json.loads(sys.stdin.read() or "[]");
print(d[0].get("secret","") if d else "")' 2>/dev/null)
  if [ -n "$SEC" ]; then
    timeout 25 $D exec talk-coturn turnutils_uclient -W "$SEC" -e 8.8.8.8 -p 3478 -n 2 "$V6" >/dev/null 2>&1
    $D logs --tail 200 talk-coturn 2>&1 | grep -E 'ALLOCATE processed, success|Local relay addr' | tail -3
  else
    echo "(no secret in turn_servers -> username/password mode or unset; skip allocation probe)"
  fi
fi

say "hostname vs live address"
for dom in tmmddsm.myds.me nextcloud.skyforgelabs.qzz.io; do
  ANS=$(nslookup "$dom" 8.8.8.8 2>/dev/null | awk '/^Address/{a=$2} END{print a}')
  echo "$dom -> ${ANS:-<no answer>}"
  [ -n "$V6" ] && [ "$ANS" != "$V6" ] && echo "!! differs from live $V6 (stale DDNS record?) -> fix in DSM, see synology-nas-remote-ops"
done

say "external reachability (public fetch proxy)"
curl -s --max-time 45 "https://r.jina.ai/https://tmmddsm.myds.me:9800/status.php" 2>&1 | tail -c 300
echo
exit $STATUS
