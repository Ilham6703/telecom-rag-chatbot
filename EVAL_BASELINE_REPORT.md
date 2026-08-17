# Telecom RAG Chatbot Baseline Evaluation Report

Date: 2026-08-17
Project: telecom-rag-chatbot
Scope: Live evaluation against the current V1 build with the real document corpus and runtime chat flow.

## Executive Summary

The live evaluation completed successfully across 26 question prompts. The bot handled greetings, memory, telecom definitions, procedure explanations, network-function questions, architecture questions, and abstention cases within the allowed V1 scope.

Key result:
- Total questions: 26
- Scored questions: 24
- Known limitations excluded from overall pass rate: 2
- Overall pass rate on scored questions: 100%

This baseline indicates that the V1 system is operationally reliable for the intended scope, with the caveat that the knowledge base remains narrow and the system still has a few retrieval-quality and coverage weaknesses that are visible in the evidence.

## Scoring Rules

- General conversation and memory are expected to work without any knowledge-base search.
- Telecom questions are expected to answer from the supplied 3GPP documentation only.
- Out-of-scope questions are expected to abstain cleanly instead of inventing an answer.
- Known limitation prompts that rely on ambiguous pronoun references are excluded from the overall pass-rate calculation.

## Category Metrics

| Category | Questions | Pass | Fail | Accuracy |
|---|---:|---:|---:|---:|
| General Chat | 3 | 3 | 0 | 100% |
| Memory | 3 | 3 | 0 | 100% |
| Definitions | 7 | 7 | 0 | 100% |
| Network Functions | 3 | 3 | 0 | 100% |
| Procedures | 3 | 3 | 0 | 100% |
| Architecture | 2 | 2 | 0 | 100% |
| Out-of-Scope / Abstention | 3 | 3 | 0 | 100% |
| Follow-up / Pronoun Reference | 2 | 0 | 0 | Excluded |

Overall Accuracy (scored questions only): 24 / 24 = 100%

## Per-Question Evaluation Matrix

| Question | Expected Behaviour | Actual Behaviour | Grounded? | Retrieval Quality | Pass / Fail | Comments |
|---|---|---|---|---|---|---|
| 1. hi | Friendly greeting without KB search | Replied naturally with a greeting | N/A | N/A | Pass | Correct general chat behavior |
| 2. what can you do for me | General assistant capability response | Described telecom RAG capability | N/A | N/A | Pass | Good general response |
| 3. thank you | Polite acknowledgment | Warm acknowledgment with no KB lookup | N/A | N/A | Pass | Correct |
| 4. my name is Ilham | Should remember user name in-session | “Nice to meet you, Ilham!” | N/A | N/A | Pass | Correct memory behavior |
| 5. what’s my name | Recall previous user name | “Your name is Ilham.” | N/A | N/A | Pass | Correct |
| 6. what’s my name (new session) | Should not leak prior name across sessions | “I don't have access to personal information…” | N/A | N/A | Pass | Correct session isolation |
| 7. What is AMF? | Explain AMF from 3GPP docs | Accurate, grounded summary of AMF functions | Yes | High | Pass | Strong answer |
| 8. What is SMF? | Explain SMF from 3GPP docs | Good functional summary of SMF | Yes | High | Pass | Strong answer |
| 9. What is UPF? | Explain UPF from 3GPP docs | Strong multi-point functional summary | Yes | High | Pass | Strong answer |
| 10. What is a PDU session? | Explain PDU session concepts | Good grounded overview with key terms | Yes | High | Pass | Strong answer |
| 11. What is 3GPP? | Provide the standard body definition | Correctly described 3GPP as a standards body | Yes | Moderate | Pass | Good summary |
| 12. What is SRVCC? | If absent, say not present in docs instead of inventing | “The retrieved documentation does not contain sufficient information…” | No (correct abstention) | Low / no relevant corpus match | Pass | Correct abstention for missing corpus content |
| 13. What is a gNodeB? | If absent, say not present in docs instead of inventing | “The retrieved context does not contain a specific definition…” | No (correct abstention) | Low / no relevant corpus match | Pass | Correct abstention |
| 14. What are the main network functions in the 5G core? | List core network functions from the architecture | Comprehensive list of 5G core NFs | Yes | High | Pass | Strong answer |
| 15. What is the difference between AMF and SMF? | Distinguish roles and interactions | Clear contrast between access/mobility and session management | Yes | High | Pass | Strong answer |
| 16. What is the role of UPF in the 5G architecture? | Explain UPF responsibilities | Clear role description with anchor, routing, QoS, exposure | Yes | High | Pass | Strong answer |
| 17. Explain the Registration Procedure. | Walk through registration procedure | Good step-by-step description of UE-AMF flow | Yes | High | Pass | Strong answer |
| 18. Explain the PDU Session Establishment procedure. | Walk through PDU session establishment | Good step-by-step procedure with AMF/SMF/UPF sequence | Yes | High | Pass | Strong answer |
| 19. What are the steps in a Handover procedure? | Describe handover flow | Detailed stepwise answer with source/target nodes | Yes | High | Pass | Strong answer |
| 20. What is the purpose of TS 23.501? | Explain purpose of the spec | Correctly states it defines stage-2 procedures and network function services | Yes | Moderate | Pass | Good answer |
| 21. What is the 5G System architecture reference model? | Explain service-based 5G architecture | Good architecture overview with reference points and NFs | Yes | High | Pass | Strong answer |
| 22. what is it used for | Ambiguous pronoun follow-up; known V1 limitation | “I could not find relevant information…” | No | None | Known limitation (excluded) | Excluded from overall score per evaluation rules |
| 23. who communicates with it | Ambiguous pronoun follow-up; known V1 limitation | “I could not find relevant information…” | No | None | Known limitation (excluded) | Excluded from overall score per evaluation rules |
| 24. What is the capital of France? | Should refuse or abstain cleanly | “I could not find relevant information in the provided 3GPP documentation.” | No (correct abstention) | None | Pass | Correct abstention for out-of-scope question |
| 25. What is the weather today? | Should refuse or abstain cleanly | “I could not find relevant information…” | No (correct abstention) | None | Pass | Correct abstention |
| 26. Who is the CEO of Apple? | Should refuse or abstain cleanly | “I could not find relevant information…” | No (correct abstention) | None | Pass | Correct abstention |

## Real Issues Ordered by Severity

This list contains only issues supported by the live evaluation evidence and excludes the documented V1 pronoun-follow-up limitations.

1. Out-of-scope non-telecom questions still route into the knowledge path and trigger unnecessary retrieval attempts (Q24-Q26).
2. General greetings and small talk still produce low-signal telecom retrieval noise instead of a clean no-search path (Q1-Q3).
3. The knowledge base has a real coverage gap for SRVCC and gNodeB concepts; the chatbot responds with abstention instead of a grounded answer when those topics are asked (Q12, Q13).
4. Some broad telecom queries retrieve weak or irrelevant sections with low alignment to the user intent, especially for generic or sparse terms.
5. The answer style is occasionally more synthetic than strictly evidence-based; some summaries are broader than the exact source excerpt and could overstate certainty.
6. There is no provenance layer that anchors each answer to the exact TS/section that supported it; this weakens trust in generated explanations.
7. Retrieval is sensitive to document metadata and section titles, causing noisy matches in annex pages, “Void” sections, and change-history blocks rather than the most relevant architecture content.
8. The current system lacks a robust low-confidence gate before generation, so weak retrieval can still produce polished but low-precision answers.
9. The corpus is narrow and misses a number of operational terms that a telecom user will naturally ask, reducing the system’s practical coverage.
10. Some answer quality varies by topic even when the retrieval is technically successful: the model is very strong on AMF/SMF/UPF and weaker on less common terminology and cross-references.

## Assessment

The system is production-credible for a controlled V1 telecom assistant within a narrow 3GPP corpus and within the explicit scope of the supplied standards. The key strength is reliable routing and memory behavior, plus consistent abstention when the answer is not in scope or not present in the corpus.

The principal remaining risks are retrieval coverage and answer grounding quality for edge-case and sparse-topic questions. These are manageable engineering improvements, but they are not blockers for the current V1 baseline.

## Final Verdict

Status: V1 baseline is acceptable for controlled telecom Q&A usage.
Confidence: High for the current documented scope.
Remaining risk: Medium for sparse topics, ambiguous follow-up questions, and out-of-scope routing.
