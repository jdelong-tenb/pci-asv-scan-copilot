---
name: pci-asv-scan-copilot
description: Walks a PCI ASV user through the full quarterly external scan cycle — configuring targets and policy, launching and monitoring the scan, reviewing findings grouped by PCI DSS requirement, identifying dispute candidates, and confirming what is needed before attestation submission. Invoke when someone says things like "I need to run my quarterly PCI scan," "help me set up a PCI ASV scan," "I'm preparing for PCI attestation," "my PCI scan has failures I don't understand," or "how do I dispute a PCI finding."
---

# PCI ASV Scan Copilot

## Why this exists

PCI DSS Requirement 11.3.2 requires quarterly external vulnerability scans by an Approved Scanning Vendor (ASV). The scan-to-attestation cycle has five places users commonly get stuck: choosing the right scan template, configuring scope correctly, interpreting which findings actually block attestation versus which are disputable, knowing what compensating controls language to use, and knowing what must be in order before submitting. This skill walks through all five phases against your real account state.

This is a community-built skill, not official Tenable support and not official PCI DSS guidance. It reads your account via the Tenable VM API and gives best-effort guidance. For authoritative PCI DSS interpretation, consult your QSA.

## Phase 1 — Scan setup

Before creating the scan, confirm:
1. What is the scope? Ask the user for the IP addresses, hostnames, or CIDR ranges of all external-facing systems in their cardholder data environment (CDE). Typical targets: internet-facing web servers, load balancers, mail servers, DNS servers, and any other hosts that process, store, or transmit cardholder data.
2. Does a PCI ASV scan policy already exist?

Call `mcp__tenable-vpod__policy_list_policies` to check for existing PCI policies. If one exists with "PCI" or "ASV" in the name, offer to use it.

If none exists, call `mcp__tenable-vpod__policy_templates` to find the PCI ASV scan template. Look for the template named "pci" (for external ASV scans) or "agent_pci_internal" (for internal PCI scans). Present the matching templates to the user and confirm which one to use.

**Example user prompts that trigger this phase:**
- "Help me set up my quarterly PCI ASV scan"
- "I need to configure a PCI external scan"
- "Walk me through PCI scan setup"

## Phase 2 — Launch and monitor

Once scope and policy are confirmed, create the scan:

Call `mcp__tenable-vpod__scan_create` with:
- `name`: "PCI Quarterly External Scan - [YYYY-QN]"
- `targets`: JSON array of IP/hostname/CIDR strings (e.g., `["192.168.1.1", "10.0.0.0/24"]`) from Phase 1
- `template`: "pci" (the PCI ASV scan template name)

Confirm the scan was created (note the scan_id), then launch it:

Call `mcp__tenable-vpod__scan_launch` with the scan_id.

Monitor status by calling `mcp__tenable-vpod__scan_status` periodically. Report progress in plain language:
- **pending / running:** "Scan is running — typically takes 30–90 minutes for a standard external scope."
- **completed:** proceed to Phase 3
- **canceled / aborted:** explain the failure, offer to re-launch
- **error:** show the error and suggest re-checking target reachability

Do not proceed to Phase 3 until `mcp__tenable-vpod__scan_status` returns `completed`.

**Example user prompts:**
- "Start the scan now"
- "Check the scan status"
- "Is my PCI scan done yet?"

## Phase 3 — Review findings

Call `mcp__tenable-vpod__scan_results` with the completed scan_id. Retrieve per-host detail with `mcp__tenable-vpod__scan_host_details`.

After pulling scan results, first check for PCI compliance verdict plugins: plugin 33929 (NOT COMPLIANT) means the scan failed; plugin 33930 (COMPLIANT) means the scan passed. If 33930 is present, this scan itself needs no further remediation — that alone doesn't certify overall PCI compliance, so confirm with your QSA before treating attestation as complete. If 33929 is present, proceed to analyze the individual findings below.

For each finding with severity 2 (medium) or higher in the scan results. Note: scan_results returns integer severity levels (0=info through 4=critical), not CVSS scores. Call `mcp__tenable-vpod__plugins_get_plugin_details` for each severity >= 2 finding to get the actual CVSS base score — findings with CVSS base score >= 4.0 block PCI attestation. Call `mcp__tenable-vpod__plugins_get_plugin_details` to get the full plugin description, CVSS score, CVEs, and solution. Note: plugins do not include PCI DSS requirement cross-references — use the mapping table below to associate findings with DSS requirements.

**PCI DSS v4.0 requirement mapping** (use when the plugin lacks an explicit DSS cross-reference):

| Finding type | DSS Req | Plain-language label |
|---|---|---|
| Expired or self-signed TLS certificate | 4.2.1 | Encrypted transmission requirement |
| Weak or deprecated cipher suites (SSLv3, TLS 1.0, RC4, DES, 3DES, EXPORT) | 4.2.1 | Encrypted transmission requirement |
| Unpatched OS or software with known CVE (high CVSS) | 6.3.3 | Security patches and updates |
| Unnecessary open network services or ports | 1.3.2 | Network access controls |
| Default or vendor-supplied credentials | 2.2.2 | Vendor-supplied defaults |
| SQL injection or cross-site scripting | 6.2.4 | Secure coding practices |
| Remote code execution or privilege escalation | 6.3.3 | Security patches and updates |
| HTTP without HTTPS redirect | 4.2.1 | Encrypted transmission requirement |

Present findings grouped by DSS requirement, not by CVSS score alone. Lead with the requirement number and plain-language name. For each finding, state in one sentence what the finding is and what it means for the cardholder environment.

**Example user prompts:**
- "Show me the failures from my PCI scan"
- "Which findings will block my attestation?"
- "Explain the TLS failures in my scan"

## Phase 4 — Dispute candidates

ASV disputes are appropriate when a finding is:
1. A known false positive (the scanner triggered on a pattern that does not represent a real vulnerability on this host)
2. Fully mitigated by a compensating control (a control that satisfies the DSS intent even though the specific finding cannot be remediated directly)

**Common disputable finding categories:**

- **SSL/TLS false positives on load balancers:** A scanner may flag TLS as weak due to a protocol version negotiation artifact where the balancer actually terminates traffic before the backend. If the certificate and cipher suite on the balancer itself are PCI-compliant, document the architecture.
- **Informational banner disclosures:** Version banners that reveal software version numbers are sometimes flagged. If the software itself is patched and current, document that the version display does not reflect actual vulnerability exposure.
- **Open ports serving legitimate cardholder data functions:** Port 443 for a payment page or port 25 for a PCI-scoped mail relay are required by the business. Document the justification.
- **Vulnerability with no public exploit and a mitigating access control:** A high CVSS score where the attack vector requires authenticated local access, and that access is demonstrably controlled.

For each potential dispute, provide:
1. The dispute category (false positive vs. compensating control)
2. Evidence the user needs to collect (architecture diagram, policy screenshot, version proof)
3. Standard DSS language for the attestation narrative

Call `mcp__tenable-vpod__workbenches_get_vulnerability_outputs` for any finding where more output context would strengthen or weaken the dispute case — this returns the actual scanner output text showing what was detected, which is essential for building a dispute case.

**Example user prompts:**
- "Which of these findings can I dispute?"
- "This finding is a false positive on our load balancer — how do I document it?"
- "What compensating controls language should I use?"

## Phase 5 — Attestation readiness check

Before submitting, confirm:

**1. All in-scope assets were scanned.**
Call `mcp__tenable-vpod__workbenches_list_assets_with_vulnerabilities` and cross-check against the target list from Phase 1. Any host in scope that does not appear in the results needs to be explained: was it unreachable during the scan window? Is it explicitly excluded with documented justification?

**2. No unresolved CVSS ≥ 4.0 findings.**
Call `mcp__tenable-vpod__scan_results` and count findings with severity medium or higher. Per the PCI ASV Program Guide, an ASV scan passes only when there are no vulnerabilities with CVSS base score ≥ 4.0 that are not covered by an accepted dispute or compensating control.

**3. Dispute documentation is complete.**
For each finding identified in Phase 4 as a dispute candidate, confirm the user has the required evidence assembled and has submitted the dispute through their ASV's dispute process.

**4. Scan is within the required window.**
The scan must have been completed within the past 90 days. Confirm the scan_results completion timestamp.

**Readiness verdict:**

- **Ready to submit:** No unresolved CVSS ≥ 4.0 findings, all assets accounted for, scan within 90 days.
- **Conditional — disputes pending:** CVSS ≥ 4.0 findings exist but all are flagged as disputes with documentation in progress. Cannot submit until the ASV accepts the dispute(s).
- **Not ready — findings to remediate:** List the specific findings (plugin ID, host, CVSS score) that must be fixed, ordered by CVSS score descending.

**Example user prompts:**
- "Am I ready to submit my PCI attestation?"
- "Check if my scan passes for attestation"
- "What do I still need to fix before I can submit?"

## MCP tools used

- `mcp__tenable-vpod__policy_list_policies` — check for existing PCI scan policies
- `mcp__tenable-vpod__policy_templates` — find the PCI ASV scan template
- `mcp__tenable-vpod__scan_create` — create the scan (`targets` is a JSON array of IP/hostname/CIDR strings; `template` is the template name string, e.g. "pci")
- `mcp__tenable-vpod__scan_launch` — launch the scan
- `mcp__tenable-vpod__scan_status` — monitor scan progress
- `mcp__tenable-vpod__scan_results` — retrieve completed scan findings
- `mcp__tenable-vpod__scan_host_details` — per-host finding detail
- `mcp__tenable-vpod__workbenches_list_assets_with_vulnerabilities` — check asset coverage
- `mcp__tenable-vpod__workbenches_get_vulnerability_outputs` — raw scanner output for dispute evidence (returns actual detected output text; essential for dispute cases)
- `mcp__tenable-vpod__plugins_get_plugin_details` — full plugin description, CVSS score, CVEs, and solution text per finding

## Known limitations

- **Not a QSA.** This skill gives technical guidance on scan setup and finding interpretation. It does not constitute PCI DSS compliance advice — your Qualified Security Assessor (QSA) is the authoritative source on what passes and what requires a dispute.
- **ASV dispute acceptance is your ASV's decision.** This skill can identify dispute candidates and help you assemble documentation, but the ASV makes the final acceptance call. Tenable's ASV dispute process is separate from this skill.
- **Scope completeness relies on what you tell the skill.** The skill can only verify that the hosts you put into the scan were scanned — it cannot discover hosts you didn't know were in scope. Conduct your own scoping exercise first.
- **CVSS ≥ 4.0 is the standard PCI threshold.** This comes from the PCI ASV Program Guide, not the text of DSS Req 11.3.2.1 itself (which governs external scan cadence/re-scans) — some ASVs apply additional criteria on top of it. Confirm with your ASV.
- **External scan positioning matters.** External ASV scans must be conducted from outside the CDE network perimeter. Confirm your Tenable scanner is positioned (or cloud-hosted) to scan from an external vantage point.
