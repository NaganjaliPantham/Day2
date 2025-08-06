from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.risk_models import RiskScoringModel, PatternDetector
from models.entity_manager import EntityManager, RecommendationEngine
from utils.data_generator import DataGenerator
from utils.data_processing import DataProcessor

# Initialize FastAPI app
app = FastAPI(
    title="Cybersecurity Risk Scoring API",
    description="Advanced insider threat detection and risk scoring system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
risk_model = RiskScoringModel()
pattern_detector = PatternDetector()
entity_manager = EntityManager()
recommendation_engine = RecommendationEngine()
data_generator = DataGenerator()
data_processor = DataProcessor()

# Pydantic models for API requests
class EntityData(BaseModel):
    entity_id: str
    entity_type: str = "user"
    department: Optional[str] = None
    role: Optional[str] = None
    access_level: int = 1
    metadata: Dict[str, Any] = {}

class SecurityRule(BaseModel):
    rule_id: str
    rule_name: str
    rule_type: str
    conditions: List[Dict[str, Any]]
    weight: float = 1.0
    enabled: bool = True

class RiskAssessmentRequest(BaseModel):
    entity_ids: List[str]
    include_recommendations: bool = True

class TrainingRequest(BaseModel):
    use_sample_data: bool = True
    data_size: int = 1000

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Cybersecurity Risk Scoring API",
        "status": "active",
        "version": "1.0.0"
    }

@app.post("/api/entities")
async def create_entity(entity: EntityData):
    """Create a new entity in the system"""
    try:
        success = entity_manager.add_entity(entity.dict())
        if success:
            return {"status": "success", "message": "Entity created successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to create entity")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entities")
async def get_entities():
    """Get all entities with their current risk scores"""
    try:
        entities = entity_manager.get_all_entities_summary()
        return {"status": "success", "entities": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entities/{entity_id}")
async def get_entity_profile(entity_id: str):
    """Get detailed entity profile with risk history and recommendations"""
    try:
        profile = entity_manager.get_entity_profile(entity_id)
        if profile:
            return {"status": "success", "profile": profile}
        else:
            raise HTTPException(status_code=404, detail="Entity not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/train-model")
async def train_model(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Train the risk scoring model"""
    try:
        if request.use_sample_data:
            # Generate sample training data
            training_data = data_generator.generate_training_data(request.data_size)
            labels = data_generator.generate_risk_labels(training_data)
        else:
            # Load data from database (implementation depends on your data source)
            training_data = pd.DataFrame()  # Placeholder
            labels = None
        
        # Train model in background
        background_tasks.add_task(train_model_background, training_data, labels)
        
        return {
            "status": "success", 
            "message": "Model training started",
            "training_samples": len(training_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def train_model_background(training_data: pd.DataFrame, labels: pd.Series = None):
    """Background task for model training"""
    try:
        result = risk_model.train(training_data, labels)
        print(f"Model training completed: {result}")
    except Exception as e:
        print(f"Model training failed: {str(e)}")

@app.post("/api/assess-risk")
async def assess_risk(request: RiskAssessmentRequest):
    """Assess risk scores for specified entities"""
    try:
        if not risk_model.is_trained:
            raise HTTPException(status_code=400, detail="Model must be trained first")
        
        # Get entity data for assessment
        entity_data = []
        for entity_id in request.entity_ids:
            # Generate current behavioral data for entity
            behavioral_data = data_generator.generate_entity_data(entity_id, 1)
            entity_data.append(behavioral_data.iloc[0])
        
        entity_df = pd.DataFrame(entity_data)
        
        # Predict risk scores
        predictions = risk_model.predict_risk_score(entity_df)
        
        if predictions["status"] == "success":
            # Update database with new scores
            for prediction in predictions["predictions"]:
                entity_manager.update_risk_score(
                    prediction["entity_id"],
                    prediction["risk_score"],
                    prediction["risk_level"],
                    prediction["contributing_factors"]
                )
            
            # Add recommendations if requested
            if request.include_recommendations:
                for prediction in predictions["predictions"]:
                    custom_recs = recommendation_engine.generate_custom_recommendations(
                        {"entity_id": prediction["entity_id"]},
                        prediction["contributing_factors"]
                    )
                    prediction["custom_recommendations"] = custom_recs
        
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/security-rules")
async def create_security_rule(rule: SecurityRule):
    """Create a new security rule for pattern detection"""
    try:
        success = entity_manager.add_security_rule(rule.dict())
        
        # Also add to pattern detector
        pattern_detector.add_pattern(
            rule.rule_id,
            {"conditions": rule.conditions, "description": rule.rule_name},
            rule.weight
        )
        
        if success:
            return {"status": "success", "message": "Security rule created successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to create security rule")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/security-rules")
async def get_security_rules():
    """Get all active security rules"""
    try:
        rules = entity_manager.get_security_rules()
        return {"status": "success", "rules": rules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/detect-patterns")
async def detect_patterns():
    """Run pattern detection on all entities"""
    try:
        # Get recent entity data
        entities = entity_manager.get_all_entities_summary()
        entity_ids = [e["entity_id"] for e in entities]
        
        # Generate current behavioral data
        entity_data_list = []
        for entity_id in entity_ids:
            behavioral_data = data_generator.generate_entity_data(entity_id, 1)
            entity_data_list.append(behavioral_data.iloc[0])
        
        entity_df = pd.DataFrame(entity_data_list)
        
        # Detect patterns
        detected_patterns = pattern_detector.detect_patterns(entity_df)
        
        return {
            "status": "success",
            "detected_patterns": detected_patterns,
            "total_patterns": len(detected_patterns)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard-stats")
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        entities = entity_manager.get_all_entities_summary()
        
        # Calculate statistics
        total_entities = len(entities)
        high_risk_entities = len([e for e in entities if e.get("current_risk_score", 0) > 30])
        medium_risk_entities = len([e for e in entities if 20 <= e.get("current_risk_score", 0) <= 30])
        low_risk_entities = len([e for e in entities if e.get("current_risk_score", 0) < 20])
        
        avg_risk_score = np.mean([e.get("current_risk_score", 0) for e in entities]) if entities else 0
        
        # Risk distribution
        risk_distribution = {
            "Critical": len([e for e in entities if e.get("current_risk_score", 0) > 35]),
            "High": len([e for e in entities if 25 < e.get("current_risk_score", 0) <= 35]),
            "Medium": len([e for e in entities if 15 < e.get("current_risk_score", 0) <= 25]),
            "Low": len([e for e in entities if e.get("current_risk_score", 0) <= 15])
        }
        
        # Department breakdown
        dept_risks = {}
        for entity in entities:
            dept = entity.get("department", "Unknown")
            if dept not in dept_risks:
                dept_risks[dept] = []
            dept_risks[dept].append(entity.get("current_risk_score", 0))
        
        dept_stats = {
            dept: {
                "count": len(scores),
                "avg_risk": np.mean(scores),
                "max_risk": np.max(scores),
                "high_risk_count": len([s for s in scores if s > 30])
            }
            for dept, scores in dept_risks.items()
        }
        
        return {
            "status": "success",
            "stats": {
                "total_entities": total_entities,
                "high_risk_entities": high_risk_entities,
                "medium_risk_entities": medium_risk_entities,
                "low_risk_entities": low_risk_entities,
                "average_risk_score": round(avg_risk_score, 2),
                "risk_distribution": risk_distribution,
                "department_stats": dept_stats,
                "model_status": "trained" if risk_model.is_trained else "not_trained"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations/{recommendation_id}/implement")
async def implement_recommendation(recommendation_id: int, notes: str = ""):
    """Mark a recommendation as implemented"""
    try:
        success = entity_manager.implement_recommendation(recommendation_id, notes)
        if success:
            return {"status": "success", "message": "Recommendation marked as implemented"}
        else:
            raise HTTPException(status_code=400, detail="Failed to implement recommendation")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/initialize-sample-data")
async def initialize_sample_data():
    """Initialize the system with sample entities and data"""
    try:
        # Generate sample entities
        sample_entities = data_generator.generate_sample_entities(50)
        
        for entity_data in sample_entities:
            entity_manager.add_entity(entity_data)
        
        # Add sample security rules
        sample_rules = [
            {
                "rule_id": "high_login_failures",
                "rule_name": "High Login Failures",
                "rule_type": "authentication",
                "conditions": [
                    {"field": "failed_logins", "operator": "gt", "value": 5}
                ],
                "weight": 2.0
            },
            {
                "rule_id": "excessive_data_access",
                "rule_name": "Excessive Data Access",
                "rule_type": "data_access",
                "conditions": [
                    {"field": "data_accessed_gb", "operator": "gt", "value": 100}
                ],
                "weight": 1.5
            },
            {
                "rule_id": "after_hours_activity",
                "rule_name": "Suspicious After Hours Activity",
                "rule_type": "schedule",
                "conditions": [
                    {"field": "after_hours_activity", "operator": "gt", "value": 20}
                ],
                "weight": 1.8
            },
            {
                "rule_id": "privilege_escalation",
                "rule_name": "Privilege Escalation Attempts",
                "rule_type": "access_control",
                "conditions": [
                    {"field": "privilege_escalations", "operator": "gt", "value": 2}
                ],
                "weight": 3.0
            }
        ]
        
        for rule in sample_rules:
            entity_manager.add_security_rule(rule)
            pattern_detector.add_pattern(
                rule["rule_id"],
                {"conditions": rule["conditions"], "description": rule["rule_name"]},
                rule["weight"]
            )
        
        return {
            "status": "success",
            "message": f"Initialized {len(sample_entities)} entities and {len(sample_rules)} security rules"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model-info")
async def get_model_info():
    """Get information about the current model"""
    try:
        return {
            "status": "success",
            "model_info": {
                "is_trained": risk_model.is_trained,
                "feature_importance": risk_model.feature_importance,
                "model_type": "Isolation Forest + Random Forest Ensemble",
                "risk_score_range": "5-50",
                "last_updated": "Not available"  # Could be enhanced with tracking
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)