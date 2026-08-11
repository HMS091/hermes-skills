#!/bin/bash
# Nextcloud Talk 流量直连主路由（策略路由 - MARK 方案）
# 用途: NAS 默认路由走旁路由 88(代理)，仅 TURN/STUN 响应走主路由直连
# 用法: sudo bash /volume1/docker/talk-direct.sh   （或 DSM 任务计划以 root 运行，开机触发）
# 原理: coturn 响应包源端口固定(3478/3479/5349 + 中继段 49152-65535),
#       在 mangle OUTPUT 打 fwmark=1 -> ip rule 走路由表 100(主路由直连)
# 已验证: DSM 7.2 上 CONNMARK --set-mark / -m connmark / ip rule sport 均不可用,
#        但 iptables-legacy/ip6tables-legacy 的 -j MARK --set-mark 可用。
# 注意: 脚本会清空 mangle OUTPUT 链 - 执行前先确认该链无其他重要规则
#       (iptables-legacy -t mangle -L OUTPUT -n)。
# 注意: GW6 需与当前主路由 v6 链路本地地址一致 (ip -6 route show default 查看),
#       运营商重拨换前缀后主路由 link-local 不变, 但 coturn/Nextcloud 里硬编码的
#       v6 地址会失效, 需要另行更新。

GW4=192.168.1.2
GW6=fe80::7eb5:9bff:fee0:40d9
IF=ovs_eth0
TBL=100

echo "== 1/4 路由表 $TBL (经主路由) =="
ip route flush table $TBL 2>/dev/null
ip route add 192.168.1.0/24 dev $IF table $TBL
ip route add default via $GW4 dev $IF table $TBL
ip -6 route flush table $TBL 2>/dev/null
ip -6 route add default via $GW6 dev $IF table $TBL

echo "== 2/4 ip rule (fwmark 1 -> 表 $TBL) =="
ip rule del fwmark 1 table $TBL 2>/dev/null
ip rule add fwmark 1 table $TBL priority 1000
ip -6 rule del fwmark 1 table $TBL 2>/dev/null
ip -6 rule add fwmark 1 table $TBL priority 1000

echo "== 3/4 IPv4 标记规则 =="
iptables-legacy -t mangle -F OUTPUT 2>/dev/null
for p in udp tcp; do
  for d in 3478 3479 5349; do
    iptables-legacy -t mangle -A OUTPUT -p $p --sport $d -j MARK --set-mark 1
  done
done
iptables-legacy -t mangle -A OUTPUT -p udp --sport 49152:65535 -j MARK --set-mark 1

echo "== 4/4 IPv6 标记规则 =="
ip6tables-legacy -t mangle -F OUTPUT 2>/dev/null
for p in udp tcp; do
  for d in 3478 3479 5349; do
    ip6tables-legacy -t mangle -A OUTPUT -p $p --sport $d -j MARK --set-mark 1
  done
done
ip6tables-legacy -t mangle -A OUTPUT -p udp --sport 49152:65535 -j MARK --set-mark 1

echo "== 完成: TURN/STUN 响应将经 $GW4 / $GW6 直连 =="
