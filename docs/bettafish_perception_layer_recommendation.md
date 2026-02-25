# Recommendation: Retaining and Refactoring the Public Narrative Module for Investment Use

## Purpose

This document provides a structured recommendation on whether and how to retain the existing BettaFish public-opinion architecture while upgrading the system for investment decision support.  
The goal is to preserve comprehensive market-wide narrative awareness while preventing social-media noise from contaminating investment judgement.

---

## Executive Summary

- The existing public-opinion architecture should be retained.
- Its role must be explicitly redefined as a Perception Layer, not an Investment Decision Layer.
- Only minimal, non-destructive prompt changes are required.
- Twitter, Reddit, and overseas news remain first-class inputs, but outputs must be mapped, structured, and gated before entering any investment workflow.

---

## Architectural Positioning

### Recommended Layering

[Perception Layer]  
└─ Narrative Radar Agent (Twitter / Reddit / Overseas News)  
↓  
[Analysis Layer]  
├─ Financial Statements Agent  
├─ Management & Capital Allocation Agent  
├─ Culture & Execution Agent  
↓  
[Judgement Layer]  
└─ Value Investor Judge  

The existing public-opinion module fully belongs in the Perception Layer.

---

## Role Definition: Narrative Radar (Perception Layer)

### Responsibilities

- Detect current market discussion themes  
- Identify rapidly spreading narratives  
- Surface emerging risks or controversies  
- Summarize market attention and sentiment distribution  

### Explicit Exclusions

- No buy / sell / hold opinions  
- No judgement on narrative correctness  
- No price prediction  
- No override of fundamental analysis  

This agent functions as an environment scanner, not a decision-maker.

---

## Prompt Adjustments (Minimal and Non-Destructive)

### 1. Source Focus and Scope

Primary sources:
- Twitter (X)
- Reddit (high-quality subreddits)
- English-language overseas financial and technology media

Excluded sources:
- Chinese social platforms
- Chinese news sources

Clarification:
This agent reports what is being discussed, not what is true.

---

### 2. Output Format: Hot-Topic Matrix

Each reporting cycle must output structured entries with the following fields:

- Topic
- Entity (company / sector / individual)
- Narrative Direction (positive / negative / mixed)
- Emotional Intensity (low / medium / high)
- Spread Velocity (new / ongoing / fading)
- Primary Platform (Twitter / Reddit / News)
- First Appearance (yes / no)

Free-form narrative summaries should be avoided.

---

### 3. Non-Decision Constraint

Mandatory prompt rules:
- Hot topics do not imply correctness
- Strong sentiment does not imply importance
- No investment recommendation is allowed

---

## Why This Layer Remains Critical

The Perception Layer provides:

1. Early risk detection (regulatory, governance, reputational)
2. Narrative-versus-fundamentals gap identification
3. Macro, industry, and cross-company sentiment context

These functions do not require investment judgement.

---

## Escalation Mechanism (Recommended)

Add a boolean output field:

"escalation_required": true | false

Set to true only when:
- A new theme emerges
- Narrative spreads rapidly
- Topic touches fundamentals, governance, or regulation

Only escalated items proceed to investment analysis.

---

## Guiding Principle

Preserve the radar.  
Remove the steering wheel.

---

## Intended Audience

Prompt engineers, agent-architecture designers, and investment-analysis system builders.
