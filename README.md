# PCI ASV Scan Copilot

A Claude Code skill that walks you through the full three-month PCI ASV (Approved Scanning Vendor) external scan cycle — from scan configuration to attestation readiness.

## What it does

PCI DSS v4.0.1 Requirement 11.3.2 requires external vulnerability scans at least once every three months of your cardholder data environment (CDE) by an Approved Scanning Vendor. The cycle has five places people commonly get stuck:

1. **Scan setup** — a network scan (template `asv`, "PCI Quarterly External Scan") plus a PCI-scoped web application scan, and the correct external-facing targets
2. **Launch and monitoring** — starting the scan and tracking progress until completion
3. **Finding review** — understanding which failures actually block attestation, with findings grouped by PCI DSS v4.0.1 requirement
4. **Dispute identification** — distinguishing genuine false positives and compensating-control candidates from findings that need to be remediated
5. **Attestation readiness** — a preliminary readiness check; the ASV's review is the only authoritative result

The skill does not create or submit attestations, and it does not track internal scans. Web application scanning defaults to guided steps in the PCI workbench, with an optional tested WAS v2 REST route (the Tenable VM MCP has no web application scanning tools). Web application findings are supplied by you. See SKILL.md for details.

This skill reads your real Tenable Vulnerability Management account state via the API and walks you through whichever phase you're in.

This is a community-built skill, not official Tenable support and not PCI DSS compliance advice. Consult your QSA for authoritative compliance guidance.

## Prerequisites

- Claude Code (or another skill-compatible client) with the Tenable Vulnerability Management MCP server configured and connected. The endpoint is `https://cloud.tenable.com/mcp` (streamable HTTP; the server reports itself as "Tenable VM MCP"). It authenticated successfully with this header, shown with placeholders only:
  ```
  X-ApiKeys: accessKey=<ACCESS>;secretKey=<SECRET>
  ```
  See Claude Code's documentation for adding an HTTP MCP server with a custom header. SKILL.md refers to tools by bare name (for example `scan_create`, `policy_templates`); your client may show them with a prefix that depends on what you named the MCP server (for example `mcp__<server-name>__scan_create`).
- A Tenable Vulnerability Management account with PCI ASV and API access. Only Administrator users can perform the PCI scanning steps, so the API key pair must belong to an Administrator. Generate it under **Settings > My Account > API Keys**.
- Never commit API keys to this repo. Store them outside the repo (for example in environment variables or the OS keychain) and keep them out of any config file you commit.
- Your external-facing CDE targets (IP addresses, hostnames, or CIDR ranges) identified before you start.

## How it connects

The skill works through Tenable's MCP, the REST API, or both. One API key pair (sent as an `X-ApiKeys` header) serves both, and the key must belong to an Administrator. Keep keys in environment variables or your OS keychain, never in a repository.

- **MCP (primary).** Endpoint `https://cloud.tenable.com/mcp`. The skill uses it for template and policy lookup, creating, launching and monitoring the network scan, and reading results and plugin details. Tested on 2026-10-07: template lookup (`policy_templates`), `policy_list_policies`, `scan_create` with `asv`, `scan_launch`, `scan_status`, `scan_list_scans`, `scan_results`, `plugins_get_plugin_details`, and `workbenches_get_vulnerability_outputs`.
- **REST API (optional, for the web application scan).** The MCP has no web application scanning tools, so the optional scripted route uses the Web App Scanning v2 API: `GET /was/v2/templates` (find the `pci` template), `POST /was/v2/configs` (needs `name`, `owner_id` from `GET /session`, `template_id`, and a top-level `targets` list of public URLs), `POST /was/v2/configs/{config_id}/scans` to launch, `GET /was/v2/scans/{scan_id}` to poll, and `GET /was/v2/scans/{scan_id}/notes` for the reason if a scan aborts. Tested on 2026-10-07: create, launch, status polling, completion, and workbench import (the imported scan appeared with `scan_type` `was` and its failure count). Private targets are rejected.
- **PCI ASV API.** `GET /pci-asv/scans` lists scans imported into the workbench (tested, read-only). Submitting through the API was not tested.
- **PCI ASV Workbench (UI).** Importing scans, creating and submitting the attestation, and disputes happen here. Use "Import to ASV Workbench" in the scan list row menu.
- **Both together.** A typical run is the network scan through MCP, the web application scan in the workbench (or through the WAS v2 REST API if you want to script it), import of both in the UI, then results review through MCP with web application findings supplied by you.

## How to run

1. Clone the repository, then copy or symlink it into your Claude Code skills path (run both commands from the same directory):
   ```bash
   git clone https://github.com/jdelong-tenb/pci-asv-scan-copilot.git
   cp -r pci-asv-scan-copilot ~/.claude/skills/
   ```
2. Add the Tenable VM MCP server to Claude Code as an HTTP server at `https://cloud.tenable.com/mcp` with the `X-ApiKeys: accessKey=<ACCESS>;secretKey=<SECRET>` header (placeholders only; the API key must belong to an Administrator; follow Claude Code's documentation for the exact syntax), restart the session, and run `/mcp` to confirm it shows as connected. For REST calls, the agent needs shell access (for example `curl`) and reads the keys from the `TIO_ACCESS_KEY` and `TIO_SECRET_KEY` environment variables; never print or log them.
3. In a Claude Code session, say something like:
   - "Help me set up my quarterly PCI ASV scan"
   - "I need to run a PCI external vulnerability scan"
   - "Scan my payment web app for PCI"
   - "Which PCI findings can I dispute"
   - "Am I ready to submit my attestation"

The skill activates automatically from its description, or you can invoke it explicitly.

You can also run the utility script directly to preview what's already configured (run it from inside the cloned `pci-asv-scan-copilot` directory):
```bash
export TIO_ACCESS_KEY="your-access-key"
export TIO_SECRET_KEY="your-secret-key"
python3 scripts/list_pci_scans.py
```
Optionally set `TIO_BASE_URL` to use a host other than `https://cloud.tenable.com`. The script lists scans whose name contains "pci" or "asv" (the scan list does not reliably expose the template, so this is a name match and can miss or over-match), flags scans whose names suggest the internal template, and lists available PCI-related templates (`asv` is submittable; `pci` is internal and never submittable). It does not list web application scans. Use it only as a quick preview.

## What it produces

The skill walks you through five phases conversationally, checking real account state at each step. By the end you have:

- A completed PCI ASV network scan (and guidance for the PCI web application scan) against your declared external scope
- Findings grouped by PCI DSS v4.0.1 requirement with plain-language explanations
- A prioritized list: findings to remediate (blocks attestation) vs. dispute candidates (false positives / compensating controls)
- A preliminary readiness verdict: Ready / Conditional (disputes pending) / Not ready (with specific action items)

## Known limitations

See [SKILL.md Known Limitations](SKILL.md#known-limitations) — most importantly: this skill provides technical guidance, not official PCI DSS compliance advice. Your QSA is the authoritative source.

## License

MIT — see [LICENSE](LICENSE).
