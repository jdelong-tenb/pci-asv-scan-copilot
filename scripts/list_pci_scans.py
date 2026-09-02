#!/usr/bin/env python3
"""
list_pci_scans.py — List existing PCI-related scans and available PCI ASV templates.

Useful for verifying what's already configured in your Tenable VM account before
using the PCI ASV Scan Copilot skill.

Usage:
    export TIO_ACCESS_KEY="your-access-key"
    export TIO_SECRET_KEY="your-secret-key"
    python3 scripts/list_pci_scans.py

Generate API keys: Settings > My Account > API Keys
Requires: Python 3 (stdlib only)
"""

import json
import os
import sys
import urllib.request
import urllib.error

BASE_URL = "https://cloud.tenable.com"


def get_headers():
    access_key = os.environ.get("TIO_ACCESS_KEY")
    secret_key = os.environ.get("TIO_SECRET_KEY")
    if not access_key or not secret_key:
        print("ERROR: TIO_ACCESS_KEY and TIO_SECRET_KEY environment variables are required.")
        print("Generate API keys at: Settings > My Account > API Keys")
        sys.exit(1)
    return {
        "X-ApiKeys": f"accessKey={access_key};secretKey={secret_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def api_get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers=get_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {"error": f"HTTP {e.code}: {body[:300]}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    print("=== Existing PCI-related scans ===")
    scans_resp = api_get("/scans")
    if "error" in scans_resp:
        print(f"  Could not retrieve scans: {scans_resp['error']}")
    else:
        scans = scans_resp.get("scans") or []
        pci_scans = [
            s for s in scans
            if "pci" in s.get("name", "").lower() or "asv" in s.get("name", "").lower()
        ]
        if pci_scans:
            for s in pci_scans:
                status = s.get("status", "unknown")
                scan_id = s.get("id", "?")
                name = s.get("name", "?")
                print(f"  [ID {scan_id}] {name}  (status: {status})")
        else:
            print("  No PCI or ASV scans found.")
            print("  The skill will help you create one.")

    print()
    print("=== Available PCI ASV scan templates ===")
    templates_resp = api_get("/editor/policy/templates")
    if "error" in templates_resp:
        print(f"  Could not retrieve templates: {templates_resp['error']}")
    else:
        templates = templates_resp.get("templates") or []
        pci_templates = [
            t for t in templates
            if "pci" in t.get("name", "").lower() or "pci" in t.get("title", "").lower()
        ]
        if pci_templates:
            for t in pci_templates:
                title = t.get("title") or t.get("name", "unknown")
                uuid = t.get("uuid", "?")
                desc = t.get("desc", "")
                print(f"  [{uuid}] {title}")
                if desc:
                    print(f"    {desc[:120]}")
        else:
            print("  No PCI templates found.")
            print("  Verify your Tenable VM subscription includes PCI ASV scanning.")

    print()
    print("=== Existing PCI scan policies ===")
    policies_resp = api_get("/policies")
    if "error" in policies_resp:
        print(f"  Could not retrieve policies: {policies_resp['error']}")
    else:
        policies = policies_resp.get("policies") or []
        pci_policies = [
            p for p in policies
            if "pci" in p.get("name", "").lower() or "asv" in p.get("name", "").lower()
        ]
        if pci_policies:
            for p in pci_policies:
                print(f"  [ID {p.get('id', '?')}] {p.get('name', '?')}")
        else:
            print("  No PCI scan policies configured yet.")
            print("  The skill will create one using a template.")


if __name__ == "__main__":
    main()
