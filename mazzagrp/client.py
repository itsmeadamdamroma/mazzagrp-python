"""
Mazza Group x402 payment client.

Handles the x402 flow: POST → HTTP 402 → parse payment requirements → sign EIP-712 → retry with payment header → settle.
Wraps all 21 mazzagrp.com AI endpoints at /api/{name}.
"""

from __future__ import annotations

import base64
import json
import typing as t

import requests
from eth_account import Account
from eth_account.messages import encode_typed_data

DEFAULT_BASE_URL = "https://mazzagrp.com"
USDC_BASE = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"  # USDC on Base Sepolia (testnet)
BASE_CHAIN_ID = 84532  # Base Sepolia


class MazzaClient:
    """Client for mazzagrp.com AI APIs with x402 USDC micropayments on Base.

    No API key needed — your wallet signs payments. Fund with USDC on Base.

    Args:
        private_key: EVM private key (hex string, 0x-prefixed) for signing payments.
        base_url: API base URL (default https://mazzagrp.com).
    """

    def __init__(
        self,
        private_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        **_kwargs: t.Any,
    ):
        self.base_url = base_url.rstrip("/")
        self.account = Account.from_key(private_key) if private_key else None
        self._session = requests.Session()

    # ── x402 payment flow ───────────────────────────────────────────────

    def _build_payment_header(self, requirements: dict) -> str:
        """Build the PAYMENT-SIGNATURE header for x402 v2."""
        if not self.account:
            raise RuntimeError("private_key required for paid endpoints")

        scheme = requirements.get("scheme", "exact")
        network = requirements.get("network", f"eip155:{BASE_CHAIN_ID}")
        chain_id = int(network.split(":")[1]) if ":" in network else BASE_CHAIN_ID
        amount = requirements.get("amount", "0")
        asset = requirements.get("asset", USDC_BASE)
        pay_to = requirements.get("payTo", "")
        extra = requirements.get("extra", {})
        max_timeout = requirements.get("maxTimeoutSeconds", 300)

        # EIP-712 typed data for x402 exact payment
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
                "name": extra.get("name", "USD Coin"),
                "version": extra.get("version", "2"),
                "chainId": chain_id,
                "verifyingContract": asset,
            },
            "message": {
                "from": self.account.address,
                "to": pay_to,
                "value": int(amount),
                "validAfter": 0,
                "validBefore": 2**64 - 1,
                "nonce": _gen_nonce(),
            },
        }

        signed = self.account.sign_message(encode_typed_data(full_message=typed_data))
        payment_payload = {
            "signature": signed.signature.hex(),
            "scheme": scheme,
            "network": network,
            "from": self.account.address,
        }
        return base64.b64encode(json.dumps(payment_payload).encode()).decode()

    def _request(
        self,
        method: str,
        path: str,
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
                json=json_body if json_body is not None else None,
                headers=headers,
                timeout=120,
            )

            if resp.status_code == 402:
                try:
                    body = resp.json()
                except Exception:
                    body = {}

                pay_header = resp.headers.get("PAYMENT-REQUIRED") or resp.headers.get("X-PAYMENT-REQUIRED")
                if pay_header:
                    decoded = json.loads(base64.b64decode(pay_header))
                    requirements = decoded.get("accepts", [decoded])[0]
                elif "accepts" in body:
                    requirements = body["accepts"][0]
                else:
                    raise RuntimeError(f"x402 payment required but no payment requirements found: {resp.text[:500]}")

                payment_header = self._build_payment_header(requirements)
                headers["PAYMENT-SIGNATURE"] = payment_header
                continue

            resp.raise_for_status()
            return resp.json()

        raise RuntimeError(f"x402 payment failed after {retries} retries")

    # ── 21 endpoint wrappers ───────────────────────────────────────────
    # All endpoints take {"prompt": str} as input via POST /api/{name}

    def recall(self, prompt: str, **kw) -> dict:
        """POST /api/recall — $0.20 — Memory recall and context retrieval."""
        return self._request("POST", "/api/recall", {"prompt": prompt, **kw})

    def rag(self, prompt: str, **kw) -> dict:
        """POST /api/rag — $1.50 — Retrieval-augmented generation pipeline."""
        return self._request("POST", "/api/rag", {"prompt": prompt, **kw})

    def sql(self, prompt: str, **kw) -> dict:
        """POST /api/sql — $1.20 — AI-powered SQL query generation and optimization."""
        return self._request("POST", "/api/sql", {"prompt": prompt, **kw})

    def negotiator(self, prompt: str, **kw) -> dict:
        """POST /api/negotiator — $1.50 — AI negotiation assistant and strategy advisor."""
        return self._request("POST", "/api/negotiator", {"prompt": prompt, **kw})

    def design(self, prompt: str, **kw) -> dict:
        """POST /api/design — $0.80 — AI-assisted design recommendations and mockups."""
        return self._request("POST", "/api/design", {"prompt": prompt, **kw})

    def simulation(self, prompt: str, **kw) -> dict:
        """POST /api/simulation — $2.00 — AI scenario simulation and modeling."""
        return self._request("POST", "/api/simulation", {"prompt": prompt, **kw})

    def character(self, prompt: str, **kw) -> dict:
        """POST /api/character — $0.10 — AI character generation and development."""
        return self._request("POST", "/api/character", {"prompt": prompt, **kw})

    def puzzles(self, prompt: str, **kw) -> dict:
        """POST /api/puzzles — $0.80 — AI puzzle generation and solving."""
        return self._request("POST", "/api/puzzles", {"prompt": prompt, **kw})

    def arena(self, prompt: str, **kw) -> dict:
        """POST /api/arena — $1.20 — AI model comparison and benchmarking arena."""
        return self._request("POST", "/api/arena", {"prompt": prompt, **kw})

    def storyforge(self, prompt: str, **kw) -> dict:
        """POST /api/storyforge — $0.60 — AI-powered creative story generation and worldbuilding."""
        return self._request("POST", "/api/storyforge", {"prompt": prompt, **kw})

    def autoflow(self, prompt: str, **kw) -> dict:
        """POST /api/autoflow — $1.50 — AI-powered automated workflow orchestration."""
        return self._request("POST", "/api/autoflow", {"prompt": prompt, **kw})

    def worldbuilder(self, prompt: str, **kw) -> dict:
        """POST /api/worldbuilder — $2.00 — AI worldbuilding for fiction, games, and RPGs."""
        return self._request("POST", "/api/worldbuilder", {"prompt": prompt, **kw})

    def longqa(self, prompt: str, **kw) -> dict:
        """POST /api/longqa — $1.00 — Long-form question answering with deep analysis."""
        return self._request("POST", "/api/longqa", {"prompt": prompt, **kw})

    def temporal(self, prompt: str, **kw) -> dict:
        """POST /api/temporal — $0.80 — Temporal workflow orchestration assistant."""
        return self._request("POST", "/api/temporal", {"prompt": prompt, **kw})

    def desktop(self, prompt: str, **kw) -> dict:
        """POST /api/desktop — $1.50 — Desktop application AI assistant."""
        return self._request("POST", "/api/desktop", {"prompt": prompt, **kw})

    def mcp_eval(self, prompt: str, **kw) -> dict:
        """POST /api/mcp-eval — $2.00 — MCP (Model Context Protocol) evaluation and scoring."""
        return self._request("POST", "/api/mcp-eval", {"prompt": prompt, **kw})

    def sheets(self, prompt: str, **kw) -> dict:
        """POST /api/sheets — $1.00 — AI spreadsheet formula generation and data analysis."""
        return self._request("POST", "/api/sheets", {"prompt": prompt, **kw})

    def webagent(self, prompt: str, **kw) -> dict:
        """POST /api/webagent — $1.80 — AI web agent for autonomous browsing and task execution."""
        return self._request("POST", "/api/webagent", {"prompt": prompt, **kw})

    def consultation(self, prompt: str, **kw) -> dict:
        """POST /api/consultation — $5.00 — AI consultation with a senior strategist."""
        return self._request("POST", "/api/consultation", {"prompt": prompt, **kw})

    def chatbot(self, prompt: str, **kw) -> dict:
        """POST /api/chatbot — $1.00 — Conversational AI chatbot interaction."""
        return self._request("POST", "/api/chatbot", {"prompt": prompt, **kw})

    def automation(self, prompt: str, **kw) -> dict:
        """POST /api/automation — $15.00 — AI-powered workflow automation design and implementation."""
        return self._request("POST", "/api/automation", {"prompt": prompt, **kw})


def _gen_nonce() -> bytes:
    """Generate a random 32-byte nonce for EIP-3009."""
    import os
    return os.urandom(32)
