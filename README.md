# japan-hobby-price-mcp

Consolidated Japanese hobby price data as a read-only MCP server.

## Data

| Dataset | Source | Observations | Tool |
|---|---|---|---|
| TCG prices (Pokemon etc.) | suruga-ya.jp | 960 | `tcg_current_price` / `tcg_price_history` |
| Anime figure prices | MyFigureList | 654 | `figure_current_price` / `figure_price_history` |

Both datasets are bundled locally in the MCPB release. No network calls, no API key required.

## Tools

- **tcg_current_price(item)** — latest used/new/list price for a TCG item
- **tcg_price_history(item, limit=50)** — price time series for a TCG item
- **figure_current_price(name)** — latest price snapshot for an anime figure
- **figure_price_history(name, limit=50)** — price time series for a figure

## Live data (Apify actors)

For real-time scraping of dlsite, mandarake, mercari, yahoo auctions etc.:

- [surugaya-japan-hobby-prices](https://apify.com/fruitful_quintessence/surugaya-japan-hobby-prices) — TCG + more
- [mandarake-surugaya-mcp](https://apify.com/fruitful_quintessence/mandarake-surugaya-mcp) — mandarake auctions
- [dlsite-scraper](https://apify.com/fruitful_quintessence/dlsite-scraper) — dlsite commodity data

Use the [kensho-apify MCP server](https://github.com/atushi1841/kensho-apify) to run these actors programmatically.

## Install

```bash
smithery install @atushi1841/japan-hobby-price-mcp
```

Or clone this repo and run:

```bash
uv run --directory . src/stdio_main.py
```

## Repository

- GitHub: <https://github.com/atushi1841/japan-hobby-price-mcp>
- MCPB release: <https://github.com/atushi1841/japan-hobby-price-mcp/releases/download/v1.0.0/server.mcpb>

## Related Projects

- [tcg-price-japan](https://github.com/atushi1841/tcg-price-japan) — original TCG-only server
- [japan-anime-figure-mcp](https://github.com/atushi1841/japan-anime-figure-mcp) — original figure-only server
- [kensho-apify](https://github.com/atushi1841/kensho-apify) — Apify actor wrapper MCP

## License

MIT
