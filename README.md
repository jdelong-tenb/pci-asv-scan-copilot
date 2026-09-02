# PCI ASV Scan Copilot

A Claude Code skill that walks you through the full quarterly PCI ASV (Approved Scanning Vendor) external scan cycle — from scan configuration to attestation readiness.

## What it does

PCI DSS Requirement 11.3.2 requires quarterly external vulnerability scans of your cardholder data environment (CDE) by an Approved Scanning Vendor. The cycle has five places people commonly get stuck:

1. **Scan setup** — selecting the right PCI ASV scan policy/template and configuring the correct external-facing targets
2. **Launch and monitoring** — starting the scan and tracking progress until completion
3. **Finding review** — understanding which failures actually block attestation, with findings grouped by PCI DSS v4.0 requirement
4. **Dispute identification** — distinguishing genuine false positives and compensating-control candidates from findings that need to be remediated
5. **Attestation readiness** — confirming what needs to be in order before you submit

This skill reads your real Tenable Vulnerability Management account state via the API and walks you through whichever phase you're in.

This is a community-built skill, not official Tenable support and not PCI DSS compliance advice. Consult your QSA for authoritative compliance guidance.

## Prerequisites

- Claude Code (or another skill-compatible client) with the `tenable-vpod` MCP server configured and connected.
- A Tenable Vulnerability Management account with API access. Generate an API key pair under **Settings > My Account > API Keys**.
- Your external-facing CDE targets (IP addresses, hostnames, or CIDR ranges) identified before you start.

## How to run

1. Copy or symlink this directory into your Claude Code skills path:
   ```bash
   cp -r pci-asv-scan-copilot ~/.claude/skills/
   ```
2. Ensure the `tenable-vpod` MCP server is configured in your Claude Code environment.
3. In a Claude Code session, say something like:
   - "Help me set up my quarterly PCI ASV scan"
   - "I need to run a PCI external vulnerability scan"
   - "Walk me through setting up a PCI scan for attestation"

The skill activates automatically from its description, or you can invoke it explicitly.

You can also run the utility script directly to preview what's already configured:
```bash
export TIO_ACCESS_KEY="your-access-key"
export TIO_SECRET_KEY="your-secret-key"
python3 scripts/list_pci_scans.py
```
This lists your existing PCI-related scans and available PCI ASV scan templates — useful for verifying what's already set up before you start.

## What it produces

The skill walks you through five phases conversationally, checking real account state at each step. By the end you have:

- A completed PCI ASV scan against your declared external scope
- Findings grouped by PCI DSS v4.0 requirement with plain-language explanations
- A prioritized list: findings to remediate (blocks attestation) vs. dispute candidates (false positives / compensating controls)
- A readiness verdict: Ready / Conditional (disputes pending) / Not ready (with specific action items)

## Known limitations

See [SKILL.md Known Limitations](SKILL.md#known-limitations) — most importantly: this skill provides technical guidance, not official PCI DSS compliance advice. Your QSA is the authoritative source.

## License

MIT — see [LICENSE](LICENSE).
