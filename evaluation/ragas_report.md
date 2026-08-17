# Telecom RAG Evaluation Report

## Dataset
- Rows: 13
- Answer expected questions: 10
- Abstention expected questions: 3

## Metric Definitions
- Faithfulness: measures whether the answer is supported by the retrieved context.
- Answer Relevancy: measures whether the answer addresses the asked question.
- Context Precision: measures how relevant the retrieved context is.
- Context Recall: measures whether the retrieved context covers the needed information.

## Overall Metrics
- Overall Score: N/A
- Faithfulness: N/A
- Answer Relevancy: N/A
- Context Precision: N/A
- Context Recall: N/A

## Dataset Size
13 benchmark questions were evaluated.

## Number of Abstentions
3 questions were expected to abstain because their answer is not in the indexed 3GPP corpus.

## Number of Answered Questions
10 questions were expected to be answered from the corpus.

## Lowest Scoring Questions
No low-scoring questions available.

## Highest Scoring Questions
No high-scoring questions available.

## Observations
- Grounded evaluation is based on the indexed corpus rather than general world knowledge.
- Out-of-domain questions are treated as abstention cases and are not judged as factual failures.
- Retrieval quality is captured explicitly in retrieval_debug.json.

## Failure Analysis
- If a question expected an answer but was abstained or had weak metric values, inspect retrieval context coverage and retrieval scores.
- If a question expected abstention but the model answered factually, the model is not respecting grounded abstention behavior.
- If retrieved context is weak or empty, the evaluation should be treated as retrieval failure rather than answer failure.
