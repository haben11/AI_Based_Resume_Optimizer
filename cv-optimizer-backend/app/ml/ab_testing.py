"""
A/B Testing Framework

Systematic testing of different RAG configurations to find optimal settings.
Supports multi-variant testing and statistical significance analysis.

Author: CV Optimizer Team
Version: 3.0.0
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import hashlib
from scipy import stats
import numpy as np
from app.core.logging import logger


class ExperimentStatus(str, Enum):
    """Status of A/B test experiment."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Variant:
    """A/B test variant configuration."""
    variant_id: str
    name: str
    description: str
    config: Dict[str, Any]
    traffic_allocation: float  # 0-1, percentage of traffic
    
    # Metrics
    impressions: int = 0
    conversions: int = 0
    total_score: float = 0.0
    
    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate."""
        return self.conversions / self.impressions if self.impressions > 0 else 0.0
    
    @property
    def avg_score(self) -> float:
        """Calculate average score."""
        return self.total_score / self.impressions if self.impressions > 0 else 0.0


@dataclass
class Experiment:
    """A/B test experiment."""
    experiment_id: str
    name: str
    description: str
    variants: List[Variant]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Configuration
    min_sample_size: int = 100  # Minimum samples per variant
    confidence_level: float = 0.95  # Statistical confidence
    
    def get_variant_for_user(self, user_id: str) -> Variant:
        """
        Get variant for user using consistent hashing.
        
        Args:
            user_id: User identifier
            
        Returns:
            Assigned variant
        """
        # Use consistent hashing for stable assignment
        hash_value = int(hashlib.md5(
            f"{self.experiment_id}_{user_id}".encode()
        ).hexdigest(), 16)
        
        # Normalize to 0-1
        normalized = (hash_value % 10000) / 10000.0
        
        # Assign based on traffic allocation
        cumulative = 0.0
        for variant in self.variants:
            cumulative += variant.traffic_allocation
            if normalized <= cumulative:
                return variant
        
        # Fallback to first variant
        return self.variants[0]


class ABTestingFramework:
    """
    A/B testing framework for RAG optimization.
    
    Features:
    - Multi-variant testing
    - Consistent user assignment
    - Statistical significance testing
    - Automatic winner selection
    - Performance monitoring
    """
    
    def __init__(self):
        """Initialize A/B testing framework."""
        self.experiments: Dict[str, Experiment] = {}
    
    def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        min_sample_size: int = 100,
        confidence_level: float = 0.95
    ) -> Experiment:
        """
        Create new A/B test experiment.
        
        Args:
            name: Experiment name
            description: Experiment description
            variants: List of variant configurations
            min_sample_size: Minimum samples per variant
            confidence_level: Statistical confidence level
            
        Returns:
            Created experiment
        """
        experiment_id = f"exp_{datetime.utcnow().timestamp()}"
        
        # Create variant objects
        variant_objects = []
        for i, var_config in enumerate(variants):
            variant = Variant(
                variant_id=f"{experiment_id}_v{i}",
                name=var_config.get("name", f"Variant {i}"),
                description=var_config.get("description", ""),
                config=var_config.get("config", {}),
                traffic_allocation=var_config.get("traffic_allocation", 1.0 / len(variants))
            )
            variant_objects.append(variant)
        
        # Normalize traffic allocation
        total_allocation = sum(v.traffic_allocation for v in variant_objects)
        for variant in variant_objects:
            variant.traffic_allocation /= total_allocation
        
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            variants=variant_objects,
            min_sample_size=min_sample_size,
            confidence_level=confidence_level
        )
        
        self.experiments[experiment_id] = experiment
        
        logger.info("experiment_created",
                   experiment_id=experiment_id,
                   num_variants=len(variant_objects))
        
        return experiment
    
    def start_experiment(self, experiment_id: str) -> None:
        """Start running experiment."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.utcnow()
        
        logger.info("experiment_started", experiment_id=experiment_id)
    
    def record_impression(
        self,
        experiment_id: str,
        user_id: str
    ) -> Variant:
        """
        Record impression and get variant for user.
        
        Args:
            experiment_id: Experiment identifier
            user_id: User identifier
            
        Returns:
            Assigned variant
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            # Return default variant if experiment not running
            return None
        
        variant = experiment.get_variant_for_user(user_id)
        variant.impressions += 1
        
        return variant
    
    def record_conversion(
        self,
        experiment_id: str,
        user_id: str,
        score: float = 1.0
    ) -> None:
        """
        Record conversion event.
        
        Args:
            experiment_id: Experiment identifier
            user_id: User identifier
            score: Quality score (0-1)
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return
        
        variant = experiment.get_variant_for_user(user_id)
        variant.conversions += 1
        variant.total_score += score
        
        logger.info("conversion_recorded",
                   experiment_id=experiment_id,
                   variant_id=variant.variant_id,
                   score=score)
    
    def analyze_experiment(
        self,
        experiment_id: str
    ) -> Dict[str, Any]:
        """
        Analyze experiment results.
        
        Args:
            experiment_id: Experiment identifier
            
        Returns:
            Analysis results with statistical significance
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # Check if minimum sample size reached
        min_samples_reached = all(
            v.impressions >= experiment.min_sample_size
            for v in experiment.variants
        )
        
        if not min_samples_reached:
            return {
                "status": "insufficient_data",
                "message": "Minimum sample size not reached",
                "variants": [self._variant_summary(v) for v in experiment.variants]
            }
        
        # Perform statistical tests
        # Compare each variant against control (first variant)
        control = experiment.variants[0]
        comparisons = []
        
        for variant in experiment.variants[1:]:
            comparison = self._compare_variants(control, variant, experiment.confidence_level)
            comparisons.append(comparison)
        
        # Determine winner
        winner = self._determine_winner(experiment.variants)
        
        analysis = {
            "status": "complete",
            "min_samples_reached": min_samples_reached,
            "control": self._variant_summary(control),
            "variants": [self._variant_summary(v) for v in experiment.variants[1:]],
            "comparisons": comparisons,
            "winner": winner,
            "recommendation": self._generate_recommendation(winner, comparisons)
        }
        
        logger.info("experiment_analyzed",
                   experiment_id=experiment_id,
                   winner=winner.get("variant_id") if winner else None)
        
        return analysis
    
    def _variant_summary(self, variant: Variant) -> Dict[str, Any]:
        """Generate variant summary."""
        return {
            "variant_id": variant.variant_id,
            "name": variant.name,
            "impressions": variant.impressions,
            "conversions": variant.conversions,
            "conversion_rate": variant.conversion_rate,
            "avg_score": variant.avg_score,
            "traffic_allocation": variant.traffic_allocation
        }
    
    def _compare_variants(
        self,
        control: Variant,
        variant: Variant,
        confidence_level: float
    ) -> Dict[str, Any]:
        """
        Compare variant against control using statistical tests.
        
        Args:
            control: Control variant
            variant: Test variant
            confidence_level: Confidence level for significance
            
        Returns:
            Comparison results
        """
        # Use two-proportion z-test for conversion rates
        n1, n2 = control.impressions, variant.impressions
        p1, p2 = control.conversion_rate, variant.conversion_rate
        
        # Calculate pooled proportion
        p_pool = (control.conversions + variant.conversions) / (n1 + n2)
        
        # Calculate standard error
        se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        
        # Calculate z-score
        z_score = (p2 - p1) / se if se > 0 else 0
        
        # Calculate p-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        # Determine significance
        is_significant = p_value < (1 - confidence_level)
        
        # Calculate lift
        lift = ((p2 - p1) / p1 * 100) if p1 > 0 else 0
        
        return {
            "variant_id": variant.variant_id,
            "variant_name": variant.name,
            "control_rate": p1,
            "variant_rate": p2,
            "lift_percent": lift,
            "z_score": z_score,
            "p_value": p_value,
            "is_significant": is_significant,
            "confidence_level": confidence_level
        }
    
    def _determine_winner(self, variants: List[Variant]) -> Optional[Dict[str, Any]]:
        """Determine winning variant based on avg_score."""
        if not variants:
            return None
        
        winner = max(variants, key=lambda v: v.avg_score)
        
        return {
            "variant_id": winner.variant_id,
            "variant_name": winner.name,
            "avg_score": winner.avg_score,
            "conversion_rate": winner.conversion_rate
        }
    
    def _generate_recommendation(
        self,
        winner: Optional[Dict[str, Any]],
        comparisons: List[Dict[str, Any]]
    ) -> str:
        """Generate recommendation based on results."""
        if not winner:
            return "Insufficient data to make recommendation"
        
        # Check if any variant is significantly better
        significant_improvements = [
            c for c in comparisons
            if c["is_significant"] and c["lift_percent"] > 0
        ]
        
        if significant_improvements:
            best = max(significant_improvements, key=lambda x: x["lift_percent"])
            return f"Deploy {best['variant_name']} - {best['lift_percent']:.1f}% improvement (statistically significant)"
        
        return "No statistically significant difference found. Continue testing or deploy control."
    
    def stop_experiment(self, experiment_id: str) -> None:
        """Stop running experiment."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return
        
        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = datetime.utcnow()
        
        logger.info("experiment_stopped", experiment_id=experiment_id)


# Singleton instance
_ab_testing_framework: Optional[ABTestingFramework] = None


def get_ab_testing_framework() -> ABTestingFramework:
    """
    Get or create global A/B testing framework instance.
    
    Returns:
        ABTestingFramework instance
    """
    global _ab_testing_framework
    
    if _ab_testing_framework is None:
        _ab_testing_framework = ABTestingFramework()
    
    return _ab_testing_framework
