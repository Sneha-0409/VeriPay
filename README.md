# VeriPay

> **Verify Before You Pay.**

**An AI-powered, voice-assisted UPI payment risk assessment system designed to verify payment intent, detect suspicious transactions, and provide contextual risk recommendations before payment authorization.**

VeriPay introduces a **Context-Aware Payment Decision Engine (CPDE)** that acts as an intelligent decision layer between understanding a user's payment instruction and initiating a payment. Rather than immediately acting on a voice command, VeriPay transcribes the instruction, extracts transaction details, evaluates fraud risk, and considers contextual signals to generate an explainable recommendation.

The proposed workflow allows users to review the payment and proceed through their preferred UPI application, where they complete authorization using their UPI PIN.

---

## The Problem

Traditional voice-based payment workflows can be vulnerable to:

- Speech recognition errors and incorrect payment details.
- Recipient selection mistakes and ambiguous contact names.
- Social engineering and scam-induced payment decisions.
- Unusual transactions that may not be adequately assessed by transaction-level fraud scores alone.

This can particularly affect:
- Elderly users.
- Digitally less-literate users.
- Users making hands-free payments.
- People vulnerable to social engineering scams.

A conventional voice payment pipeline primarily focuses on understanding a command and initiating a transaction. VeriPay explores an additional layer of verification and contextual risk assessment before payment authorization.

---

## The Solution

VeriPay follows a safety-oriented workflow:

> **Listen → Understand → Verify Intent → Assess Risk → Explain → Pay**

The system combines three major components:

1. **Voice Processing:** Converts spoken payment instructions into text using speech recognition.
2. **Fraud Risk Prediction:** Uses a trained machine learning model to estimate transaction-level fraud probability.
3. **Context-Aware Payment Decision Engine (CPDE):** Combines fraud probability with contextual information to generate payment risk recommendations.

The objective is to bridge the gap between predicting potentially fraudulent transactions and providing actionable pre-payment decisions.

---

## System Workflow

```text
              🎤 Voice Command
                     |
                     v
             Speech-to-Text
              (Whisper Tiny)
                     |
                     v
             Intent Extraction
          (Recipient and Amount)
                     |
                     v
       Context-Aware Payment Decision
                Engine (CPDE)
                     |
          +----------+----------+
          |          |          |
          v          v          v
      Verify      Assess     Explain
      Intent       Risk      Decision
          |          |          |
          +----------+----------+
                     |
                     v
             Decision Policy
                     |
          +----------+----------+
          |          |          |
          v          v          v
        Proceed     Warn      Confirm/
                              Clarify
                     |
                     v
           Payment Authorization
                     |
                     v
          Preferred UPI Application
                     |
                     v
              User Enters UPI PIN
                     |
                     v
              Payment Completed
```

*Note: The workflow represents the intended end-to-end system. The current prototype provides pre-payment risk recommendations and does not independently execute or authorize bank transactions.*

---

## CPDE: Context-Aware Payment Decision Engine

CPDE is the central decision-making component of VeriPay.

It combines transaction-level fraud predictions with contextual information to determine whether a payment should proceed, receive a warning, or require additional confirmation.

### CPDE Architecture

```text
                    CPDE
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
  Transaction     Recipient      Intent
   Fraud Score     Context     Verification
       |             |             |
       +-------------+-------------+
                     |
                     v
              Risk Assessment
                     |
                     v
               Decision Policy
                     |
        +------------+------------+
        |            |            |
        v            v            v
     Proceed       Warn       Confirm/
                               Clarify
                     |
                     v
             Explainable Output
```

### Core Decision Components

| Component | Responsibility |
|---|---|
| Intent Verification | Checks whether the payment instruction has been correctly understood. |
| Recipient Matching | Identifies the intended recipient and handles ambiguous matches. |
| Fraud Prediction | Estimates transaction-level fraud probability using the trained ML model. |
| Context Analysis | Evaluates recipient history and transaction-related contextual signals. |
| Decision Policy | Maps the evaluated risk to an appropriate recommendation. |
| Explainability | Provides reasons behind the generated recommendation. |

---

## Risk Assessment Signals

CPDE is designed to consider multiple contextual signals.

| Signal | Purpose |
|---|---|
| Recipient Novelty | Identifies first-time or unfamiliar recipients. |
| Amount Deviation | Identifies transactions that differ from historical payment patterns. |
| Contact Ambiguity | Detects similar recipient names and potential selection errors. |
| Urgency Language | Identifies pressure-related phrases that may indicate social engineering. |
| High-Amount Pattern | Flags unusually large transactions. |
| ML Fraud Probability | Incorporates the transaction-level fraud prediction into the decision process. |

Recipient history and behavioral information in the current demonstration may use mock data. These signals should not be interpreted as verified real-world banking records.

---

## Decision Policy

The intended decision policy maps contextual risk scores to recommendations.

| Risk Score | Recommendation |
|---|---|
| 0.00 – 0.30 | Proceed |
| 0.31 – 0.60 | Warning + Confirmation |
| 0.61 – 1.00 | Mandatory Confirmation + Explanation |

If intent confidence falls below the configured threshold, the system should request clarification before proceeding.

**Important:** These are proposed policy ranges. They should only be described as implemented and validated thresholds if confirmed by the actual code and evaluation results.

---

## Key Features

- Voice-assisted payment instruction input.
- Speech-to-text transcription using Whisper Tiny.
- Recipient and transaction detail extraction.
- Machine learning-based transaction fraud prediction.
- Context-aware payment risk assessment.
- Recipient history and transaction context evaluation.
- Intent verification and ambiguity handling.
- Explainable payment risk recommendations.
- Pre-payment decision support.

### Planned Enhancements

- UPI deep-link integration.
- Flutter-based mobile application.
- Multilingual speech support.
- Retrieval-Augmented Generation (RAG) for contextual assistance.
- Enhanced intent verification.
- Voice anti-spoofing and replay attack detection.
- Expanded evaluation using realistic payment scenarios.

---

## Machine Learning Experiments

VeriPay incorporates fraud detection experiments using two datasets.

### 1. PaySim

A synthetic mobile money transaction dataset used to study financial transaction fraud detection.

### 2. IEEE-CIS Fraud Detection

An e-commerce transaction fraud dataset used to train and evaluate transaction-level fraud classification models.

### Model Comparison

| Dataset | Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|
| PaySim | Logistic Regression | 96.35% | 0.03 | 0.98 | 0.06 | 0.9962 |
| PaySim | Random Forest | 99.9996% | 1.00* | 1.00* | 1.00* | 0.9990 |
| IEEE-CIS | Logistic Regression | 64% | 0.06 | 0.58 | 0.10 | 0.6563 |
| IEEE-CIS | Random Forest | 99% | 0.88 | 0.69 | 0.78 | 0.9591 |
| IEEE-CIS | XGBoost | 98% | 0.90 | 0.40 | 0.55 | 0.9276 |

*Random Forest PaySim precision, recall, and F1 are rounded reported values, not necessarily exactly 1.00.*

**Observation:** Random Forest achieved the strongest reported performance among the IEEE-CIS experiments. However, class imbalance, dataset characteristics, and generalization limitations must be considered when interpreting these results.

PaySim and IEEE-CIS represent different transaction domains, so their results should not be treated as a direct apples-to-apples comparison.

---

## Speech Processing Experiments

Speech-related experiments were conducted using the Skit-S2I Indian English banking-domain speech dataset.

The evaluated approaches included:

- MFCC-based feature extraction.
- Delta and Delta-Delta audio features.
- Log-Mel spectrograms.
- CNN-based speech classification.
- Wav2Vec 2.0-based speech representations.

The current payment interface uses **OpenAI Whisper Tiny** for speech-to-text transcription.

Whisper performs speech recognition; it does not independently verify speaker identity or detect cloned voices.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React.js, Vite |
| Backend | Python, FastAPI |
| Machine Learning | Scikit-learn, Random Forest, Logistic Regression, XGBoost |
| Speech Recognition | OpenAI Whisper Tiny |
| Speech Processing | MFCC, Log-Mel Spectrograms, Wav2Vec 2.0 |
| Data Processing | NumPy, Pandas |
| Deployment | Vercel, Google Cloud Run |
| Decision Layer | Context-Aware Payment Decision Engine (CPDE) |
| Planned Mobile Integration | Flutter |
| Planned Enhancement | RAG |

---

## Project Architecture

```text
VeriPay/
│
├── frontend/
│   ├── React.js
│   └── Vite
│
├── backend/
│   ├── FastAPI
│   ├── ML Fraud Prediction
│   ├── CPDE
│   └── API Endpoints
│
├── models/
│   ├── Random Forest
│   └── Model Preprocessing
│
├── experiments/
│   ├── PaySim
│   ├── IEEE-CIS
│   └── Speech Processing
│
├── docs/
│   └── Architecture and Research
│
└── README.md
```

*The directory structure is illustrative. Refer to the actual repository for the current implementation.*

---

## Evaluation and Testing

The prototype includes testing of transaction model integration and contextual decision behavior.

| Test Case | Description |
|---|---|
| Model Prediction Parity | Compared backend Random Forest predictions with directly loaded model predictions on 100 IEEE-CIS rows. |
| Hybrid Fraud Assessment | Evaluated CPDE behavior using a high fraud probability and contextual inputs. |

**Reported result:** Backend and directly loaded Random Forest predictions matched exactly for the 100-row parity test, with a maximum prediction difference of zero.

Further evaluation is required to establish the effectiveness of CPDE against transaction-only and threshold-based baselines.

---

## Research Motivation and Contribution

Conventional machine learning fraud detection primarily focuses on identifying suspicious transactions and generating fraud probabilities.

However, a fraud probability alone does not necessarily provide an actionable decision for a user preparing to make a payment.

VeriPay explores the integration of:

- Voice-based payment instruction understanding.
- Transaction-level machine learning fraud prediction.
- Recipient and transaction context.
- Intent verification.
- Explainable pre-payment recommendations.

Its central research direction is the **Context-Aware Payment Decision Engine (CPDE)**, which aims to bridge the gap between fraud prediction and actionable payment risk assessment.

The framework is a prototype research contribution and requires further comparative evaluation against existing approaches.

---

## Security and Limitations

VeriPay is currently a research prototype, not a production banking application.

Current limitations include:

- No direct execution of real UPI transactions in the current prototype.
- No bank-side payment authorization.
- No implemented voice-clone or replay attack detection.
- Whisper transcription does not establish speaker identity.
- Some recipient and transaction context is simulated.
- Fraud detection performance depends on dataset quality and distribution.
- Real-world UPI validation has not yet been established.

Future production deployment would require secure UPI integration, robust authentication, voice anti-spoofing, privacy safeguards, and extensive security testing.

---

## Target Audience

**Primary Users**
- Elderly users.
- Digitally less-literate users.
- Users who rely on hands-free payment interfaces.

**Secondary Users**
- General UPI users seeking additional payment risk awareness.
- Users who want contextual explanations before authorizing transactions.

---

## Development Roadmap

- [x] Repository setup
- [x] FastAPI backend setup
- [x] Configuration module
- [x] Logging system
- [x] Transaction fraud detection experiments
- [x] Speech processing experiments
- [x] Whisper Tiny integration
- [x] CPDE conceptualization and prototype implementation
- [x] Frontend-backend integration
- [x] Backend deployment
- [x] Frontend deployment
- [ ] Expanded synthetic contextual dataset
- [ ] Systematic CPDE baseline comparison
- [ ] Comprehensive evaluation dashboard
- [ ] Flutter mobile application
- [ ] UPI deep-link integration
- [ ] Voice anti-spoofing
- [ ] Multilingual support
- [ ] RAG-based contextual assistance

---

## Project Links

- **Live Demo:** https://veripay-secure-pay.vercel.app/
- **Backend API:** https://veripay-backend-214543665633.asia-south1.run.app
- **GitHub Repository:** https://github.com/Sneha-0409/VeriPay

---

## Built By

**Sneha**  
Computer Science| 3rd Year

> **VeriPay — Verify Before You Pay.**
