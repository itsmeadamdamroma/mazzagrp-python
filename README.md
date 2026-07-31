<div align="center">

# mazzagrp-python

<h3>The Python SDK for mazzagrp.com AI APIs — 21 endpoints, x402 USDC micropayments, zero API keys</h3>

<p>Agents can't sign up for accounts. Agents can't enter credit cards.<br>
Agents can only sign transactions.<br><br>
<strong>mazzagrp-python is the only AI API SDK that lets autonomous agents pay-per-request with crypto.</strong></p>

<br>

<img src="https://img.shields.io/badge/🤖_21_AI_Endpoints-blue?style=for-the-badge" alt="21 AI endpoints">&nbsp;
<img src="https://img.shields.io/badge/🔑_Zero_API_Keys-success?style=for-the-badge" alt="Zero API keys">&nbsp;
<img src="https://img.shields.io/badge/⚡_x402_Protocol-purple?style=for-the-badge" alt="x402 protocol">&nbsp;
<img src="https://img.shields.io/badge/💰_USDC_on_Base-0052FF?style=for-the-badge&logo=coinbase&logoColor=white" alt="USDC on Base">&nbsp;
<img src="https://img.shields.io/badge/🐍_Python_3.9+-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+">&nbsp;
<img src="https://img.shields.io/badge/🔓_MIT_License-green?style=for-the-badge" alt="MIT license">

<br>

[![PyPI version](https://img.shields.io/pypi/v/mazzagrp.svg?style=flat-square&color=blue)](https://pypi.org/project/mazzagrp/)
[![PyPI downloads](https://img.shields.io/pypi/dm/mazzagrp.svg?style=flat-square&color=blue)](https://pypi.org/project/mazzagrp/)
[![GitHub stars](https://img.shields.io/github/stars/itsmeadamdamroma/mazzagrp-python?style=flat-square)](https://github.com/itsmeadamdamroma/mazzagrp-python)
[![CI](https://img.shields.io/github/actions/workflow/status/itsmeadamdamroma/mazzagrp-python/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/itsmeadamdamroma/mazzagrp-python/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![x402 Protocol](https://img.shields.io/badge/x402-Micropayments-purple?style=flat-square)](https://x402.org)
[![Base Network](https://img.shields.io/badge/Base-USDC-0052FF?style=flat-square&logo=coinbase&logoColor=white)](https://base.org)

</div>

> **mazzagrp-python** is the official Python SDK for [mazzagrp.com](https://mazzagrp.com) AI APIs. It provides typed access to 21 AI endpoints — scraping, RAG, embeddings, code review, text-to-SQL, browser automation, and more — with per-request USDC micropayments via the [x402 protocol](https://x402.org) on Base. No API keys, no accounts, no credit cards. Your wallet signature IS authentication. MIT licensed.

---

## Why mazzagrp-python exists

Every other AI API SDK was built for **human developers** — create an account, get an API key, add a credit card, manage rate plans.

**Agents can't do any of that.**

mazzagrp-python is built for the agent-first world:

- **No accounts** — generate a wallet locally, no signup
- **No API keys** — your wallet signature IS authentication
- **No credit cards** — agents pay per-request with USDC via [x402](https://x402.org)
- **21 endpoints** — scraping, RAG, sentiment, embeddings, code review, web automation, and more
- **$0.01–$0.50 per request** — fractions of a cent, settled on-chain

This is the stack that lets agents operate autonomously: **x402 + USDC on Base**.

---

## How x402 works

The [x402 protocol](https://x402.org) is an HTTP-native payment standard. It repurposes HTTP status code **402 Payment Required** — which has been reserved since 1999 and never used — to enable real-time micropayments for API access.

```
Agent → POST /v1/scrape {"url": "..."}
  ← 402 Payment Required (accepts: [{scheme: "exact", network: "base", amount: 0.05, payTo: "0x..."}])
Agent → signs EIP-3009 transfer authorization with wallet
Agent → POST /v1/scrape {"url": "..."} + X-PAYMENT: <signed-payload>
  ← 200 OK {"data": ...} (payment settled on-chain)
```

No API key. No pre-paid balance. No subscription. The server returns 402, the client signs a crypto payment authorization, retries with the payment header, and the server settles the USDC transfer on Base — all in one request.

The SDK handles this automatically. You just call methods and get results.

---

## Installation

```bash
pip install mazzagrp
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv pip install mazzagrp
```

### Requirements

- Python 3.9+
- An EVM wallet private key (for paid endpoints)
- USDC on Base (for paid endpoints — $5 covers thousands of requests)

---

## Quick Start

```python
from mazzagrp import MazzaClient

# Your wallet private key — agents sign with this, no API key needed
client = MazzaClient(private_key="0x...")

# Scrape a website
result = client.scrape(url="https://example.com")
print(result)

# Get a Lighthouse audit
audit = client.lighthouse(url="https://example.com")

# Summarize text
summary = client.summarize(text="Long article content here...")

# RAG query with citations
answer = client.rag_query(question="What is x402?")
```

> **No wallet?** The demo endpoint (`/v1/demo`) is free. Generate a wallet:
> ```python
> from eth_account import Account
> acct = Account.create()
> print(f"Private key: {acct.key.hex()}")
> print(f"Address: {acct.address}")  # Send USDC on Base here
> ```

---

## All 21 Endpoints

| # | Method | Endpoint | Price | SDK Method | Description |
|---|--------|----------|-------|------------|-------------|
| 1 | `GET` | `/v1/demo` | $0.01 | `client.demo()` | Test endpoint |
| 2 | `POST` | `/v1/scrape` | $0.05 | `client.scrape(url)` | Scrape a website |
| 3 | `POST` | `/v1/gigs/search` | $0.15 | `client.gigs_search(query)` | GigRadar — freelance gig search |
| 4 | `GET` | `/v1/lighthouse?url=` | $0.12 | `client.lighthouse(url)` | Lighthouse performance audit |
| 5 | `POST` | `/v1/a11y/audit` | $0.08 | `client.a11y_audit(url)` | Accessibility audit |
| 6 | `GET` | `/v1/crawl/judge?url=` | $0.03 | `client.crawl_judge(url)` | CrawlJudge — crawlability assessment |
| 7 | `POST` | `/v1/doc/extract` | $0.25 | `client.doc_extract(document)` | DocClerk — PDF/URL content extraction |
| 8 | `POST` | `/v1/sentiment` | $0.10 | `client.sentiment(text)` | Sentiment analysis |
| 9 | `POST` | `/v1/summarize` | $0.10 | `client.summarize(text)` | Text summarization |
| 10 | `POST` | `/v1/translate` | $0.12 | `client.translate(text, target_lang)` | Translation |
| 11 | `POST` | `/v1/classify` | $0.08 | `client.classify(text)` | Text classification |
| 12 | `POST` | `/v1/ner` | $0.10 | `client.ner(text)` | Named Entity Recognition |
| 13 | `POST` | `/v1/embeddings` | $0.05 | `client.embeddings(text)` | Vector embeddings |
| 14 | `POST` | `/v1/code-review` | $0.15 | `client.code_review(code)` | AI code review |
| 15 | `POST` | `/v1/sql-generate` | $0.12 | `client.sql_generate(query, schema)` | Text-to-SQL |
| 16 | `POST` | `/v1/rag-query` | $0.20 | `client.rag_query(question)` | RAG with citations |
| 17 | `POST` | `/v1/web-agent` | $0.50 | `client.web_agent(task)` | Browser automation |
| 18 | `POST` | `/v1/sheets-automation` | $0.30 | `client.sheets_automation(task)` | Sheets automation |
| 19 | `POST` | `/v1/roleplay` | $0.10 | `client.roleplay(character, message)` | Character engine |
| 20 | `POST` | `/v1/negotiation` | $0.15 | `client.negotiation(scenario)` | Negotiation training |
| 21 | `POST` | `/v1/knowledge-recall` | $0.25 | `client.knowledge_recall(question)` | Zero-hallucination recall |

---

## Examples

### Scraping & Auditing

```python
from mazzagrp import MazzaClient

client = MazzaClient(private_key="0x...")

# Scrape a product page
product = client.scrape(url="https://store.example.com/widget", selector=".product-info")

# Lighthouse performance audit
perf = client.lighthouse(url="https://example.com")
print(f"Performance: {perf['scores']['performance']}")

# Accessibility audit
a11y = client.a11y_audit(url="https://example.com", standards=["wcag-2.1-aa"])

# Crawlability check
crawl = client.crawl_judge(url="https://example.com")
```

### Document Processing

```python
# Extract content from a PDF URL
doc = client.doc_extract(document="https://example.com/report.pdf")

# Summarize
summary = client.summarize(text=doc["content"], max_length=200)

# Translate
translated = client.translate(text=summary["summary"], target_lang="es")
```

### NLP

```python
# Sentiment analysis
sentiment = client.sentiment(text="This product is amazing!")

# Named entity recognition
entities = client.ner(text="Apple was founded by Steve Jobs in Cupertino, California.")

# Text classification
categories = client.classify(text="The stock market rallied today.", labels=["finance", "sports", "tech"])

# Embeddings
vectors = client.embeddings(text="machine learning")
```

### Developer Tools

```python
# AI code review
review = client.code_review(code="def add(a, b): return a + b", language="python")

# Text-to-SQL
sql = client.sql_generate(
    query="Get all users who signed up last month",
    schema="users(id, name, email, created_at)"
)

# RAG with citations
answer = client.rag_query(
    question="What is the x402 protocol?",
    collection="docs"
)
```

### Automation

```python
# Browser automation
result = client.web_agent(task="Go to example.com and extract all prices")

# Sheets automation
sheets = client.sheets_automation(
    task="Create a spreadsheet with the top 10 Hacker News stories"
)
```

### Creative & Training

```python
# Character roleplay
reply = client.roleplay(
    character="A wise old wizard who speaks in riddles",
    message="What should I do about the dragon?"
)

# Negotiation training
session = client.negotiation(scenario="B2B SaaS pricing negotiation, $50k deal")

# Zero-hallucination knowledge recall
facts = client.knowledge_recall(question="What is the speed of light?")
```

---

## Configuration

```python
from mazzagrp import MazzaClient

# Default — uses https://api.mazzagrp.com
client = MazzaClient(private_key="0x...")

# Custom base URL (e.g. staging)
client = MazzaClient(
    private_key="0x...",
    base_url="https://staging-api.mazzagrp.com"
)

# Custom facilitator URL (advanced — for self-hosted x402 settlement)
client = MazzaClient(
    private_key="0x...",
    facilitator_url="https://my-facilitator.example.com"
)
```

---

## Wallet Setup

Generate a wallet, fund it with USDC on Base, and pass the private key:

```python
from eth_account import Account

# Generate a new wallet
wallet = Account.create()
print(f"Private key: {wallet.key.hex()}")
print(f"Address: {wallet.address}")

# Send USDC on Base to the address above
# Base Mainnet chain ID: 8453
# USDC contract: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA0b13F
```

> ⚠️ **Never commit your private key.** Use environment variables:
> ```python
> import os
> client = MazzaClient(private_key=os.environ["PRIVATE_KEY"])
> ```

---

## How It Compares

| | OpenAI API | Anthropic API | Other AI APIs | **mazzagrp-python** |
|---|---|---|---|---|
| **Auth** | API key | API key | API key | **Wallet signature** |
| **Payment** | Credit card | Credit card | Credit card / pre-paid | **USDC per-request** |
| **Signup** | Account required | Account required | Account required | **No signup** |
| **Agent-ready** | No | No | No | **Yes** |
| **On-chain** | No | No | No | **Base L2** |

✓ Crypto native · ✓ Agent ready · ✓ No API keys · ✓ Open source · ✓ x402 protocol

---

## Error Handling

```python
from mazzagrp import MazzaClient
import requests

client = MazzaClient(private_key="0x...")

try:
    result = client.scrape(url="https://example.com")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 402:
        print("Payment failed — check your USDC balance on Base")
    else:
        print(f"API error: {e}")
except RuntimeError as e:
    print(f"x402 payment error: {e}")
```

---

## Development

```bash
git clone https://github.com/itsmeadamdamroma/mazzagrp-python.git
cd mazzagrp-python
pip install -e ".[dev]"
pytest
```

---

## License

[MIT](LICENSE) © 2025 Mazza Group

---

<div align="center">

**[mazzagrp.com](https://mazzagrp.com) · [API Docs](https://mazzagrp.com/apis) · [x402 Protocol](https://x402.org)**

</div>
