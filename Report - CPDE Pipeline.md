# VeriPay — Model & System Evaluation Report

**Project:** Design and Development of a Context-Aware Payment Decision Engine (CPDE) for Secure Voice-Based UPI Payments

## 1. Project Overview

VeriPay is a prototype voice-based payment security system that combines machine learning-based fraud detection with contextual risk assessment.

The system evaluates transaction features, recipient-match confidence, transaction amount deviation and voice-intent confidence to generate one of four decisions:

- **PROCEED:** Risk is low.
- **WARN:** Contextual risk is elevated; verify payment details.
- **BLOCK:** High fraud or contextual risk.
- **REQUEST_CLARIFICATION:** Recipient identity is uncertain.

The prototype does not execute real UPI transactions. Payment execution remains disabled.

## 2. Machine Learning Model Evaluation

**Dataset:** IEEE-CIS Fraud Detection Dataset  
**Model:** Random Forest Classifier  
**Number of features:** 23 numerical features  
**Training configuration:** 100 estimators, `class_weight="balanced"`, `random_state=42`  
**Data split:** 80% training and 20% testing  
**Split strategy:** Stratified sampling (`random_state=42`)  
**Decision threshold:** 0.45

### Model performance

| Metric | Result |
|---|---:|
| ROC-AUC | 0.9591 |
| Accuracy | 99% |
| Fraud precision | 84% |
| Fraud recall | 72% |
| Fraud F1-score | 0.78 |

### Confusion matrix

| | Predicted legitimate | Predicted fraud |
|---|---:|---:|
| Actual legitimate | 113,417 | 558 |
| Actual fraud | 1,149 | 2,984 |

The model correctly detected 2,984 fraudulent transactions among 4,133 actual fraud records in the held-out test set.

## 3. Hybrid CPDE Evaluation

Four end-to-end scenarios were tested through the `/predict-context` API.

| Scenario | ML probability | Context score | Expected decision | Observed decision |
|---|---:|---:|---|---|
| Genuine fraudulent transaction | 1.00 | 0.0656 | BLOCK | BLOCK |
| Genuine legitimate transaction | 0.00 | 0.0641 | PROCEED | PROCEED |
| Ambiguous recipient | 0.00 | 0.2341 | REQUEST_CLARIFICATION | REQUEST_CLARIFICATION |
| Elevated transaction amount | 0.00 | 0.4200 | WARN | WARN |

All four scenarios produced the expected CPDE decisions.

### Interpretation

**Fraud detection:** A genuine held-out fraud record received a fraud probability of 1.00. Despite low contextual risk, the CPDE blocked the transaction.

**Legitimate transaction:** A genuine held-out legitimate record received a fraud probability of 0.00 and a low contextual score. The CPDE returned PROCEED, while still requiring user confirmation.

**Recipient ambiguity:** Low recipient-match confidence triggered REQUEST_CLARIFICATION, even though the ML model predicted a low fraud probability.

**Elevated contextual risk:** A high illustrative transaction amount relative to the typical amount generated a MEDIUM contextual risk and WARN decision, despite a low ML fraud probability.

## 4. Safety Testing

### Application-level test report

The final application test report recorded 9/9 passing tests, including:

- Recorded voice payment.
- High-risk transaction blocking.
- Ambiguous recipient clarification.
- Low voice confidence.
- Missing amount and recipient.
- Confirmation gate.
- Unrelated banking request handling.

### Additional safety test report

The separate safety test report recorded 7/7 passing tests, including:

- Voice payment command parsing.
- High-risk payment blocking.
- Missing payment details.
- Unrelated banking query rejection.
- Confirmation gate.
- Approved prototype flow without payment execution.

**Combined reported result: 16/16 application and safety tests passed.**

The two reports cover related safety behaviours, so this combined count represents test cases across both reports, not necessarily 16 unique independent behaviours.

## 5. Payment Safety Mechanism

The API responses confirmed the following behaviour:

| Decision | Payment behaviour |
|---|---|
| BLOCK | Payment blocked |
| REQUEST_CLARIFICATION | Further recipient clarification required |
| PROCEED | Awaiting user confirmation |
| WARN | Awaiting user confirmation |

Across the demonstrated API tests:

- Blocked transactions did not proceed.
- Ambiguous recipient cases did not request payment confirmation.
- PROCEED and WARN cases required user confirmation.
- `payment_execution` remained `NOT_EXECUTED`.

## 6. Conclusion

The evaluation demonstrates that VeriPay's prototype successfully combines IEEE-CIS-based Random Forest fraud prediction with contextual risk assessment.

The ML model achieved a ROC-AUC of 0.9591 on the reproduced held-out test set. The hybrid API also demonstrated four expected decision outcomes: BLOCK, PROCEED, REQUEST_CLARIFICATION and WARN.

The results support the feasibility of a context-aware decision engine for voice-based payment security. Further testing with real-world recipient histories, independently collected voice data, additional datasets and payment-system integration would be necessary before production deployment.

**Important evaluation note:** The IEEE-CIS transactions provide the ground-truth labels for the ML tests. The recipient and voice context values used in the hybrid demonstrations were illustrative inputs, not historical context recorded for those dataset transactions.
