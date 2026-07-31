"""
Mazza Group x402 payment client.

Handles the x402 flow: GET/POST → HTTP 402 → parse payment requirements → sign EIP-712/EIP-3009 → retry with payment header → settle.
Wraps all 21 mazzagrp.com AI endpoints.
"""

from __future__ import annotations

import base64
import json
import typing as t

import requests
from eth_account import Account
from eth_account.messages import encode_typed_data

DEFAULT_BASE_URL = "https://api.mazzagrp.com"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA0b13F"  # USDC on Base (chain 8453)
BASE_CHAIN_ID = 8453


class MazzaClient:
    """Client for mazzagrp.com AI APIs with x402 USDC micropayments on Base.

    No API key needed — your wallet signs payments. Fund with USDC on Base.

    Args:
        private_key: EVM private key (hex string, 0x-prefixed) for signing payments.
        base_url: API base URL (default https://api.mazzagrp.com).
        facilitator_url: x402 facilitator URL (optional — mazzagrp handles settlement server-side).
    """

    def __init__(
        self,
        private_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        facilitator_url: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.facilitator_url = facilitator_url
        self.account = Account.from_key(private_key) if private_key else None
        self._session = requests.Session()

    # ── x402 payment flow ───────────────────────────────────────────────

    def _sign_eip3009(self, requirements: dict) -> dict:
        """Sign an EIP-3009 transfer-authorization for USDC payment on Base."""
        if not self.account:
            raise RuntimeError("private_key required for paid endpoints")

        pay_to = requirements["payTo"]
        amount = requirements["maxAmountRequired"]
        valid_after = "0"
        import time
        valid_before = str(int(time.time()) + (requirements.get("maxTimeoutSeconds", 3600)))
        nonce = _gen_nonce()

        # EIP-3009 TransferWithAuthorization — USDC contract on Base
        # USDC uses EIP-712 typed data with the TransferWithAuthorization struct
        typed_data = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "TransferWithAuthorization": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "validAfter", "type": "uint256"},
                    {"name": "validBefore", "type": "uint256"},
                    {"name": "nonce", "type": "bytes32"},
                ],
            },
            "primaryType": "TransferWithAuthorization",
            "domain": {
                "name": "USD Coin",
                "version": "2",
                "chainId": BASE_CHAIN_ID,
                "verifyingContract": USDC_BASE,
            },
            "message": {
                "from": self.account.address,
                "to": pay_to,
                "value": int(amount),
                "validAfter": int(valid_after),
                "validBefore": int(valid_before),
                "nonce": nonce,
            },
        }
        signed = self.account.sign_message(encode_typed_data(full_message=typed_data))
        sig_hex = signed.signature.hex()
        if not sig_hex.startswith("0x"):
            sig_hex = "0x" + sig_hex

        return {
            "authorization": {
                "from": self.account.address,
                "to": pay_to,
                "value": str(amount),
                "validAfter": valid_after,
                "validBefore": valid_before,
                "nonce": "0x" + nonce.hex() if isinstance(nonce, bytes) else nonce,
            },
            "signature": sig_hex,
        }

    def _build_payment_header(self, requirements: dict, scheme: str = "exact") -> str:
        """Build the x402 payment payload + base64-encode for the X-PAYMENT header."""
        payload_data = self._sign_eip3009(requirements)
        payment_payload = {
            "x402Version": 1,
            "scheme": scheme,
            "network": "base",
            "payload": payload_data,
        }
        return base64.b64encode(json.dumps(payment_payload).encode()).decode()

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: dict | None = None,
        retries: int = 3,
    ) -> dict:
        """Execute request with automatic x402 payment on 402."""
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}

        for attempt in range(retries + 1):
            resp = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json_body if json_body is not None else None,
                headers=headers,
                timeout=120,
            )

            if resp.status_code == 402:
                # x402: parse payment requirements from 402 response body
                try:
                    body = resp.json()
                except Exception:
                    body = {}

                # v1 puts accepts in body; v2 uses PAYMENT-REQUIRED header
                pay_header = resp.headers.get("PAYMENT-REQUIRED") or resp.headers.get("X-PAYMENT-REQUIRED")
                if pay_header:
                    decoded = json.loads(base64.b64decode(pay_header))
                    requirements = decoded.get("accepts", [decoded])[0]
                elif "accepts" in body:
                    requirements = body["accepts"][0]
                else:
                    raise RuntimeError(f"x402 payment required but no payment requirements found: {resp.text[:500]}")

                # sign and retry
                payment_header = self._build_payment_header(requirements)
                headers["X-PAYMENT"] = payment_header
                continue

            resp.raise_for_status()
            return resp.json()

        raise RuntimeError(f"x402 payment failed after {retries} retries")

    # ── 21 endpoint wrappers ───────────────────────────────────────────

    def demo(self) -> dict:
        """GET /v1/demo — $0.01 — Test endpoint."""
        return self._request("GET", "/v1/demo")

    def scrape(self, url: str, **kwargs) -> dict:
        """POST /v1/scrape — $0.05 — Scrape a URL."""
        return self._request("POST", "/v1/scrape", json_body={"url": url, **kwargs})

    def gigs_search(self, query: str, **kwargs) -> dict:
        """POST /v1/gigs/search — $0.15 — GigRadar: search freelance gigs."""
        return self._request("POST", "/v1/gigs/search", json_body={"query": query, **kwargs})

    def lighthouse(self, url: str) -> dict:
        """GET /v1/lighthouse — $0.12 — Lighthouse audit of a URL."""
        return self._request("GET", "/v1/lighthouse", params={"url": url})

    def a11y_audit(self, url: str, **kwargs) -> dict:
        """POST /v1/a11y/audit — $0.08 — Accessibility audit."""
        return self._request("POST", "/v1/a11y/audit", json_body={"url": url, **kwargs})

    def crawl_judge(self, url: str) -> dict:
        """GET /v1/crawl/judge — $0.03 — CrawlJudge: assess crawlability."""
        return self._request("GET", "/v1/crawl/judge", params={"url": url})

    def doc_extract(self, document: str, **kwargs) -> dict:
        """POST /v1/doc/extract — $0.25 — DocClerk: extract content from PDF/URL."""
        return self._request("POST", "/v1/doc/extract", json_body={"document": document, **kwargs})

    def sentiment(self, text: str, **kwargs) -> dict:
        """POST /v1/sentiment — $0.10 — Sentiment analysis."""
        return self._request("POST", "/v1/sentiment", json_body={"text": text, **kwargs})

    def summarize(self, text: str, **kwargs) -> dict:
        """POST /v1/summarize — $0.10 — Summarize text."""
        return self._request("POST", "/v1/summarize", json_body={"text": text, **kwargs})

    def translate(self, text: str, target_lang: str, **kwargs) -> dict:
        """POST /v1/translate — $0.12 — Translate text."""
        return self._request("POST", "/v1/translate", json_body={"text": text, "target_lang": target_lang, **kwargs})

    def classify(self, text: str, **kwargs) -> dict:
        """POST /v1/classify — $0.08 — Classify text into categories."""
        return self._request("POST", "/v1/classify", json_body={"text": text, **kwargs})

    def ner(self, text: str, **kwargs) -> dict:
        """POST /v1/ner — $0.10 — Named Entity Recognition."""
        return self._request("POST", "/v1/ner", json_body={"text": text, **kwargs})

    def embeddings(self, text: str, **kwargs) -> dict:
        """POST /v1/embeddings — $0.05 — Generate embeddings."""
        return self._request("POST", "/v1/embeddings", json_body={"text": text, **kwargs})

    def code_review(self, code: str, **kwargs) -> dict:
        """POST /v1/code-review — $0.15 — AI code review."""
        return self._request("POST", "/v1/code-review", json_body={"code": code, **kwargs})

    def sql_generate(self, query: str, schema: str | None = None, **kwargs) -> dict:
        """POST /v1/sql-generate — $0.12 — Text-to-SQL generation."""
        return self._request("POST", "/v1/sql-generate", json_body={"query": query, "schema": schema, **kwargs})

    def rag_query(self, question: str, **kwargs) -> dict:
        """POST /v1/rag-query — $0.20 — RAG with citations."""
        return self._request("POST", "/v1/rag-query", json_body={"question": question, **kwargs})

    def web_agent(self, task: str, **kwargs) -> dict:
        """POST /v1/web-agent — $0.50 — Browser automation agent."""
        return self._request("POST", "/v1/web-agent", json_body={"task": task, **kwargs})

    def sheets_automation(self, task: str, **kwargs) -> dict:
        """POST /v1/sheets-automation — $0.30 — Sheets automation."""
        return self._request("POST", "/v1/sheets-automation", json_body={"task": task, **kwargs})

    def roleplay(self, character: str, message: str, **kwargs) -> dict:
        """POST /v1/roleplay — $0.10 — Character engine roleplay."""
        return self._request("POST", "/v1/roleplay", json_body={"character": character, "message": message, **kwargs})

    def negotiation(self, scenario: str, **kwargs) -> dict:
        """POST /v1/negotiation — $0.15 — Negotiation training."""
        return self._request("POST", "/v1/negotiation", json_body={"scenario": scenario, **kwargs})

    def knowledge_recall(self, question: str, **kwargs) -> dict:
        """POST /v1/knowledge-recall — $0.25 — Zero-hallucination knowledge recall."""
        return self._request("POST", "/v1/knowledge-recall", json_body={"question": question, **kwargs})


def _gen_nonce() -> bytes:
    """Generate a random 32-byte nonce for EIP-3009."""
    import secrets
    return secrets.token_bytes(32)
