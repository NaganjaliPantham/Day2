import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from typing import Dict, List, Tuple, Any
import joblib
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskScoringModel:
    """
    Advanced risk scoring model using ensemble of Isolation Forest and Random Forest
    for detecting insider threats and assigning dynamic risk scores (5-50 range)
    """
    
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.random_forest = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            max_depth=10
        )
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_importance = {}
        self.is_trained = False
        
    def preprocess_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess features for ML models
        """
        processed_data = data.copy()
        
        # Handle categorical variables
        categorical_cols = processed_data.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if col != 'entity_id':  # Keep entity_id as identifier
                processed_data[col] = self.label_encoder.fit_transform(processed_data[col].astype(str))
        
        # Handle missing values
        processed_data = processed_data.fillna(processed_data.mean(numeric_only=True))
        
        # Feature engineering for cybersecurity metrics
        if 'login_attempts' in processed_data.columns and 'failed_logins' in processed_data.columns:
            processed_data['login_failure_rate'] = processed_data['failed_logins'] / (processed_data['login_attempts'] + 1)
        
        if 'data_accessed_gb' in processed_data.columns and 'avg_data_access_gb' in processed_data.columns:
            processed_data['data_access_anomaly'] = processed_data['data_accessed_gb'] / (processed_data['avg_data_access_gb'] + 1)
        
        if 'after_hours_activity' in processed_data.columns and 'total_activity' in processed_data.columns:
            processed_data['after_hours_ratio'] = processed_data['after_hours_activity'] / (processed_data['total_activity'] + 1)
        
        return processed_data
    
    def train(self, training_data: pd.DataFrame, labels: pd.Series = None) -> Dict[str, Any]:
        """
        Train the ensemble model on historical data
        """
        try:
            logger.info("Starting model training...")
            
            # Preprocess data
            processed_data = self.preprocess_features(training_data)
            
            # Remove non-feature columns
            feature_cols = [col for col in processed_data.columns if col not in ['entity_id', 'timestamp', 'risk_score']]
            X = processed_data[feature_cols]
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest (unsupervised)
            self.isolation_forest.fit(X_scaled)
            
            # Train Random Forest if labels are provided
            if labels is not None:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, labels, test_size=0.2, random_state=42
                )
                self.random_forest.fit(X_train, y_train)
                
                # Calculate feature importance
                self.feature_importance = dict(zip(feature_cols, self.random_forest.feature_importances_))
                
                # Evaluate model
                accuracy = self.random_forest.score(X_test, y_test)
                logger.info(f"Random Forest accuracy: {accuracy:.3f}")
            
            self.is_trained = True
            logger.info("Model training completed successfully")
            
            return {
                "status": "success",
                "feature_importance": self.feature_importance,
                "training_samples": len(X),
                "features_count": len(feature_cols)
            }
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def predict_risk_score(self, entity_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Predict risk scores for entities (5-50 range)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        try:
            # Preprocess data
            processed_data = self.preprocess_features(entity_data)
            feature_cols = [col for col in processed_data.columns if col not in ['entity_id', 'timestamp', 'risk_score']]
            X = processed_data[feature_cols]
            X_scaled = self.scaler.transform(X)
            
            # Get anomaly scores from Isolation Forest
            isolation_scores = self.isolation_forest.decision_function(X_scaled)
            isolation_predictions = self.isolation_forest.predict(X_scaled)
            
            # Get probability scores from Random Forest
            rf_probabilities = None
            if hasattr(self.random_forest, 'predict_proba'):
                try:
                    rf_probabilities = self.random_forest.predict_proba(X_scaled)[:, 1]
                except:
                    rf_probabilities = np.ones(len(X_scaled)) * 0.5
            
            # Combine scores and normalize to 5-50 range
            risk_scores = self._calculate_dynamic_risk_scores(
                isolation_scores, isolation_predictions, rf_probabilities
            )
            
            # Create detailed results
            results = []
            for i, entity_id in enumerate(entity_data.get('entity_id', range(len(entity_data)))):
                result = {
                    "entity_id": entity_id,
                    "risk_score": float(risk_scores[i]),
                    "risk_level": self._get_risk_level(risk_scores[i]),
                    "anomaly_score": float(isolation_scores[i]),
                    "is_anomaly": bool(isolation_predictions[i] == -1),
                    "timestamp": datetime.now().isoformat(),
                    "contributing_factors": self._get_contributing_factors(X.iloc[i], feature_cols)
                }
                results.append(result)
            
            return {
                "status": "success",
                "predictions": results,
                "model_confidence": np.mean(np.abs(isolation_scores))
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _calculate_dynamic_risk_scores(self, isolation_scores: np.ndarray, 
                                     isolation_predictions: np.ndarray, 
                                     rf_probabilities: np.ndarray = None) -> np.ndarray:
        """
        Calculate dynamic risk scores in the range of 5-50
        """
        # Normalize isolation scores to 0-1 range
        iso_normalized = (isolation_scores - isolation_scores.min()) / (isolation_scores.max() - isolation_scores.min() + 1e-8)
        
        # Combine with Random Forest probabilities if available
        if rf_probabilities is not None:
            combined_scores = 0.6 * (1 - iso_normalized) + 0.4 * rf_probabilities
        else:
            combined_scores = 1 - iso_normalized
        
        # Apply penalties for clear anomalies
        anomaly_penalty = (isolation_predictions == -1).astype(float) * 0.3
        combined_scores += anomaly_penalty
        
        # Clip and scale to 5-50 range
        combined_scores = np.clip(combined_scores, 0, 1)
        risk_scores = 5 + (combined_scores * 45)
        
        return risk_scores
    
    def _get_risk_level(self, risk_score: float) -> str:
        """
        Categorize risk score into levels
        """
        if risk_score <= 15:
            return "Low"
        elif risk_score <= 25:
            return "Medium"
        elif risk_score <= 35:
            return "High"
        else:
            return "Critical"
    
    def _get_contributing_factors(self, entity_features: pd.Series, feature_names: List[str]) -> List[Dict]:
        """
        Identify contributing factors to the risk score
        """
        factors = []
        
        # Get feature importance scores
        for feature, value in zip(feature_names, entity_features):
            importance = self.feature_importance.get(feature, 0.1)
            
            factor = {
                "feature": feature,
                "value": float(value),
                "importance": float(importance),
                "description": self._get_feature_description(feature, value)
            }
            factors.append(factor)
        
        # Sort by importance
        factors.sort(key=lambda x: x['importance'], reverse=True)
        return factors[:5]  # Return top 5 contributing factors
    
    def _get_feature_description(self, feature: str, value: float) -> str:
        """
        Generate human-readable descriptions for features
        """
        descriptions = {
            "login_failure_rate": f"Login failure rate: {value:.2%}",
            "data_access_anomaly": f"Data access anomaly ratio: {value:.2f}",
            "after_hours_ratio": f"After-hours activity ratio: {value:.2%}",
            "failed_logins": f"Failed login attempts: {int(value)}",
            "data_accessed_gb": f"Data accessed: {value:.1f} GB",
            "privilege_escalations": f"Privilege escalation attempts: {int(value)}",
            "suspicious_file_access": f"Suspicious file accesses: {int(value)}",
            "network_anomalies": f"Network anomaly count: {int(value)}"
        }
        
        return descriptions.get(feature, f"{feature}: {value}")
    
    def save_model(self, filepath: str) -> bool:
        """
        Save the trained model
        """
        try:
            model_data = {
                "isolation_forest": self.isolation_forest,
                "random_forest": self.random_forest,
                "scaler": self.scaler,
                "label_encoder": self.label_encoder,
                "feature_importance": self.feature_importance,
                "is_trained": self.is_trained
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
            return False
    
    def load_model(self, filepath: str) -> bool:
        """
        Load a previously trained model
        """
        try:
            model_data = joblib.load(filepath)
            self.isolation_forest = model_data["isolation_forest"]
            self.random_forest = model_data["random_forest"]
            self.scaler = model_data["scaler"]
            self.label_encoder = model_data["label_encoder"]
            self.feature_importance = model_data["feature_importance"]
            self.is_trained = model_data["is_trained"]
            logger.info(f"Model loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False


class PatternDetector:
    """
    Advanced pattern detection for identifying suspicious behaviors and rule violations
    """
    
    def __init__(self):
        self.patterns = []
        self.rule_weights = {}
        
    def add_pattern(self, pattern_id: str, pattern_rule: Dict, weight: float = 1.0):
        """
        Add a new pattern rule for detection
        """
        pattern = {
            "id": pattern_id,
            "rule": pattern_rule,
            "weight": weight,
            "triggered_count": 0,
            "last_triggered": None
        }
        self.patterns.append(pattern)
        self.rule_weights[pattern_id] = weight
    
    def detect_patterns(self, entity_data: pd.DataFrame) -> List[Dict]:
        """
        Detect patterns in entity behavior
        """
        detected_patterns = []
        
        for _, row in entity_data.iterrows():
            for pattern in self.patterns:
                if self._evaluate_pattern(row, pattern["rule"]):
                    detection = {
                        "entity_id": row.get("entity_id", "unknown"),
                        "pattern_id": pattern["id"],
                        "weight": pattern["weight"],
                        "timestamp": datetime.now().isoformat(),
                        "details": self._get_pattern_details(row, pattern["rule"])
                    }
                    detected_patterns.append(detection)
                    pattern["triggered_count"] += 1
                    pattern["last_triggered"] = datetime.now()
        
        return detected_patterns
    
    def _evaluate_pattern(self, entity_row: pd.Series, rule: Dict) -> bool:
        """
        Evaluate if an entity matches a pattern rule
        """
        try:
            for condition in rule.get("conditions", []):
                field = condition["field"]
                operator = condition["operator"]
                value = condition["value"]
                
                if field not in entity_row:
                    continue
                
                entity_value = entity_row[field]
                
                if operator == "gt" and entity_value <= value:
                    return False
                elif operator == "lt" and entity_value >= value:
                    return False
                elif operator == "eq" and entity_value != value:
                    return False
                elif operator == "contains" and str(value).lower() not in str(entity_value).lower():
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Pattern evaluation error: {str(e)}")
            return False
    
    def _get_pattern_details(self, entity_row: pd.Series, rule: Dict) -> Dict:
        """
        Get detailed information about why a pattern was triggered
        """
        details = {
            "rule_description": rule.get("description", "Unknown rule"),
            "triggered_conditions": []
        }
        
        for condition in rule.get("conditions", []):
            field = condition["field"]
            if field in entity_row:
                details["triggered_conditions"].append({
                    "field": field,
                    "operator": condition["operator"],
                    "threshold": condition["value"],
                    "actual_value": entity_row[field]
                })
        
        return details