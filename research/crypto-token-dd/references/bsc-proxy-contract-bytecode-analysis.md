# BSC Proxy Contract Bytecode Analysis — Pro Token (PRO) Case Study

## Session Context

Two EIP-1967 UUPS proxy contracts appeared as the #1 and #2 holders on BscScan for Pro Token (PRO), claiming 50.62% and 14.51% ownership. This reference documents how they were identified and what they revealed.

## Wallets Analyzed

| Rank | Address | Claimed % | Type | Admin Address |
|------|---------|-----------|------|---------------|
| #1 | `0xc0021e0849fadefb98761f40829009905dbd8ee8` | 50.62% | EIP-1967 UUPS Proxy | `0xd78d4a09e00a54ac9787ecbbeca02791336c75b3` |
| #2 | `0x9b68c219dbcc09eba7ca470eabb28a38daecbccc` | 14.51% | EIP-1967 UUPS Proxy | `0x27d4743f242c06e5a47113c1b136c5dc0e068d7b` |

## Technique: Identifying EIP-1967 UUPS Proxy via Bytecode

### Step 1: Check if address is a contract or EOA

```bash
curl -s -X POST "$BSC_RPC" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["<ADDRESS>", "latest"],"id":1}'
```

If `result` is `0x` followed by > 10 hex chars, it's a contract. Otherwise EOA.

### Step 2: Analyze bytecode structure

EIP-1967 UUPS proxy bytecode (761 bytes) has these signatures:

```
60806040  → Solidity preamble (PUSH1 0x80, PUSH1 0x40, MSTORE)
```

**Permission check (hardcoded admin):**
```
6080604052337f000000000000000000000000<ADMIN_ADDRESS_40_HEX>...
```
Where `7f` = PUSH32 followed by the whitelisted caller address. The real address is the last 20 bytes (40 hex chars) of the PUSH32.

**Function selectors present:**
```
0x278f7943 → uniswapV2SwapCall(address,uint256,uint256,bytes)
0x34ad5dbb → uniswapV2Pair()
0xd6bda275 → _mint(address,uint256)
```

**EIP-1967 storage slot (always present):**
```
360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc
```
This slot stores the **logic contract address** that can be upgraded.

**Solidity compiler footer:**
```
64736f6c634300081e0033  → solc 0.8.30 (736f6c63 = 'solc')
```

### Step 3: Compare bytecodes between proxy contracts

```python
code1 = "6080604052337f000000000000000000000000d78d4..."  # full hex
code2 = "6080604052337f00000000000000000000000027d47..."  # full hex

# Extract admin address
idx1 = code1.index('7f') + 2
admin1 = '0x' + code1[idx1+24:idx1+64][-40:]
idx2 = code2.index('7f') + 2  
admin2 = '0x' + code2[idx2+24:idx2+64][-40:]

# Identical bytecode except admin address?
# Compare everything except the 40-hex admin at position after 7f
```

### Step 4: Extract the admin address

```python
code_hex = "6080604052337f..."  # full bytecode from eth_getCode
idx = code_hex.index('7f') + 2  # PUSH32 starts here
push32_data = code_hex[idx:idx+64]  # 64 hex = 32 bytes
admin = '0x' + push32_data[-40:]   # last 20 bytes
print(f"Admin: {admin}")
```

### Step 5: Cross-check with balanceOf() (see honeypot detection ref)

Both proxy contracts also had fake balanceOf() returns:
- Claimed 2,010,000 PRO and 578,990 PRO respectively
- Actual `balanceOf()` via RPC: 0.0020 and 0.0013 PRO
- Zero Transfer events for either wallet

## Pattern: Same-Template Proxy Deployment

When two proxy contracts on the same token have:
- Identical bytecode (except admin address)
- Same function selectors  
- Same EIP-1967 storage slot
- Same solc version footer

They were deployed from the **same factory contract** by the same project team. Each has a different admin, but both admins likely point to the same operator.

## Key Takeaways for Due Diligence

1. **"Top holders" that are proxy contracts** → the actual tokens are controlled by the admin address, not the proxy itself
2. **Multiple same-template proxies in top 10** → project team is concentrating supply under multiple identities
3. **Proxy contracts with uniswapV2SwapCall** → flash-loan capable, used for liquidity manipulation
4. **Proxy + fake balanceOf()** → definitive honeypot. The proxy is either: holding minted tokens in a shadow contract, or the balanceOf is faked entirely
5. **Always check: is the "top holder" a contract or an EOA?** If it's a contract, ask: what type? Can it be upgraded? Who controls it?
