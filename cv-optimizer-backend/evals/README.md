# CV Optimizer AI - Evaluation Framework

This directory contains a formal evaluation framework for the RAG pipeline, leveraging the [Ragas](https://github.com/explodinggradients/ragas) library.

## Overview

The framework allows you to programmatically measure the quality of the resume optimization system across four key dimensions:

1.  **Faithfulness (Hallucination Detection):** Measures how much of the generated resume is actually derived from the original resume context.
2.  **Answer Relevancy:** Measures how well the optimized resume addresses the requirements of the Job Description.
3.  **Context Precision:** Measures the quality of the retrieval system (how relevant the retrieved chunks are to the JD).
4.  **Context Recall:** Measures if the retrieval system found all the necessary information from the resume to answer the JD requirements.

## Components

### 1. Synthetic Data Generator (`synthetic_data_generator.py`)
Generates a "Gold Standard" dataset. It takes raw resumes, analyzes them, and uses an LLM to generate pairs of:
- **Question:** A hypothetical Job Description.
- **Context:** The relevant sections from the resume.
- **Ground Truth:** An ideal optimized resume snippet.

### 2. Evaluation Runner (`run_evals.py`)
Runs the current RAG pipeline against the Gold Dataset and computes Ragas scores. It outputs a summary report and saves detailed per-case metrics to `latest_eval_results.csv`.

## How to Run

### Step 1: Install Dependencies
Ensure you have the required packages:
```bash
pip install ragas datasets pandas
```

### Step 2: Prepare Sample Data
Place a few diverse resumes (PDF, DOCX, or TXT) in the `data/samples` directory.

### Step 3: Generate Gold Dataset
```bash
python evals/synthetic_data_generator.py
```
This will create `evals/gold_dataset.jsonl`.

### Step 4: Run Evaluation
```bash
python evals/run_evals.py
```

## Interpreting Results

- **Scores range from 0.0 to 1.0.**
- **Faithfulness > 0.9:** Very low hallucination.
- **Answer Relevancy > 0.8:** High-quality optimization.
- **Context Precision/Recall > 0.7:** Strong retrieval performance.

Use these metrics to validate model updates (e.g., switching from Gemini 1.5 Flash to Pro) or changes to your chunking/retrieval strategy.
