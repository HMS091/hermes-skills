# TP-LINK TL-ER6229GPE-AC admin UI notes (main router 192.168.1.2)

Environment facts verified 2026-08:
- Main router is **TP-LINK TL-ER6229GPE-AC** (普联技术, "双核多WAN口PoE·AC一体化千兆路由器"), NOT Tenda.
  The earlier "Tenda/SLP framework" guess was wrong — TP-LINK (Shenzhen) uses the same SLP-style web framework.
- Admin UI: `http://192.168.1.2:9000` (HTTP, port **9000**; port 80 answers nothing, 443 has a self-signed cert but the UI is on 9000).
- Login: username `tl` (user-provided password). Note the user gave `tl / 123123` for this box.
- WAN1 is PPPoE dial; WAN IPv6 = `240e:398:ba01:fa40:7cb5:9b65:98e0:40da`-style prefix (China Telecom).

## Why automation fails (learned the hard way)
The UI is a JS shell (iframe content area + JS menu handlers, URLs like
`http://192.168.1.2:9000/stok=<session-token>/userrpm/<page>.htm`).
- cua-driver UIA element clicks: menu ListItems expose no invoke action.
- cua-driver coordinate clicks (background PostMessage AND foreground SendInput): do not register on the left menu (页面 stayed on 云管理).
- Direct URL navigation to `userrpm/ipv6.htm` etc. via address bar: ignored (page loads through menu JS, direct .htm GETs don't switch the iframe).
- `query_dom` (UIA backend) only sees the outer shell; menu sub-entries render only after the menu JS runs, which automation can't trigger.
**Conclusion: hand mouse actions to the user** ("click 传输控制 on the left sidebar, tell me what expands"), then read the resulting DOM.

## Menu map (left sidebar, top→bottom)
运行状态 / 基本设置 / 对象管理 / AP管理 / 易展设备管理 / **传输控制** / 安全管理 / 行为管控 / VPN / 安全审计 / 认证管理 / 系统服务 / 系统工具
- **IPv6 config confirmed under 基本设置** (NOT 传输控制):
  - 基本设置 → **接口设置**: 右侧 IP协议类型 有 IPv4/IPv6 单选；IPv6 模式 = 状态启用 + 地址配置方式 EUI-64/手动 + 前缀授权接口 WAN1（自动填公网前缀 `240e:39e:396:6520::`，LAN IPv6 地址按 MAC EUI-64 自动生成）。保存后网络短暂中断属正常。
  - 基本设置 → **LAN设置** → **SLAAC**: 新增条目（服务接口 LAN1、IPv6地址前缀留空=默认用路由器前缀、DNS配置方式 DHCPv6、状态启用）→ 确定。这是让路由器向 LAN 通告公网前缀的关键一步。
  - 另有 LAN设置 → DHCPv6服务 / IPv6客户端列表 / IPv6静态地址分配。
- 传输控制 子菜单只有 NAT设置/带宽控制/连接数限制/流量均衡/路由设置（没有 IPv6）。
- 登录 `tl / 123123`；WAN1 PPPoE 拨号；LAN IPv6 默认关，需在接口设置手动启用。
- 用户不懂技术 → 让用户用鼠标点菜单，agent 用 cua-driver page get_text 读结果（自动点击在此界面无效，见上）。
