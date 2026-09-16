# VeriPay

> **Verify Before You Pay.**

**An AI-powered voice-based UPI payment system that verifies user intent and assesses payment risk before money moves.**

VeriPay introduces a **Context-Aware Payment Decision Engine (CPDE)** that acts as an intelligent decision layer between understanding a voice command and initiating a UPI payment. Instead of immediately executing a payment request, the system verifies intent, analyzes contextual risk, and provides explainable decisions before launching the user's preferred UPI application.

---

## The Problem

Existing voice-based payment systems typically follow a simple pipeline:

> **Listen → Pay**

If a command is misheard, the wrong recipient is selected, or a scammer pressures the user into making a payment, there is very little contextual verification before the transaction begins.

This problem particularly affects:

- Elderly users
- Digitally less-literate users
- Users making hands-free payments
- People vulnerable to social engineering scams

---

## The Solution

VeriPay follows a safer workflow:

> **Listen → Understand → Verify Intent → Assess Risk → Explain → Pay**

The core innovation is the **Context-Aware Payment Decision Engine (CPDE)**, which independently evaluates:

- **Intent Confidence** — Did the system correctly understand the user's request?
- **Payment Risk Score** — Should this payment be trusted based on context?

Only after these checks does VeriPay launch the preferred UPI application using **UPI Deep Linking**, where the user securely completes the payment using their own UPI PIN.

---

# Workflow of the Project

```text
          🎤 Voice Command
                 │
                 ▼
         Speech-to-Text (STT)
                 │
                 ▼
         Intent Extraction
                 │
                 ▼
      Context-Aware Payment
       Decision Engine (CPDE)
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
   Verify     Assess    Explain
   Intent      Risk     Decision
        └────────┼────────┘
                 ▼
        Launch Preferred
            UPI App
                 ▼
      User Enters UPI PIN
                 ▼
         Payment Completed
```

---

# CPDE Internal Architecture

```text
                 CPDE
                  │
 ┌────────────────┼────────────────┐
 ▼                ▼                ▼
Recipient     Intent          Context
Matching     Verification     Analysis
                  │
                  ▼
          Risk Assessment
                  │
                  ▼
          Decision Policy
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
   Proceed      Warn      Clarify
```

---

## Why CPDE is Different

| Capability | Typical Voice Payment | VeriPay |
|------------|-----------------------|----------|
| Voice Payment | ✅ | ✅ |
| Verifies Intent | ❌ | ✅ |
| Context-Aware Risk Analysis | ❌ | ✅ |
| Explainable Decisions | ❌ | ✅ |
| Recipient Ambiguity Detection | ❌ | ✅ |
| Baseline Evaluation | ❌ | ✅ |

---

## Key Features

- Voice-based UPI payment initiation
- Intent Verification before payment
- Recipient ambiguity detection
- Context-aware risk assessment
- Explainable AI decisions
- Secure UPI Deep Linking
- Future multilingual support

---

## Risk Assessment Signals

CPDE evaluates multiple contextual signals before making a payment decision.

| Signal | Purpose |
|---------|----------|
| Recipient Novelty | Detect first-time payees |
| Amount Deviation | Compare against historical payment behavior |
| Contact Ambiguity | Detect similar contact names |
| Urgency Language | Detect scam-style pressure phrases |
| High Amount Pattern | Flag unusual high-value transfers |

These signals contribute to an explainable **Risk Score**, while a separate **Intent Confidence Score** measures how accurately the user's request was understood.

---

## Decision Policy

| Risk Score | Action |
|------------|--------|
| **0.00 – 0.30** | Proceed |
| **0.31 – 0.60** | Warning + Confirmation |
| **0.61 – 1.00** | Mandatory Confirmation + Explanation |

If intent confidence falls below the threshold, VeriPay asks the user for clarification before any payment action is taken.

---

## Tech Stack

| Layer | Technology |
|--------|------------|
| Mobile App | Flutter |
| Backend | FastAPI |
| Language | Python |
| AI | Gemini / OpenAI |
| Speech Recognition | Speech-to-Text |
| Decision Engine | CPDE |
| Payment | UPI Deep Linking |
| Future Module | RAG |

---

## Project Structure

```text
VeriPay/
│
├── backend/
│   ├── app/
│   │   ├── config/
│   │   ├── intent/
│   │   ├── risk/
│   │   ├── policy/
│   │   ├── recipients/
│   │   ├── rag/
│   │   ├── logger.py
│   │   └── main.py
│   ├── data/
│   ├── demo/
│   ├── eval/
│   ├── logs/
│   └── tests/
│
├── frontend/
├── docs/
└── README.md
```

---

## Current Roadmap

- [x] Repository setup
- [x] FastAPI backend
- [x] Configuration module
- [x] Logging system
- [ ] Synthetic dataset creation
- [ ] Baseline voice payment pipeline
- [ ] Intent Verification module
- [ ] Risk Assessment module
- [ ] Decision Policy implementation
- [ ] Flutter integration
- [ ] Evaluation dashboard

---

## Target Audience

**Primary**

- Elderly users
- Digitally less-literate users
- Hands-free payment users

**Secondary**

- General UPI users seeking safer payments

---

## Novelty

> Existing systems: **Listen → Pay**

> VeriPay: **Listen → Understand → Verify Intent → Assess Risk → Explain → Pay**

Instead of treating voice payments as a speech-to-transaction pipeline, VeriPay treats every payment as a **decision problem**, ensuring users understand **why** a payment is allowed, warned, or paused before money moves.

---

## Built By:
Sneha 
Computer Science & Design, 3rd Year

**VeriPay - Verify Before You Pay.**
