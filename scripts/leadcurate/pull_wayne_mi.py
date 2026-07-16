#!/usr/bin/env python3
"""Pull the current official Wayne County MI annual assessment package.

Wayne County serves the ZIP behind an Akamai browser check, so this pull uses
Playwright intentionally. It is manual-invoke only and writes source metadata
beside the untouched ZIP.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ASSETS = {
    "assessment": {
        "source_page": (
            "https://www.waynecountymi.gov/Government/Departments/Management-Budget/"
            "Assessment-Equalization/Annual-Assessment-Data"
        ),
        "file_name": "2026-wayne-county-assessments-names-addresses-legal.zip",
        "file_url": (
            "https://www.waynecountymi.gov/files/assets/mainsite/v/1/management-amp-budget/"
            "documents/2026-wayne-county-assessments-names-addresses-legal.zip"
        ),
        "source_label": "2026 Wayne County Assessments (Names, Addresses, Legal)",
        "source_status": "2026 annual county assessment roll; county states annual data is not real-time",
    },
    "tax-foreclosure": {
        "source_page": (
            "https://www.waynecountymi.gov/Government/Elected-Officials/Treasurer/"
            "Property-Tax-Information/Forfeited-Property-List-with-Interested-Parties"
        ),
        "file_name": "2026_wayne_county_delinquent_tax_liens.pdf",
        "file_url": (
            "https://www.waynecountymi.gov/files/assets/mainsite/v/1/treasurer/"
            "property-amp-taxes/documents/2026_wayne_county_delinquent_tax_liens.pdf"
        ),
        "source_label": "2026 Wayne County Foreclosure Listing",
        "source_status": "Official 2026 delinquent-tax lien and foreclosure listing",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def archive_members(path: Path) -> list[dict[str, object]]:
    with zipfile.ZipFile(path) as archive:
        return [
            {
                "name": item.filename,
                "uncompressed_bytes": item.file_size,
                "compressed_bytes": item.compress_size,
            }
            for item in archive.infolist()
            if not item.is_dir()
        ]


def pull(asset: str, output_dir: Path, timeout_ms: int) -> dict[str, object]:
    spec = ASSETS[asset]
    source_page = spec["source_page"]
    file_name = spec["file_name"]
    file_url = spec["file_url"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / file_name
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            accept_downloads=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        response = page.goto(source_page, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(5000)
        if not response or response.status >= 400:
            raise RuntimeError(f"Assessment page returned {response.status if response else 'no response'}")

        locator = page.locator(f'a[href*="{file_name}"]').first
        if locator.count() != 1:
            links = page.locator("a").evaluate_all(
                "els => els.map(a => ({text: a.textContent.trim(), href: a.href}))"
            )
            matching = [item for item in links if file_name.lower() in item["href"].lower()]
            if not matching:
                raise RuntimeError("The official 2026 countywide assessment link was not found")
            href = matching[0]["href"]
            locator = page.locator(f'a[href="{href}"]').first

        href = locator.get_attribute("href") or file_url
        try:
            with page.expect_download(timeout=timeout_ms) as pending:
                locator.click(timeout=timeout_ms)
            download = pending.value
            download.save_as(output)
        except PlaywrightTimeoutError:
            # Some county deployments navigate to the ZIP instead of emitting a
            # download event. Reuse the validated browser session and cookies.
            cookie_header = "; ".join(
                f"{cookie['name']}={cookie['value']}" for cookie in context.cookies()
            )
            headers = {"Referer": source_page}
            if cookie_header:
                headers["Cookie"] = cookie_header
            file_response = context.request.get(href, headers=headers, timeout=timeout_ms)
            if not file_response.ok:
                raise RuntimeError(f"ZIP request returned HTTP {file_response.status}")
            output.write_bytes(file_response.body())
        finally:
            browser.close()

    if asset == "assessment" and not zipfile.is_zipfile(output):
        raise RuntimeError(f"Downloaded payload is not a ZIP: {output}")
    if asset == "tax-foreclosure" and not output.read_bytes()[:5] == b"%PDF-":
        raise RuntimeError(f"Downloaded payload is not a PDF: {output}")
    retrieved = datetime.now(timezone.utc).isoformat()
    metadata = {
        "market": "wayne-mi",
        "asset": asset,
        "source_page": source_page,
        "source_url": href,
        "source_label": spec["source_label"],
        "source_status": spec["source_status"],
        "retrieved_at": retrieved,
        "file": str(output),
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "archive_members": archive_members(output) if asset == "assessment" else None,
    }
    metadata_path = output_dir / f"wayne-mi-{asset}-source-meta.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", choices=sorted(ASSETS), default="assessment")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-ms", type=int, default=180_000)
    args = parser.parse_args()
    print(json.dumps(pull(args.asset, args.output_dir, args.timeout_ms), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
