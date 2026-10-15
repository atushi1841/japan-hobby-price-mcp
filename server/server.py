#!/usr/bin/env python3
"""japan-hobby-price-mcp MCP server (MCPB bundle entry point).

Consolidated server combining:
  - tcg-price-japan      (suruga-ya.jp TCG data, 960 obs)
  - japan-anime-figure-mcp  (MyFigureList figure data, 654 obs)

Tools:
  - tcg_current_price(item)     -> latest TCG price snapshot
  - tcg_price_history(item, n)  -> TCG price time series
  - figure_current_price(name)  -> latest figure price snapshot
  - figure_price_history(name, n) -> figure price time series

Data sources are bundled locally (read-only). No network, no API key.
For live dlsite/mandarake data, use Apify actors:
  - surugaya-japan-hobby-prices (tcg data + more TCG)
  - mandarake-surugaya-mcp (mandarake auction prices)
  - dlsite-scraper (dlsite commodity prices)
Links available via the kensho-apify MCP server.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TCG_DATA = DATA_DIR / "accumulated.jsonl"
FIGURE_DATA = DATA_DIR / "anime_figure_prices_normalized.jsonl"

server = FastMCP("japan-hobby-price-mcp")


# ── TCG helpers (suruga-ya.jp dataset) ───────────────────────────────────────

def _load_tcg() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not TCG_DATA.exists():
        return rows
    with TCG_DATA.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _match_tcg(rows: list[dict[str, Any]], item: str) -> list[dict[str, Any]]:
    q = item.strip().lower()
    out = []
    for r in rows:
        blob = " ".join([
            str(r.get("name", "")),
            str(r.get("keyword", "")),
            str(r.get("url", "")),
        ]).lower()
        if q and q in blob:
            out.append(r)
    return out


# ── Figure helpers (MyFigureList dataset) ─────────────────────────────────────

def _load_figures() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not FIGURE_DATA.exists():
        return rows
    with FIGURE_DATA.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _match_figure(rows: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    q = name.strip().lower()
    if not q:
        return rows
    out = []
    for r in rows:
        blob = " ".join([
            str(r.get("name", "")),
            str(r.get("series", "")),
            str(r.get("character", "")),
            str(r.get("manufacturer", "")),
            str(r.get("source_url", "")),
        ]).lower()
        if q in blob:
            out.append(r)
    return out


# ── Tools ─────────────────────────────────────────────────────────────────────

@server.tool()
async def tcg_current_price(item: str) -> dict[str, Any]:
    """Current used/new/list price for a Pokemon/TCG item in the Japan (Suruga-ya) dataset.

    Args:
        item: item name or URL substring (e.g. "リザードン", "pokemon card").
    Returns the latest observed price snapshot (JPY) plus match count.
    """
    rows = sorted(_match_tcg(_load_tcg(), item), key=lambda r: r.get("collected_at", ""))
    if not rows:
        return {"item": item, "matches": 0, "error": "no matching item in dataset"}
    latest = rows[-1]
    return {
        "item": item,
        "matches": len(rows),
        "name": latest.get("name"),
        "url": latest.get("url"),
        "used_price_jpy": latest.get("used_price_jpy"),
        "new_price_jpy": latest.get("new_price_jpy"),
        "list_price_jpy": latest.get("list_price_jpy"),
        "collected_at": latest.get("collected_at"),
        "source": latest.get("source"),
        "in_stock": latest.get("in_stock"),
    }


@server.tool()
async def tcg_price_history(item: str, limit: int = 50) -> dict[str, Any]:
    """Price time series (trend) for a TCG item in the Japan (Suruga-ya) dataset.

    Args:
        item: item name or URL substring.
        limit: max number of history rows to return (default 50).
    Returns oldest-first observations of used/new/list prices (JPY).
    """
    rows = sorted(_match_tcg(_load_tcg(), item), key=lambda r: r.get("collected_at", ""))
    if not rows:
        return {"item": item, "matches": 0, "error": "no matching item in dataset"}
    hist = [
        {
            "collected_at": r.get("collected_at"),
            "used_price_jpy": r.get("used_price_jpy"),
            "new_price_jpy": r.get("new_price_jpy"),
            "list_price_jpy": r.get("list_price_jpy"),
        }
        for r in rows[-limit:]
    ]
    return {"item": item, "matches": len(rows), "history": hist}


@server.tool()
async def figure_current_price(name: str) -> dict[str, Any]:
    """Current price snapshot for an anime figure in the Japan (MyFigureList) dataset.

    Args:
        name: figure name, series, character, or URL substring.
    Returns the latest observed price snapshot plus match count.
    """
    rows = sorted(_match_figure(_load_figures(), name), key=lambda r: r.get("fetched_at", ""))
    if not rows:
        return {"name": name, "matches": 0, "error": "no matching figure in dataset"}
    latest = rows[-1]
    offers = latest.get("offers", [])
    in_stock = [o for o in offers if o.get("availability") == "InStock"]
    return {
        "name": latest.get("name"),
        "series": latest.get("series"),
        "character": latest.get("character"),
        "manufacturer": latest.get("manufacturer"),
        "category": latest.get("category"),
        "matches": len(rows),
        "lowest_price_jpy": latest.get("lowest_price_jpy"),
        "highest_price_jpy": latest.get("highest_price_jpy"),
        "msrp_jpy": latest.get("msrp_jpy"),
        "in_stock_count": latest.get("in_stock_count"),
        "total_offers": latest.get("total_offers_count"),
        "in_stock_offers": in_stock[:5],
        "all_offers": offers[:10],
        "fetched_at": latest.get("fetched_at"),
        "source_url": latest.get("source_url"),
    }


@server.tool()
async def figure_price_history(name: str, limit: int = 50) -> dict[str, Any]:
    """Price time series for an anime figure in the Japan (MyFigureList) dataset.

    Args:
        name: figure name or URL substring.
        limit: max number of history rows to return (default 50).
    Returns oldest-first observations of lowest/highest prices (JPY).
    """
    rows = sorted(_match_figure(_load_figures(), name), key=lambda r: r.get("fetched_at", ""))
    if not rows:
        return {"name": name, "matches": 0, "error": "no matching figure in dataset"}
    hist = [
        {
            "fetched_at": r.get("fetched_at"),
            "lowest_price_jpy": r.get("lowest_price_jpy"),
            "highest_price_jpy": r.get("highest_price_jpy"),
            "in_stock_count": r.get("in_stock_count"),
        }
        for r in rows[-limit:]
    ]
    return {"name": name, "matches": len(rows), "history": hist}


if __name__ == "__main__":
    server.run(transport="stdio")
