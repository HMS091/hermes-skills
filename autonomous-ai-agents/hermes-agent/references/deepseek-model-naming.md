# DeepSeek Model Naming

## 背景

DeepSeek 不定期更新模型 ID，旧名字会从 API 中移除。  
典型报错：配置了 `model.default: deepseek-chat` 但 DeepSeek API 返回 404 / model not found。

## 当前可用模型（2026-06）

```
deepseek-v4-flash    ← 前身 deepseek-chat（对话/聊天模型）
deepseek-v4-pro      ← 前身 deepseek-reasoner（推理模型）
```

## 排查方法

```bash
# 1. 列出 DeepSeek API 当前所有可用模型
curl -s https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"

# 2. 检查本地配置中的模型名
grep "^model:" /opt/data/config.yaml

# 3. 修复配置（写对当前模型名）
hermes config set model.default deepseek-v4-flash
hermes config set model.provider deepseek
```

## 注意事项

- DeepSeek API 是 OpenAI 兼容格式，base_url 为 `https://api.deepseek.com/v1`
- 模型名变更不影响 API key，只需改 `config.yaml` 里的 `model.default`
- 改完后需要 `/reset` 新会话才生效（CLI 重启 / Dashboard 刷新）
- 对于使用 Hermes 配置文件直接修改的情况，配置文件路径见 `hermes config path`
