# SwachhLoop AI — Phase 5: Evaluation, Guardrails & Production Hardening

> Phase 5 Architecture, AI Defensive Guardrails, Evaluation Methodology, and Hardening
> Focus Area: Kalady Grama Panchayat, Ernakulam District, Kerala

---

## 1. Overview & Objectives

Phase 5 hardens SwachhLoop AI into an enterprise-ready, production-grade civic AI platform. Building on top of the Phase 1–4 foundational architecture and LangGraph multi-agent subgraphs, Phase 5 delivers:
1. **Reusable AI Evaluation Framework**: An offline, deterministic benchmark suite evaluating complaint NLP classification, waste computer vision, geospatial route constraints, cleanup verification, bilingual RAG grounding, and multi-agent workflows.
2. **Defensive AI Guardrails & Input Validation**: Strict payload limits, image byte & decompression-bomb verification, geographic coordinate constraint validation, and adversarial prompt-injection heuristics.
3. **RAG Grounding & Reliability**: Strict separation of retrieval and response generation, token overlap grounding metrics, civic stopword filtering, and explicit insufficient-context uncertainty fallbacks for English and Malayalam queries.
4. **Resilience & Fault Tolerance**: Bounded retries with exponential backoff for transient AI provider errors, configurable timeouts, LangGraph bounded execution limits, and safe fallbacks.
5. **Privacy & Security Hardening**: Automated PII masking (Indian mobile numbers, email addresses, Aadhaar identity tokens) in server logs and audit trails, without exposing stack traces or credentials to API clients.

---

## 2. Phase 5 Architecture & Hardened System Flow

```mermaid
graph TD
    User([Citizen / Cleaner / Municipal Staff]) --> RateLimiter[Input Guardrails & Length Limits]
    RateLimiter --> InjCheck{Prompt Injection Check?}
    InjCheck -->|Adversarial Pattern Detected| FlagRisk[Sanitize Tokens & Flag Untrusted Context]
    InjCheck -->|Clean Input| PIIFilter[PII Masking & Sanitization]
    FlagRisk --> PIIFilter

    PIIFilter --> APIRoutes[FastAPI Endpoints (/api/ai/*)]

    APIRoutes --> Router[Parent Orchestrator / Services]
    Router -->|PROCESS_COMPLAINT| CSG[Complaint Subgraph + Validation]
    Router -->|OPTIMIZE_ROUTE| LSG[Logistics TSP + Constraint Checker]
    Router -->|VERIFY_CLEANUP| VSG[Verification + Change Bounds]
    Router -->|PUBLIC_AWARENESS| ASG[Bilingual RAG + Grounding Check]

    CSG --> Gov[Policy Governance & Human Review Gate]
    LSG --> Gov
    VSG --> Gov
    ASG --> Gov

    Gov --> OutputValidator[Output Guardrail Verification]
    OutputValidator --> AuditLogger[Sanitized Audit Log DB / Response]
    AuditLogger --> ClientResp([Secure API Client Response])
```

---

## 3. Evaluation Framework

The evaluation framework is located in `evaluations/` and is strictly decoupled from production inference logic. It operates **100% offline without requiring paid API credentials**, using deterministic fixtures stored under `evaluations/datasets/`.

### Evaluated Suites & Metrics

| Suite | Dataset Fixture | Primary Metrics | Purpose |
|-------|-----------------|-----------------|---------|
| **Complaint NLP Analysis** | `complaints_eval.json` (13 cases) | `urgency_accuracy`, `urgency_macro_f1`, `location_extraction_accuracy`, `ambiguity_detection_accuracy` | Evaluates classification of hazards (critical/high/medium/low) in Kalady landmarks and ambiguity detection. |
| **CV Waste Detection** | `waste_detection_eval.json` (5 fixtures) | `detection_accuracy`, `category_accuracy`, `bounding_box_validity_rate`, `average_confidence` | Tests image dimension validity, corrupted file rejection, and bounding box coordinate physical bounds. |
| **Geospatial Route Optimization** | `routes_eval.json` (4 route sets) | `constraint_violation_rate`, `average_distance_reduction_pct`, `mean_route_distance_km` | Validates that routes preserve all stops, satisfy shift length/duration constraints, and improve upon naive stop ordering. |
| **Cleanup Verification** | `verification_eval.json` (5 pairs) | `verification_accuracy`, `macro_f1`, per-verdict breakdown | Tests detection of verified clean sites, partial cleanup, and rejection of identical/tampered images. |
| **Civic Knowledge RAG** | `rag_eval.json` (12 bilingual queries) | `mean_relevance_score`, `mean_groundedness_score`, `citation_coverage_rate`, `fallback_accuracy` | Verifies grounding in Kalady bylaws, citation coverage, and rejection of out-of-domain or prompt-injection queries. |
| **Multi-Agent Workflows** | `workflows_eval.json` (5 scenarios) | `success_rate`, `error_handling_rate`, `human_review_accuracy`, `mean_latency_ms` | Tests hierarchical orchestration completion, supervisor review gate accuracy, and unknown task type fallback. |

### Metric Definitions

- **`urgency_accuracy`**: Proportion of complaints whose urgency matches ground truth exactly.
- **`urgency_macro_f1`**: Macro-averaged F1 score across all four urgency categories (`critical`, `high`, `medium`, `low`).
- **`location_extraction_accuracy`**: Accuracy of recognizing specific Kalady landmarks (e.g., *Mattoor, MC Road, Temple Road, Piraroor, Sree Sankaracharya University*) or correctly marking location as missing.
- **`constraint_violation_rate`**: Percentage of generated routes with missing stops, negative distance, or excessive shift length.
- **`average_distance_reduction_pct`**: Travel distance saved by TSP optimization relative to naive input-sequence traversal.
- **`mean_groundedness_score`**: Lexical overlap ratio between generated RAG answers and retrieved official civic articles.
- **`citation_coverage_rate`**: Percentage of in-domain civic inquiries retrieving the correct official source article ID.
- **`fallback_accuracy`**: Accuracy of returning an explicit insufficient-context notice on out-of-domain queries rather than hallucinating facts.

### Running AI Evaluations

Execute the complete evaluation suite from the workspace root:

```bash
# Run all 6 evaluation suites:
python -m evaluations.runner

# Run specific suites:
python -m evaluations.runner --suite complaint,rag

# Output report to custom path:
python -m evaluations.runner --output evaluations/reports/custom_report.json
```

---

## 4. AI Guardrails & Validation

All guardrails reside in `backend/core/guardrails.py` and are enforced across API endpoints, services, and LangGraph subgraphs.

### A. Input Guardrails
1. **Complaint Text**:
   - Length bounded between 1 and 5,000 characters (`MAX_COMPLAINT_TEXT_LENGTH`).
   - Scanned against 12+ prompt injection patterns (e.g., `ignore previous instructions`, `reveal system prompt`, `developer mode`, `<|im_start|>`).
   - Control characters and hostile markdown code delimiters are sanitized.
2. **Image Evidence**:
   - Size limit: 10 MB (`MAX_IMAGE_UPLOAD_BYTES`).
   - PIL verification: verifies header integrity, protects against 0-byte files and decompression bombs (>100 megapixels).
3. **Route Stops**:
   - Stop count limit: max 50 collection stops (`MAX_ROUTE_STOPS`).
   - Coordinate boundary check: $-90.0 \le \text{lat} \le 90.0$ and $-180.0 \le \text{lon} \le 180.0$.
   - Automatic detection of duplicate stop coordinates.
4. **RAG Queries**:
   - Length bounded to 1,000 characters (`MAX_RAG_QUERY_LENGTH`).
   - Prompt-injection attempts automatically short-circuit retrieval to prevent adversarial jailbreaks.

### B. Output Guardrails
1. **Route Constraints**: Output routes validated via `validate_route_constraints`:
   - Checks that all input stops are present in the final ordering.
   - Asserts non-negative travel distance and duration.
   - Enforces shift capacity limits (>40 km or >6 hours triggers supervisor review).
2. **Verification & Waste Detection**:
   - Clamps confidence and change scores strictly to $[0.0, 1.0]$.
   - Validates that bounding boxes are non-negative, ordered $(y_1 \le y_2, x_1 \le x_2)$, and physically plausible.
3. **RAG Grounding**:
   - Output answers evaluated against retrieved context tokens via `evaluate_rag_groundedness`.
   - Low relevance ($< 0.25$) automatically returns explicit uncertainty response.

---

## 5. Security & Privacy Hardening

1. **Automated PII Redaction**:
   - Integrated directly into `AuditService.log` and `sanitize_pii()`.
   - Redacts 10-digit Indian phone numbers (`[REDACTED_PHONE]`), email addresses (`[REDACTED_EMAIL]`), and 12-digit Aadhaar identity numbers (`[REDACTED_ID]`).
2. **Safe Exception Handling**:
   - Global and endpoint-level exception handlers log complete stack traces on the server while returning sanitized error responses (`{"detail": "..."}`) to API clients.
   - Secret keys, API tokens, and internal paths are never leaked in HTTP error responses.
3. **Role-Based Access Control**:
   - Route optimization and cleanup verification endpoints strictly restricted to authenticated cleaners, municipal staff, and administrators (`HTTP 403 Forbidden` for unauthorized citizen accounts).

---

## 6. Configuration & Environment Variables

New Phase 5 configuration knobs in `backend/core/config.py` and `.env.example`:

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `AI_REQUEST_TIMEOUT_SECONDS` | `15.0` | Timeout in seconds for external AI provider API calls |
| `AI_MAX_RETRIES` | `3` | Maximum retry attempts for transient AI provider failures |
| `AI_RETRY_BACKOFF_FACTOR` | `1.5` | Exponential backoff multiplier for provider retries |
| `MAX_IMAGE_UPLOAD_BYTES` | `10485760` | Maximum allowed image file upload size in bytes (10 MB) |
| `MAX_COMPLAINT_TEXT_LENGTH` | `5000` | Maximum character length for citizen complaint text |
| `MAX_ROUTE_STOPS` | `50` | Maximum collection stops allowed in a single routing request |
| `MAX_RAG_QUERY_LENGTH` | `1000` | Maximum character length for civic RAG inquiries |
| `RAG_RELEVANCE_THRESHOLD` | `0.25` | Minimum BM25 relevance score required to return an answer |
| `GUARDRAILS_ENABLED` | `true` | Master flag to enable/disable defensive AI guardrails |
| `SANITIZE_LOGS_PII` | `true` | Automatically redact phone numbers, emails, and Aadhaar IDs in logs |
| `WORKFLOW_RECURSION_LIMIT` | `25` | LangGraph StateGraph execution recursion limit |
| `WORKFLOW_MAX_STEPS` | `15` | Maximum traceable execution steps per multi-agent workflow |

---

## 7. Testing & Verification Guide

### Test Suite Execution

```bash
# Run all 154 unit and integration tests:
pytest

# Run only Phase 5 tests:
pytest tests/test_guardrails.py tests/test_rag_reliability.py tests/test_resilience_and_hardening.py tests/test_evaluations.py -v

# Run AI service and agent tests:
pytest tests/test_ai_services.py tests/test_ai_agents_and_api.py -v
```

### Reproducing Evaluation Results

```bash
python -m evaluations.runner
```
Output report will be generated at `evaluations/reports/evaluation_report.json`.

---

## 8. Current Limitations & Production Risks

1. **Heuristic Prompt-Injection Detection**: Rule-based regex pattern matching mitigates known prompt-injection prefixes and delimiter escapes, but cannot theoretically eliminate novel jailbreaks. A secondary defense-in-depth model can be deployed in future phases.
2. **Local Mock Heuristics**: The local rule-based waste detector uses color channel variance and aspect ratios for zero-credential testing. In cloud production, real YOLOv8 or cloud vision model weights should be configured via `GEMINI_API_KEY` or `OPENAI_API_KEY`.
3. **Static Knowledge Base**: The civic knowledge base is currently loaded from `data/knowledge_base.json`. Upgrading to vector database storage (e.g. pgvector or ChromaDB) can be evaluated in subsequent iterations.

---

## 9. Phase 5 Completion Checklist

- [x] **A. AI Evaluation Framework**:
  - [x] Reusable offline evaluation runner (`evaluations/runner.py`)
  - [x] Standard metrics: Accuracy, Precision, Recall, Macro F1, Distance Reduction, Groundedness, Fallback Accuracy
  - [x] 6 deterministic evaluation suites and labeled datasets in `evaluations/datasets/`
  - [x] Machine-readable JSON report with metric definitions (`evaluations/reports/evaluation_report.json`)
  - [x] Zero paid external API dependencies for evaluation
- [x] **B. AI Guardrails & Validation**:
  - [x] Dedicated guardrails module (`backend/core/guardrails.py`)
  - [x] Input length and image byte validation with decompression bomb protection
  - [x] Adversarial prompt-injection detection and delimiter escaping
  - [x] Route constraints validation and coordinate boundary checking
  - [x] Output verification for waste detection bounding boxes and change scores
- [x] **C. RAG Reliability Improvements**:
  - [x] Separable `retrieve()` and `generate_answer()` methods in `backend/services/knowledge_service.py`
  - [x] Relevance score thresholding (`RAG_RELEVANCE_THRESHOLD`)
  - [x] Grounding lexical overlap evaluation (`evaluate_rag_groundedness`)
  - [x] Civic stopword filtering preventing false matches on general town names
  - [x] Explicit bilingual fallback in English and Malayalam for unsupported queries
- [x] **D. Reliability and Resilience**:
  - [x] Resilient retry helper with exponential backoff (`resilient_call_with_retry`)
  - [x] Configurable timeouts and retry limits in `Settings`
  - [x] LangGraph recursion limits and bounded steps (`WORKFLOW_RECURSION_LIMIT`, `WORKFLOW_MAX_STEPS`)
  - [x] Safe application startup and local fallback operation without external credentials
- [x] **E. Security and Privacy Review**:
  - [x] Automated PII masking for phone numbers, emails, and Aadhaar numbers in `AuditService.log`
  - [x] Error masking on all AI API routes preventing credential and stack trace leakage
  - [x] Strict RBAC enforcement on logistics and cleanup verification endpoints
- [x] **F. Testing & Regression Coverage**:
  - [x] 28 guardrails unit tests in `tests/test_guardrails.py`
  - [x] 9 RAG grounding and reliability tests in `tests/test_rag_reliability.py`
  - [x] 12 resilience and API hardening tests in `tests/test_resilience_and_hardening.py`
  - [x] 12 evaluation framework tests in `tests/test_evaluations.py`
  - [x] Complete 154-test regression run passing with 0 failures
- [x] **G. Documentation & Operational Readiness**:
  - [x] Detailed Phase 5 architecture documentation in `docs/phase5_evaluation_and_hardening.md`
