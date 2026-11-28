# AI/LLM 开源生态全景调查 (2026年6月)

> 按类别整理 >20,000 star 的 AI/LLM 相关开源项目。

## 1. Model Serving（模型推理服务）

| 项目 | Stars | 语言 | 说明 |
|------|-------|------|------|
| ollama/ollama | ~175k | Go | 本地LLM运行，支持多种模型 |
| nomic-ai/gpt4all | ~77.4k | C++ | 本地运行LLM，商业可用 |
| vllm-project/vllm | ~48k | Python | 高吞吐LLM推理引擎 |
| sgl-project/sglang | ~29.6k | Python | 高性能LLM+多模态推理框架 |
| ggml-org/llama.cpp | ~80k+ | C++ | 纯CPU/GPU推理 |

## 2. RAG / 知识库

| 项目 | Stars | 语言 | 说明 |
|------|-------|------|------|
| infiniflow/ragflow | ~83.6k | Go | 开源RAG引擎，融合Agent |
| Mintplex-Labs/anything-llm | ~62.1k | JavaScript | 全功能本地AI知识库 |
| pathwaycom/llm-app | ~59.2k | Python | RAG/企业搜索模板 |
| run-llama/llama_index | ~50.4k | Python | 文档Agent和OCR平台 |
| HKUDS/LightRAG | ~37k | Python | 轻量级RAG+知识图谱 |

## 3. Embedding / 向量数据库

| 项目 | Stars | 说明 |
|------|-------|------|
| meilisearch/meilisearch | ~58.3k | 极速搜索引擎，支持向量混合搜索 |
| milvus-io/milvus | ~33k+ | 最流行开源向量数据库 |
| qdrant/qdrant | ~25k+ | 高性能向量数据库 |

## 4. AI Agent 框架

| 项目 | Stars | 说明 |
|------|-------|------|
| Significant-Gravitas/AutoGPT | ~185k | 自主AI Agent先驱 |
| langchain-ai/langchain | ~140k | 最流行Agent工程平台 |
| firecrawl/firecrawl | ~139k | AI网页搜索/抓取API |
| langgenius/dify | ~50k+ | LLM应用开发平台 |

## 5. AI 编程助手

| 项目 | Stars | 说明 |
|------|-------|------|
| AntonOsika/gpt-engineer | ~55.2k | CLI代码生成平台 |
| TabbyML/tabby | ~33.7k | 自托管AI编程助手 |
| Pythagora-io/gpt-pilot | ~33.7k | AI全栈开发者 |

## 6. OCR / Document AI

| 项目 | Stars | 说明 |
|------|-------|------|
| PaddlePaddle/PaddleOCR | ~83.8k | 最强OCR工具包，100+语言 |
| tesseract-ocr/tesseract | ~74.9k | 经典OCR引擎 |
| opendatalab/MinerU | ~69.3k | PDF/Office→LLM就绪Markdown |
| hiroi-sora/Umi-OCR | ~45.5k | 开源离线OCR软件 |

## 7. Speech / 语音处理

| 项目 | Stars | 说明 |
|------|-------|------|
| ggml-org/whisper.cpp | ~51k | Whisper C++移植 |
| SYSTRAN/faster-whisper | ~23.8k | CTranslate2加速Whisper |
| m-bain/whisperX | ~22.7k | ASR+时间戳+说话人分离 |

## 8. 数据提取 / ETL

| 项目 | Stars | 说明 |
|------|-------|------|
| firecrawl/firecrawl | ~139k | AI网页抓取API |
| D4Vinci/Scrapling | ~66.1k | 自适应Web Scraping框架 |
| ScrapeGraphAI/Scrapegraph-ai | ~27.6k | AI驱动的网页爬虫 |

## 高优先级安装评估

推荐优先安装:
1. **RAGFlow** (83.6k⭐) — Docker部署, 增强Hermes知识库能力
2. **FireCrawl** (139k⭐) — Node.js, 网页数据搜索/抓取
3. **MinerU** (69.3k⭐) — pip install, PDF→Markdown批量文档解析
4. **SGLang** (29.6k⭐) — pip install, 替代vLLM的高性能推理
5. **AnythingLLM** (62.1k⭐) — Docker部署, 完整本地知识库前端

> 数据来源: GitHub Topics页 + GitHub API搜索 (2026年6月25日)
