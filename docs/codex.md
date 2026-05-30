# Codex setup notes

This repository is written primarily for Claude Code, but the same skills and MCP
servers can be used from Codex with a small amount of local setup.

## Install the skills

Clone the repository, then copy the two skill directories into Codex's skill
directory:

```powershell
git clone https://github.com/TaewoooPark/scholar-megasearch.git
cd scholar-megasearch

$skills = Join-Path $env:USERPROFILE ".codex\skills"
New-Item -ItemType Directory -Force -Path $skills | Out-Null
Copy-Item -Recurse -Force .\skills\scholar-megasearch (Join-Path $skills "scholar-megasearch")
Copy-Item -Recurse -Force .\skills\arxiv-search (Join-Path $skills "arxiv-search")
```

Restart Codex after copying the skills so the new `SKILL.md` files are loaded.

## Create local Python environments

```powershell
$skillVenv = Join-Path $env:USERPROFILE ".codex\skill_venv"
$paperVenv = Join-Path $env:USERPROFILE ".codex\paper_search_mcp_venv"

py -3.12 -m venv $skillVenv
& "$skillVenv\Scripts\python.exe" -m pip install --upgrade pip
& "$skillVenv\Scripts\python.exe" -m pip install -r .\setup\requirements.txt

py -3.12 -m venv $paperVenv
& "$paperVenv\Scripts\python.exe" -m pip install --upgrade pip
& "$paperVenv\Scripts\python.exe" -m pip install git+https://github.com/openags/paper-search-mcp.git
```

## Register MCP servers

Use your own email address for Unpaywall. It is used for polite API access and
should not be committed to the repository.

```powershell
codex mcp add arxiv-mcp-server -- uvx arxiv-mcp-server
codex mcp add asta --url https://asta-tools.allen.ai/mcp/v1

$paperPython = Join-Path $env:USERPROFILE ".codex\paper_search_mcp_venv\Scripts\python.exe"
codex mcp add paper-search-mcp `
  --env PAPER_SEARCH_MCP_UNPAYWALL_EMAIL=you@example.com `
  -- $paperPython -m paper_search_mcp.server
```

Verify the registrations:

```powershell
codex mcp list
codex mcp get paper-search-mcp
```

## arXiv rate limits

An arXiv HTTP 429 response is an external rate limit, not an installation error.
Use smaller result batches, add delays between searches, and start broad searches at
lower depth levels. When arXiv is rate-limited, fall back to Asta/Semantic Scholar,
DuckDuckGo, and Unpaywall-backed PDF acquisition.
