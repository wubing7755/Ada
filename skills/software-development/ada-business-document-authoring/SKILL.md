---
name: ada-business-document-authoring
description: "Use when evidence must become a decision-ready business document, executive brief, proposal, status report, or polished DOCX/PDF for non-technical readers. Covers audience framing, source traceability, narrative structure, visual evidence, and rendered-deliverable QA; use ada-document-artifacts for format mechanics only."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [documents, business-writing, executive-brief, docx, evidence]
    related_skills: [ada-document-artifacts, ada-doc-comparison-analysis]
---

# Business Document Authoring

Turn verified source material into a document that a non-technical reader can use to make a decision. This Skill owns argument, evidence, audience, and delivery quality. File conversion and low-level DOCX/PDF mechanics remain delegated to the matching document tool.

## Activation

Use for executive briefs, proposals, stakeholder reports, decision memos, project summaries, client-facing analysis, and polished Word/PDF delivery where factual traceability matters.

## Do Not Use When

- The task is only format conversion, merge/split, or template manipulation; use `ada-document-artifacts`.
- The deliverable is a normative SRS or traceability matrix; use the relevant Ada SRS Skill.
- The user wants an exhaustive engineering audit rather than an audience-shaped document.
- Source material or permission to disclose it is missing.

## Inputs

Establish before drafting:

- reader, decision, and desired action;
- source documents and their authority;
- required format, template, length, language, and deadline;
- confidentiality and redaction boundaries;
- claims that require citations, calculations, or visual evidence.

## Workflow

### 1. Build an evidence map

Create a private working table: claim → source → confidence → audience relevance → planned location. Separate fact, inference, recommendation, and unknown. Never convert an unsupported inference into a factual sentence.

### 2. Choose a decision structure

Default structure:

1. purpose and decision requested;
2. current situation and constraints;
3. evidence and options;
4. recommendation with trade-offs;
5. risks, mitigations, and next actions;
6. sources or appendix.

Use a different structure only when the reader or template requires it.

### 3. Draft for the reader

- Lead each section with its conclusion.
- Translate implementation detail into impact, risk, cost, or choice.
- Define unavoidable technical terms once.
- Keep evidence close to the claim it supports.
- Use tables for comparison and charts only when they reduce cognitive load.
- Preserve material uncertainty and dissenting evidence.

### 4. Create the delivery artifact

Load the relevant document-format Skill only after content stabilizes. Preserve heading hierarchy, table semantics, source notes, alt text, page numbering, and reusable styles. Do not embed credentials, private paths, memory, or hidden review notes.

### 5. Inspect the rendered result

A successful file write is not delivery proof. Render or open the actual artifact and inspect:

- page breaks, clipping, overflow, and orphan headings;
- table width, chart labels, image resolution, and captions;
- consistent fonts, numbering, margins, and headers/footers;
- hyperlinks, citations, filename, and expected output location.

Revise and re-render until the artifact is readable in its target form.

## Mandatory Checks

- Every material claim is sourced or explicitly labeled as inference/recommendation.
- Executive summary and detailed sections do not contradict each other.
- Numbers retain units, time period, population, and calculation basis.
- Redactions remove both visible content and accidental metadata where relevant.
- The final output contains no local credentials, private runtime state, or temporary paths.
- The rendered artifact, not only source Markdown, has been inspected.

## Stop Conditions

Stop and ask when the requested narrative conflicts with evidence, disclosure authority is unclear, the required template is unavailable, or a consequential calculation cannot be verified.

## Output Contract

Report:

- artifact path and format;
- intended audience and decision;
- sources used and important exclusions;
- verification performed on the rendered output;
- remaining uncertainty or disclosure caveats.
