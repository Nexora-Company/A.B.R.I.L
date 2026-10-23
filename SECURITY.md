# Security Policy

## Reporting a vulnerability

Report vulnerabilities privately using GitHub's [Private Vulnerability Reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) for this repository. Do not open a public issue.

Alternative: contact {{CONTACT_EMAIL}}.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | `{{TODO: confirm}}` |
| < 0.2   | No |

## What to include

- Affected version or commit
- Steps to reproduce
- Impact assessment
- Suggested fix (optional)

## What to expect

- Acknowledgement within `{{TODO: set SLA}}`
- Status updates every `{{TODO: set cadence}}`
- Coordinated disclosure after a fix is available

## Coordinated disclosure

Please allow time for a fix before public disclosure.

## Scope

In scope (for an AI terminal assistant):
- Prompt injection that bypasses identity or safety rules
- Data leakage (files, environment, memory)
- Restriction evasion (executing actions without confirmation)
- Vulnerable dependencies
- Secret or credential exposure

Out of scope:
- Issues in Ollama or upstream models
- Social engineering
- Denial of service on the local machine

## Acknowledgements

`{{TODO: hall of fame}}`

## Reminder for maintainers

Enable Private Vulnerability Reporting in the repository settings before publishing.