"""
Synthetic Test Set Generator for RAG Evaluation

This module uses Ragas to generate a synthetic dataset of (Job Description, Resume Context, 
Gold Answer) triples from raw resume files. This dataset serves as the "Gold Standard"
for evaluating the RAG pipeline's performance.

Author: Antigravity AI
Version: 1.0.0
"""

import os
import asyncio
from typing import List
from datasets import Dataset
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.core.config import settings
from app.utils.file_parser import FileParser
from langchain.schema import Document


async def generate_gold_dataset(resume_paths: List[str], output_path: str = "evals/gold_dataset.jsonl"):
    """
    Generate a synthetic test set from a list of resumes.
    """
    print(f"Loading {len(resume_paths)} resumes for synthetic data generation...")
    
    documents = []
    for path in resume_paths:
        try:
            text = await FileParser.parse_file_path(path)
            # Create a LangChain document
            doc = Document(
                page_content=text,
                metadata={"source": os.path.basename(path)}
            )
            documents.append(doc)
        except Exception as e:
            print(f"Failed to parse {path}: {e}")

    if not documents:
        print("No documents found. Aborting.")
        return

    # Initialize LLM and Embeddings for generation
    generator_llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=settings.GOOGLE_API_KEY
    )
    critic_llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=settings.GOOGLE_API_KEY
    )
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GOOGLE_API_KEY
    )

    # Initialize Generator
    generator = TestsetGenerator.from_langchain(
        generator_llm,
        critic_llm,
        embeddings
    )

    # Define distribution of test case types
    distributions = {
        simple: 0.5,
        reasoning: 0.25,
        multi_context: 0.25
    }

    print("Generating synthetic test set (this may take a few minutes)...")
    testset = generator.generate_with_langchain_docs(
        documents, 
        test_size=10,  # Number of test cases to generate
        distributions=distributions
    )

    # Save to disk
    df = testset.to_pandas()
    df.to_json(output_path, orient="records", lines=True)
    print(f"Successfully generated gold dataset with {len(df)} cases at {output_path}")


if __name__ == "__main__":
    # Example usage: point to a directory of sample resumes
    sample_dir = "data/samples"
    if not os.path.exists(sample_dir):
        os.makedirs(sample_dir, exist_ok=True)
        print(f"Please place some sample resumes in {sample_dir} then run this script again.")
    else:
        sample_files = [
            os.path.join(sample_dir, f) for f in os.listdir(sample_dir) 
            if f.endswith(('.pdf', '.docx', '.txt'))
        ]
        if sample_files:
            asyncio.run(generate_gold_dataset(sample_files))
        else:
            print(f"No sample resumes found in {sample_dir}")
