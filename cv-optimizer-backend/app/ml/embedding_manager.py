"""
Fine-tuned Embedding Manager

Manages domain-specific embeddings fine-tuned on resume/job description pairs.
Provides better semantic understanding of HR terminology and job requirements.

Features:
- Fine-tuning on resume-job pairs
- Model versioning and rollback
- A/B testing support
- Performance monitoring

Author: CV Optimizer Team
Version: 3.0.0
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
from app.core.config import settings
from app.core.logging import logger


@dataclass
class EmbeddingModelConfig:
    """Configuration for embedding model."""
    base_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    fine_tuned_model_path: Optional[str] = None
    model_version: str = "v1.0"
    embedding_dimension: int = 384
    max_seq_length: int = 512
    normalize_embeddings: bool = True


@dataclass
class FineTuningConfig:
    """Configuration for fine-tuning process."""
    num_epochs: int = 3
    batch_size: int = 16
    learning_rate: float = 2e-5
    warmup_steps: int = 100
    evaluation_steps: int = 500
    save_best_model: bool = True
    use_amp: bool = True  # Automatic Mixed Precision


@dataclass
class TrainingExample:
    """Training example for fine-tuning."""
    resume_text: str
    job_description: str
    label: float  # 0-1 similarity score
    metadata: Dict[str, Any] = field(default_factory=dict)


class EmbeddingManager:
    """
    Manages fine-tuned embeddings for resume-job matching.
    
    Capabilities:
    - Load base or fine-tuned models
    - Fine-tune on domain data
    - Version management
    - A/B testing support
    - Performance monitoring
    """
    
    def __init__(
        self,
        config: Optional[EmbeddingModelConfig] = None,
        model_dir: Optional[str] = None
    ):
        """
        Initialize embedding manager.
        
        Args:
            config: Model configuration
            model_dir: Directory for model storage
        """
        self.config = config or EmbeddingModelConfig()
        self.model_dir = model_dir or os.path.join(settings.CHROMA_DB_DIR, "models")
        self._ensure_model_dir()
        
        self.model: Optional[SentenceTransformer] = None
        self.model_metadata: Dict[str, Any] = {}
        self._load_model()
    
    def _ensure_model_dir(self) -> None:
        """Ensure model directory exists."""
        os.makedirs(self.model_dir, exist_ok=True)
    
    def _load_model(self) -> None:
        """Load embedding model (base or fine-tuned)."""
        try:
            if self.config.fine_tuned_model_path and os.path.exists(self.config.fine_tuned_model_path):
                # Load fine-tuned model
                logger.info("loading_fine_tuned_model", path=self.config.fine_tuned_model_path)
                self.model = SentenceTransformer(self.config.fine_tuned_model_path)
                self._load_metadata()
            else:
                # Load base model
                logger.info("loading_base_model", model=self.config.base_model)
                self.model = SentenceTransformer(self.config.base_model)
                self.model_metadata = {
                    "model_type": "base",
                    "base_model": self.config.base_model,
                    "version": self.config.model_version,
                    "created_at": datetime.utcnow().isoformat()
                }
            
            # Set max sequence length
            self.model.max_seq_length = self.config.max_seq_length
            
            logger.info("model_loaded", 
                       model_type=self.model_metadata.get("model_type", "base"),
                       version=self.model_metadata.get("version"))
            
        except Exception as e:
            logger.error("model_load_failed", error=str(e))
            raise
    
    def _load_metadata(self) -> None:
        """Load model metadata."""
        metadata_path = os.path.join(self.config.fine_tuned_model_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                self.model_metadata = json.load(f)
    
    def _save_metadata(self, save_path: str) -> None:
        """Save model metadata."""
        metadata_path = os.path.join(save_path, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(self.model_metadata, f, indent=2)
    
    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Encode texts to embeddings.
        
        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            Numpy array of embeddings
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=self.config.normalize_embeddings
        )
        
        return embeddings
    
    def fine_tune(
        self,
        training_examples: List[TrainingExample],
        validation_examples: Optional[List[TrainingExample]] = None,
        config: Optional[FineTuningConfig] = None
    ) -> Dict[str, Any]:
        """
        Fine-tune model on domain-specific data.
        
        Args:
            training_examples: Training data
            validation_examples: Validation data
            config: Fine-tuning configuration
            
        Returns:
            Training statistics
        """
        config = config or FineTuningConfig()
        
        logger.info("fine_tuning_started",
                   num_training=len(training_examples),
                   num_validation=len(validation_examples) if validation_examples else 0)
        
        try:
            # Prepare training data
            train_examples = [
                InputExample(
                    texts=[ex.resume_text, ex.job_description],
                    label=ex.label
                )
                for ex in training_examples
            ]
            
            train_dataloader = DataLoader(
                train_examples,
                shuffle=True,
                batch_size=config.batch_size
            )
            
            # Define loss function (Cosine Similarity Loss)
            train_loss = losses.CosineSimilarityLoss(self.model)
            
            # Calculate training steps
            num_train_steps = len(train_dataloader) * config.num_epochs
            
            # Fine-tune model
            self.model.fit(
                train_objectives=[(train_dataloader, train_loss)],
                epochs=config.num_epochs,
                warmup_steps=config.warmup_steps,
                evaluation_steps=config.evaluation_steps,
                output_path=None,  # Don't save during training
                show_progress_bar=True,
                use_amp=config.use_amp
            )
            
            # Evaluate on validation set if provided
            validation_score = None
            if validation_examples:
                validation_score = self._evaluate(validation_examples)
            
            # Save fine-tuned model
            save_path = self._get_save_path()
            self.model.save(save_path)
            
            # Update metadata
            self.model_metadata = {
                "model_type": "fine_tuned",
                "base_model": self.config.base_model,
                "version": self.config.model_version,
                "fine_tuned_at": datetime.utcnow().isoformat(),
                "num_training_examples": len(training_examples),
                "num_epochs": config.num_epochs,
                "validation_score": validation_score,
                "training_config": {
                    "batch_size": config.batch_size,
                    "learning_rate": config.learning_rate,
                    "warmup_steps": config.warmup_steps
                }
            }
            self._save_metadata(save_path)
            
            # Update config to use fine-tuned model
            self.config.fine_tuned_model_path = save_path
            
            logger.info("fine_tuning_completed",
                       save_path=save_path,
                       validation_score=validation_score)
            
            return {
                "success": True,
                "save_path": save_path,
                "validation_score": validation_score,
                "num_training_examples": len(training_examples)
            }
            
        except Exception as e:
            logger.error("fine_tuning_failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _evaluate(self, examples: List[TrainingExample]) -> float:
        """
        Evaluate model on examples.
        
        Args:
            examples: Evaluation examples
            
        Returns:
            Average cosine similarity score
        """
        scores = []
        
        for ex in examples:
            # Encode texts
            emb1 = self.encode([ex.resume_text])[0]
            emb2 = self.encode([ex.job_description])[0]
            
            # Calculate cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            # Compare with label
            error = abs(similarity - ex.label)
            scores.append(1.0 - error)  # Convert error to score
        
        return float(np.mean(scores))
    
    def _get_save_path(self) -> str:
        """Get save path for fine-tuned model."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_name = f"fine_tuned_{self.config.model_version}_{timestamp}"
        return os.path.join(self.model_dir, model_name)
    
    def compare_models(
        self,
        other_model_path: str,
        test_examples: List[TrainingExample]
    ) -> Dict[str, Any]:
        """
        Compare current model with another model.
        
        Args:
            other_model_path: Path to other model
            test_examples: Test examples for comparison
            
        Returns:
            Comparison results
        """
        logger.info("comparing_models", other_model=other_model_path)
        
        # Evaluate current model
        current_score = self._evaluate(test_examples)
        
        # Load and evaluate other model
        other_model = SentenceTransformer(other_model_path)
        
        # Temporarily swap models
        original_model = self.model
        self.model = other_model
        other_score = self._evaluate(test_examples)
        self.model = original_model
        
        comparison = {
            "current_model": {
                "path": self.config.fine_tuned_model_path or "base",
                "score": current_score
            },
            "other_model": {
                "path": other_model_path,
                "score": other_score
            },
            "winner": "current" if current_score > other_score else "other",
            "improvement": abs(current_score - other_score)
        }
        
        logger.info("model_comparison_complete", **comparison)
        return comparison
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model."""
        return {
            "model_type": self.model_metadata.get("model_type", "base"),
            "version": self.model_metadata.get("version"),
            "base_model": self.config.base_model,
            "embedding_dimension": self.config.embedding_dimension,
            "max_seq_length": self.config.max_seq_length,
            "fine_tuned_at": self.model_metadata.get("fine_tuned_at"),
            "validation_score": self.model_metadata.get("validation_score"),
            "path": self.config.fine_tuned_model_path or "base"
        }


# Singleton instance
_embedding_manager: Optional[EmbeddingManager] = None


def get_embedding_manager(
    config: Optional[EmbeddingModelConfig] = None
) -> EmbeddingManager:
    """
    Get or create global embedding manager instance.
    
    Args:
        config: Optional configuration
        
    Returns:
        EmbeddingManager instance
    """
    global _embedding_manager
    
    if _embedding_manager is None:
        _embedding_manager = EmbeddingManager(config)
    
    return _embedding_manager
