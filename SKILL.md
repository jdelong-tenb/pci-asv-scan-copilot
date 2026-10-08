---
name: pci-asv-scan-copilot
description: Walks a PCI ASV user through the full three-month external scan cycle for network and web application targets — scan setup, launch and monitoring, finding review grouped by PCI DSS v4.0.1 requirement, dispute candidate identification, and a preliminary attestation readiness check. Invoke when someone says things like "help me set up my quarterly PCI ASV scan," "I need to run a PCI external vulnerability scan," "scan my payment web app for PCI," "which PCI findings can I dispute," or "am I ready to submit my attestation."
---

# PCI ASV Scan Copilot

## Why this exists

PCI DSS v4.0.1 Requirement 11.3.2 requires external vulnerability scans at least once every three months by an Approved Scanning Vendor (ASV). The scan-to-attestation cycle has five places users commonly get stuck: choosing the right scan template, configuring scope correctly (including web application URLs), interpreting which findings actually block attestation versus which are disputable, knowing what evidence a dispute needs, and knowing what must be in order before submitting. This skill walks through all five phases against your real account state.

This is a community-built skill, not official Tenable support and not PCI DSS compliance advice. It gives best-effort guidance. For authoritative interpretation, consult your QSA. The ASV's review in the PCI ASV Workbench is the only authoritative result.

**Scope:** external vulnerability scanning (ASV) of network/host targets (Tenable Vulnerability Management) and public-facing web applications via the PCI-scoped web application scan in the PCI workbench (a PCI-limited WAS scan, not the full Tenable Web App Scanning product), plus any externally facing system component that may provide access to the CDE (ASV Program Guide section 5.5). Does not cover internal scans, penetration testing, or other PCI DSS requirements. The customer owns scope.

## Before you start

Tell the user these up front:

- Tenable recommends no more than 5,000 assets per PCI scan; larger imports can fail or take hours. (Tenable PCI ASV User Guide, p. 104)
- PCI licensing counts unique IP addresses; web application FQDNs are resolved to IPs. The check happens when you submit an attestation, and an attestation whose asset count exceeds your licensed count is rejected (Tenable PCI ASV User Guide, pp. 11-13).
- The PCI ASV license includes the Nessus and WAS scanners with the PCI scan templates. The PCI web application template only covers the minimal PCI requirements, and Tenable recommends a full Web App Scanning license to scan and monitor web applications fully (Tenable PCI ASV User Guide, p. 14).
- You cannot create an attestation for a scan more than 90 days old, and dispute activity must finish before the scan report's 90-day expiration (Tenable PCI ASV User Guide, pp. 107-108).
- Each rescan is a separate scan and must be imported into the workbench. Passing results from several scans can be aggregated into one report for the period (ASV Program Guide sections 7.3 and 7.4).
- A dispute cannot be edited or deleted once the attestation is submitted. Cloning a dispute deletes the other disputes on the same attestation.
- If the subscription expires during the review period, Tenable cannot complete the report.
- The attestation is the customer's and cannot be outsourced. Evidence prepared with help, including from this skill, must be reviewed and attested by the customer (ASV Program Guide section 5.2).
- The ASV may discover extra domains or IPs (for example through MX records, redirects, or crawling). The customer must scan them or declare them out of scope (section 5.5.3).
- Shared hosting: coordinate scan interference with the ISP or host, or obtain the provider's passing scans (section 5.5.2).
- The final report is submitted per the payment brands' reporting requirements; ask your acquirer or payment brand where (section 7.9).

## How it connects

The skill works through Tenable's MCP, the REST API, or both. One API key pair (sent as an `X-ApiKeys` header) serves both, and the key must belong to an Administrator. Keep keys in environment variables or your OS keychain, never in a repository. For REST calls, the agent needs shell access (for example `curl`) and reads the keys from the `TIO_ACCESS_KEY` and `TIO_SECRET_KEY` environment variables; never print or log them.

- **MCP (primary).** Endpoint `https://cloud.tenable.com/mcp`. The skill uses it for template and policy lookup, creating, launching and monitoring the network scan, and reading results and plugin details. Tested on 2026-10-07: template lookup (`policy_templates`), `policy_list_policies`, `scan_create` with `asv`, `scan_launch`, `scan_status`, `scan_list_scans`, `scan_results`, `plugins_get_plugin_details`, and `workbenches_get_vulnerability_outputs`.
- **REST API (optional, for the web application scan).** The MCP has no web application scanning tools, so the optional scripted route uses the Web App Scanning v2 API: `GET /was/v2/templates` (find the `pci` template), `POST /was/v2/configs` (needs `name`, `owner_id` from `GET /session`, `template_id`, and a top-level `targets` list of public URLs), `POST /was/v2/configs/{config_id}/scans` to launch, `GET /was/v2/scans/{scan_id}` to poll, and `GET /was/v2/scans/{scan_id}/notes` for the reason if a scan aborts. Tested on 2026-10-07: create, launch, status polling, completion, and workbench import (the imported scan appeared with `scan_type` `was` and its failure count). Private targets are rejected.
- **PCI ASV API.** `GET /pci-asv/scans` lists scans imported into the workbench (tested, read-only). Submitting through the API was not tested.
- **PCI ASV Workbench (UI).** Importing scans, creating and submitting the attestation, and disputes happen here. Use "Import to ASV Workbench" in the scan list row menu.
- **Both together.** A typical run is the network scan through MCP, the web application scan in the workbench (or through the WAS v2 REST API if you want to script it), import of both in the UI, then results review through MCP with web application findings supplied by you.

## Phase 1 — Scan setup

Two scans, not one:

1. **Network scan** — Nessus Scanner scan using the "PCI Quarterly External Scan" template (template `asv`) for IP addresses and ranges.
2. **Web application scan** — PCI-scoped web application scan ("PCI ASV" in the workbench picker; "PCI" in Tenable documentation) for web application FQDNs entered as URLs such as http://www.example.com. Both can be imported into the PCI ASV Workbench, but the workbench requires a PCI WAS scan to be combined with a PCI Quarterly External Scan before submitting for ASV review (in New Scan Results, select both scans and click Start Attestation; the workbench will not start an attestation for a web application scan unless a PCI Quarterly External scan is included, Tenable PCI ASV User Guide p. 107, which points to the knowledge base article "How To Combine multiple PCI ASV Scans").

The "Internal PCI Network Scan" tile (template `pci`) may also appear in the VM scan template list. It is not submittable. **Never use template `pci` for the submitted scan.**

Steps:

1. Ask for scope: IPs and ranges, plus every fully qualified domain name, virtual host, and web application URL in scope, including URLs that cannot be reached by crawling from the home page (ASV Program Guide v4.0 r2 section 5.5). The skill cannot verify scope. PCI expects a web application scan whenever there are public-facing web applications in the CDE; remind the user, but whether to run it is the customer's decision.
2. Call `policy_templates` and look up the template named `asv` ("PCI Quarterly External Scan") at run time. The MCP tool returns a plain-text list of template names and UUIDs without the display titles, so match on the name. Do not hardcode UUIDs. If it is not listed, stop and tell the user to check that their subscription includes PCI ASV.
3. Call `policy_list_policies` **only** to spot reuse of the wrong template (for example an existing scan or policy built on `pci` or a basic network template). The submitted scan always uses the unmodified PCI Quarterly External Scan template. Customers may not modify checks, severities, or scan parameters because the ASV manages the scan solution (ASV Program Guide section 5.2). Do not offer to tune or clone a policy.
4. Only Administrator users can perform the scanning steps (Tenable PCI ASV documentation, Get Started). Ask the user to confirm the account and API key belong to an Administrator.

**Internal scans are separate.** PCI DSS also requires internal scans at least once every three months. They use the "Internal PCI Network Scan" template (`pci`), run on the Vulnerability Management side like any other scan, and cannot be imported into the PCI workbench, so they are never submitted for ASV review. If asked, point to the template, but do not manage or track internal scans; that is the customer's responsibility. Tenable PCI ASV customers are required to own a full Tenable One Vulnerability Management license, which is where internal scans run (Tenable PCI ASV User Guide, p. 13).

**Scan configuration health check** before Phase 2:

1. **Target list must be non-empty.** If none was provided, stop and prompt again.
2. **External scan, external targets.** Flag RFC1918 addresses (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16). An external ASV scan cannot reach private addresses from outside, so these targets will not produce a valid result. Ask the user to confirm or correct to public IPs.
3. **Correct template confirmed.** The selected template must be `asv`, not `pci`, "basic network scan," "advanced scan," or any agent-based template.

Do not tell the user to position or confirm "your Tenable scanner" for the ASV scan. The ASV manages the scan solution (ASV Program Guide section 5.2).

**Example user prompts:** "Help me set up my quarterly PCI ASV scan," "I need to configure a PCI external scan," "Scan my payment web app for PCI."

## Phase 2 — Launch and monitor

### Network scan

Call `scan_create` with `name` "PCI Quarterly External Scan - [YYYY-MM-DD]", `targets` (JSON array of IP/hostname/CIDR strings), and `template` "asv". It returns the scan ID as plain text, so read the ID from the text. Then `scan_launch` with the scan_id. When `scan_status` reports completed, tell the user to import it from the VM scan list row menu ("Import to ASV Workbench"). If REST access is available, confirm it appears in `GET /pci-asv/scans` with `scan_type` `nessus` and `import_status` complete.

**Workbench fallback:** if `scan_create` with `asv` fails or the import does not appear in the workbench, have the user create it from the workbench (Create Scan > PCI Quarterly External Scan) and give you the resulting scan name/ID to monitor.

The API key used must belong to an Administrator.

Monitor with `scan_status` periodically:
- **pending / running:** "Scan is running — typically takes 30–90 minutes for a standard external scope."
- **completed:** proceed to Phase 3
- **publishing:** results are being finalized; keep polling.
- **canceled / aborted:** explain the failure, offer to re-launch
- **error:** show the error and suggest re-checking target reachability

Do not proceed to Phase 3 until status is `completed`.

For a web application scan run through the REST API, statuses seen are queued, pending, running, completed and aborted; on aborted, call `GET /was/v2/scans/{scan_id}/notes` for the reason.

### Web application scan

The Tenable VM MCP has no web application scanning tools (its `scan_create` builds VM scans only), and this skill does not use general WAS scan templates. Guide the user through the PCI workbench: "Create a Scan - PCI WAS Scan", which needs a Name and Targets entered as URLs. This is a PCI-limited scan, not general Web App Scanning. The WAS API rejects private targets (for example http://10.0.0.133) with "Private target ... is not allowed" (tested 2026-10-07), so web application targets must be publicly reachable. The WAS v2 REST API route was tested end to end on 2026-10-07: `POST /was/v2/configs` with the `pci` template, `owner_id`, and a top-level `targets` list creates the configuration, `POST /was/v2/configs/{config_id}/scans` launches it, `GET /was/v2/scans/{scan_id}` reports status (queued, pending, running, completed or aborted), and `GET /was/v2/scans/{scan_id}/notes` gives the reason for an abort. A completed scan was then imported with "Import to ASV Workbench" in the WAS scan row menu (importing through the API was not tested). Default to guiding the user through the workbench; offer the REST route only if the user wants to script it and has an Administrator API key.

### Import into the workbench

Each completed scan, including every rescan (each rescan is a new scan), must be imported into the PCI ASV Workbench before it can be attached to an attestation. For web application scans, use "Import to ASV Workbench" in the WAS scan row menu. Remind the user after every scan and rescan.

### Testing rules

- **Web application testing:** unauthenticated testing is the PCI minimum (ASV Program Guide section 6, Table 1, Web Applications). Tenable advises against adding credentials to PCI ASV scans. Do not suggest adding credentials; if the user asks, tell them to discuss it with their ASV.
- **WAF/IPS:** for the scan window only, advise configuring active protection systems (for example IPS or rate-based WAF rules) to monitor and log, but not block, the ASV scanner IPs, or to consistently pass non-attack traffic. Reapply the normal configuration when the scan finishes. No allow-listing or extra access is required. A scan left inconclusive because of interference is reported as failed (ASV Program Guide sections 5.6 and 7.6).

**Example user prompts:** "Start the scan now," "Check the scan status," "Is my PCI scan done yet?"

## Phase 3 — Review findings

**Network scan:** call `scan_results` with the completed scan_id, and `scan_host_details` for per-host detail (untested; skip it if it is not in your MCP tool list). If plugin 33929 (NOT COMPLIANT) is present the scan failed; 33930 (COMPLIANT) means it passed. 33930 does not certify overall compliance and does not replace the ASV's review.

`scan_results` returns integer severity levels (0=info through 4=critical), not CVSS scores. Call `plugins_get_plugin_details` for **every** finding, not only severity >= 2, to get the CVSS score, CVEs, and solution. Do not skip low-severity findings: automatic failures can have low CVSS.

**Web application scan:** the MCP has no WAS tools. Work from findings the user exports or pastes from the web application scan. Treat them as user-supplied and say so in your output.

**Per-finding handling.** Never collapse findings by plugin alone. The same web application plugin firing on different URLs or parameters is a separate, legitimate finding. Keep URL, parameter, and plugin output with each finding.

**CVSS.** A CVSS base score of 4.0 or higher fails the scan (ASV Program Guide sections 6.2.1 and 6.3.2, Table 2). ASVs score with CVSS v3.1, falling back to v3.0 and then v2.0 (if there is no NVD score, the ASV calculates v3.1). Use the plugin's CVSS v3.x score in that order of preference as an estimate, and tell the user the score in the ASV report governs.

**What counts as a failure:**

- Automatic failures regardless of CVSS score (ASV Program Guide section 6.3.3 exception 4 and Table 1). Web applications: SQL injection, cross-site scripting, directory traversal, HTTP response splitting or header injection. Network components: backdoors/malware, default accounts and passwords, unrestricted DNS zone transfers, unsupported operating systems, SSL/early TLS, internet-reachable cardholder-data databases. Flag these separately and never downgrade them on a low CVSS score.
- A purely denial-of-service vulnerability (for example, CVSS confidentiality and integrity impact both "None") is not ranked as a failure (section 6.3.3 exception 3). The ASV applies this exception; only flag it as a likely non-failure.
- Missing patches for High or Medium findings must be installed or covered by a compensating control. "No patch is available" is not itself an exception (section 7.7 note).
- Special Notes to Scan Customer: the ASV must declare the report FAILED until all applicable declarations are obtained and reviewed (section 7.2). Special Notes alone do not cause a scan failure or supersede CVSS scoring (section 6.1, footnote 1). Report the scan as FAILED until the user confirms the declarations are reviewed.
- Load balancers: the ASV needs the customer's documented assurance that the environment behind them is synchronized, or it adds a Special Note (section 6.1). Ask for it.

**PCI DSS v4.0.1 requirement mapping** (plugins carry no PCI cross-references; confirm any mapping with the QSA):

| Finding type | DSS Req | Plain-language label |
|---|---|---|
| Expired or self-signed TLS certificate | 4.2.1 | Encrypted transmission requirement |
| Weak or deprecated cipher suites (SSLv3, TLS 1.0, RC4, DES, 3DES, EXPORT) | 4.2.1 | Encrypted transmission requirement |
| Unpatched OS or software with known CVE (high CVSS) | 6.3.3 | Security patches and updates |
| Unnecessary exposed services or ports | 2.2.4 and 1.2.5 (1.3.1 if the service is in the CDE) | Only necessary services enabled; network access controls (1.3.2 covers outbound traffic, not this) |
| Default or vendor-supplied credentials | 2.2.2 | Vendor-supplied defaults |
| SQL injection or cross-site scripting (custom web apps) | 6.2.4 | Secure coding practices |
| Remote code execution or privilege escalation | 6.3.3 | Security patches and updates |
| HTTP without HTTPS redirect | 4.2.1 | Encrypted transmission requirement |

Present findings grouped by DSS requirement, not by CVSS score alone. Lead with the requirement number and plain-language name. For each finding, state in one sentence what it is and what it means for the cardholder environment.

**Example user prompts:** "Show me the failures from my PCI scan," "Which findings will block my attestation?"

## Phase 4 — Dispute candidates

Each dispute is assessed **per finding** (per URL and parameter for web application findings), never per plugin. Recast rules do not apply to results from the two ASV templates, so disputes are the route for contested findings. The ASV, not the user or this skill, decides whether a dispute is accepted (ASV Program Guide sections 7.7 and 7.8).

Dispute categories drawn from the ASV Program Guide:

- **False positive:** the scanner triggered on a pattern that does not represent a real vulnerability on this host.
- **Disputed CVSS score:** the plugin's score does not match the vulnerability as it exists in this environment.
- **Compensating control:** a control that satisfies the intent though the finding cannot be remediated directly.

Common examples: TLS flagged on a load balancer because of a negotiation artifact (document the architecture); version banners flagged on software that is patched and current (document the patch level). Open ports that serve legitimate CDE functions (for example 443 for a payment page) are only disputable where the finding itself is a false positive or covered by a compensating control; documenting business justification alone is not a dispute basis.

Do not propose a dispute category that has no basis in the ASV Program Guide, such as "no public exploit plus a mitigating access control."

Evidence rules:

- Evidence should be system generated (screen captures, configuration files, version and patch lists) with a description of when, where, and how it was obtained. The customer attests that it is accurate and complete (section 7.7).
- Dispute outcomes are not carried forward. Evidence is resubmitted and re-evaluated for each scan period (section 7.7).
- One dispute in the workbench can cover several failures that share a plugin ID, but the evidence must cover every attached URL or host.

For each candidate give: (1) category, (2) evidence to collect, (3) the per-finding scope (URL/parameter or host). Call `workbenches_get_vulnerability_outputs` where scanner output would strengthen or weaken the case.

**Example user prompts:** "Which PCI findings can I dispute?" "This finding is a false positive on our load balancer — how do I document it?"

## What you do in the PCI ASV Workbench

This skill does not create or submit attestations. After both scans are imported, tell the user that the workbench requires a PCI WAS scan to be combined with a PCI Quarterly External Scan before submitting for ASV review (in New Scan Results, select both scans and click Start Attestation; the workbench will not start an attestation for a web application scan unless a PCI Quarterly External scan is included, Tenable PCI ASV User Guide p. 107, which points to the knowledge base article "How To Combine multiple PCI ASV Scans"), and then to:

1. Create an attestation draft.
2. Mark assets that are not in the CDE as out of scope. The customer is attesting they are segmented from the CDE; the ASV reports excluded components on the attestation (ASV Program Guide sections 7.3 and 5.5.3).
3. Open a dispute for each failure. A failure left undisputed at submission makes the ASV reviewer fail the attestation.
4. Submit for ASV review.

Tenable does not provide in-depth consulting on fixes (Tenable PCI ASV documentation, Welcome page).

## Phase 5 — Preliminary attestation readiness

This is a preliminary readiness assessment only. The ASV's review in the workbench is the only authoritative result. Base it on the network scan results the skill can read plus the web application findings and dispute information the user provides.

**1. Asset coverage.** Compare the Phase 1 target list against the scan's own host list from `scan_results` and `scan_host_details`. Do **not** rely on `workbenches_list_assets_with_vulnerabilities` alone: hosts with no findings are expected to be absent there. Any in-scope host missing from the scan's host list needs explaining (unreachable during the window, or explicitly excluded with documented justification).

**2. Unresolved failing findings.** Count findings with CVSS base score 4.0 or higher, plus automatic failures regardless of CVSS, that are not covered by an accepted dispute or resolved by remediation. Include the user-supplied web application findings.

**3. Dispute documentation.** For each Phase 4 candidate, confirm the user has the evidence assembled and has opened the dispute in the workbench.

**4. Special Notes and load balancers.** Confirm all applicable declarations are obtained and reviewed; otherwise the report is FAILED.

**5. Combined scans.** If a PCI WAS scan is part of the submission, confirm the user has combined it with a PCI Quarterly External Scan in the workbench (select both scans in New Scan Results and click Start Attestation; required before submitting for ASV review). Combining was not tested by this skill.

**6. Cycle and expiry.** The cycle is three months, not calendar quarters.
- State the completion date and the date three months later as the next-scan deadline.
- Separately, each ASV scan report carries a scan expiration 90 days after the scan completes (ASV Program Guide Appendix A, A.3). Tenable's workbench enforces the same window: you cannot create an attestation for a scan more than 90 days old, and dispute activity must be completed before the report's 90-day expiration (Tenable PCI ASV User Guide, Create an Attestation, pp. 107-108). Disputes must be resolved and the attestation finalized while the scan is still valid, otherwise a new scan is needed.
- Report days since completion against both and name whichever comes first.
- Call `scan_list_scans` and look for prior completed PCI ASV scans (match on name; this is approximate). If the previous completion is more than three months before this one, flag the gap: a QSA may ask about it. If none is found, say so and suggest confirming history with the QSA.
- After any significant change, PCI DSS 11.3.2.1 also requires an external scan with CVSS 4.0 or higher findings resolved. That scan need not be performed by an ASV, but must be done by qualified, independent personnel.

**Readiness verdict:**
- **Ready to submit (preliminary):** no unresolved failing findings, all in-scope assets accounted for, WAS scan combined with the external scan (if used), Special Notes reviewed, within the expiry and deadline.
- **Conditional — disputes pending:** failing findings remain but all have disputes in progress. Cannot pass until the ASV accepts them.
- **Not ready — findings to remediate:** list the specific findings (plugin ID, host or URL/parameter, CVSS score), highest first.

**Example user prompts:** "Am I ready to submit my attestation?" "What do I still need to fix before I can submit?"

## MCP tools used

- `policy_list_policies` — spot reuse of the wrong template only
- `policy_templates` — look up the `asv` template at run time
- `scan_create` — create the network scan (`targets` is a JSON array; `template` "asv"; creation, launch and workbench import tested, workbench fallback in Phase 2)
- `scan_launch` — launch the scan
- `scan_status` — monitor progress
- `scan_results` — completed scan findings and host list
- `scan_host_details` — per-host finding detail (untested)
- `plugins_get_plugin_details` — CVSS, CVEs, solution for every finding
- `workbenches_get_vulnerability_outputs` — raw scanner output for dispute evidence
- `workbenches_list_assets_with_vulnerabilities` — secondary cross-check only; absent hosts may simply have no findings
- `scan_list_scans` — find prior PCI ASV scans (Phase 5)

Tools are referred to by bare name. Your client may show them with a prefix that depends on what you named the MCP server (for example `mcp__<server-name>__scan_create`). There are no web application scanning tools.

## Known limitations

- **Not a QSA.** This skill gives technical guidance. Your QSA is the authoritative source.
- **ASV decides.** ASV scan reports, attestation, and dispute decisions come from your ASV, not this skill.
- **Web application scan has no MCP tools.** It defaults to guided steps in the PCI workbench and is limited to PCI scope; the MCP has no tools for it, and web application findings are user-supplied. The optional WAS v2 REST route (create, launch, poll, complete) and the workbench import were tested on 2026-10-07; importing through the API was not.
- **Tested.** Tested on 2026-10-07: network scan creation, launch, completion and workbench import (`scan_create` with `asv`, `scan_launch`, `scan_status`, then "Import to ASV Workbench"), and WAS `pci` configuration creation, launch (`POST /was/v2/configs/{config_id}/scans`), polling, completion (about two hours against a deliberately vulnerable test site) and workbench import. Not tested: combining the two scans, attestation, disputes, submission, and API-based import, which happen in the PCI ASV Workbench and with the ASV. Details of what was observed: `scan_create` with `asv` returns the scan ID as plain text; `scan_status` moves running, publishing, completed (a scan against an unroutable address took about 16 minutes on the Tenable cloud scanner); a completed scan does not appear in the PCI ASV Workbench until it is imported from the VM scan list row menu, after which `GET /pci-asv/scans` showed it with `scan_type` `nessus` and `import_status` complete.
- **Not yet tested.** `scan_host_details` and `workbenches_list_assets_with_vulnerabilities`; confirm they exist in your MCP tool list.
- **Scope completeness relies on what you tell the skill.** It can only verify the targets in the scan.
- **CVSS 4.0 is the ASV Program Guide threshold**, not the text of DSS 11.3.2. Some ASVs apply additional criteria. Confirm with your ASV.
