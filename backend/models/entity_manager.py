import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sqlite3
import json
import logging

logger = logging.getLogger(__name__)

class EntityManager:
    """
    Manages entities, their profiles, and provides actionable recommendations
    """
    
    def __init__(self, db_path: str = "/workspace/backend/data/entities.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """
        Initialize the database with required tables
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Entities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    department TEXT,
                    role TEXT,
                    access_level INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    metadata TEXT
                )
            ''')
            
            # Risk scores history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT,
                    risk_score REAL,
                    risk_level TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contributing_factors TEXT,
                    model_version TEXT,
                    FOREIGN KEY (entity_id) REFERENCES entities (entity_id)
                )
            ''')
            
            # Recommendations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT,
                    recommendation_type TEXT,
                    title TEXT,
                    description TEXT,
                    priority INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    implemented_at TIMESTAMP,
                    impact_score REAL,
                    FOREIGN KEY (entity_id) REFERENCES entities (entity_id)
                )
            ''')
            
            # Rules table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_name TEXT NOT NULL,
                    rule_type TEXT,
                    conditions TEXT,
                    weight REAL DEFAULT 1.0,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_triggered TIMESTAMP,
                    trigger_count INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def add_entity(self, entity_data: Dict) -> bool:
        """
        Add a new entity to the system
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO entities 
                (entity_id, entity_type, department, role, access_level, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                entity_data.get('entity_id'),
                entity_data.get('entity_type', 'user'),
                entity_data.get('department'),
                entity_data.get('role'),
                entity_data.get('access_level', 1),
                json.dumps(entity_data.get('metadata', {}))
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to add entity: {str(e)}")
            return False
    
    def get_entity_profile(self, entity_id: str) -> Optional[Dict]:
        """
        Get comprehensive entity profile with risk history
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get entity basic info
            entity_df = pd.read_sql_query(
                "SELECT * FROM entities WHERE entity_id = ?", 
                conn, params=[entity_id]
            )
            
            if entity_df.empty:
                conn.close()
                return None
            
            # Get recent risk scores
            risk_history_df = pd.read_sql_query('''
                SELECT * FROM risk_scores 
                WHERE entity_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 30
            ''', conn, params=[entity_id])
            
            # Get active recommendations
            recommendations_df = pd.read_sql_query('''
                SELECT * FROM recommendations 
                WHERE entity_id = ? AND status = 'pending'
                ORDER BY priority DESC, created_at DESC
            ''', conn, params=[entity_id])
            
            conn.close()
            
            # Build profile
            entity_info = entity_df.iloc[0].to_dict()
            entity_info['metadata'] = json.loads(entity_info.get('metadata', '{}'))
            
            profile = {
                "entity_info": entity_info,
                "current_risk_score": float(risk_history_df.iloc[0]['risk_score']) if not risk_history_df.empty else 5.0,
                "current_risk_level": risk_history_df.iloc[0]['risk_level'] if not risk_history_df.empty else "Low",
                "risk_trend": self._calculate_risk_trend(risk_history_df),
                "risk_history": risk_history_df.to_dict('records'),
                "active_recommendations": recommendations_df.to_dict('records'),
                "risk_statistics": self._calculate_risk_statistics(risk_history_df)
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get entity profile: {str(e)}")
            return None
    
    def update_risk_score(self, entity_id: str, risk_score: float, risk_level: str, 
                         contributing_factors: List[Dict], model_version: str = "1.0") -> bool:
        """
        Update entity's risk score and store in history
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO risk_scores 
                (entity_id, risk_score, risk_level, contributing_factors, model_version)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                entity_id,
                risk_score,
                risk_level,
                json.dumps(contributing_factors),
                model_version
            ))
            
            # Update entity last_updated timestamp
            cursor.execute('''
                UPDATE entities 
                SET last_updated = CURRENT_TIMESTAMP 
                WHERE entity_id = ?
            ''', (entity_id,))
            
            conn.commit()
            conn.close()
            
            # Generate recommendations based on new risk score
            self._generate_recommendations(entity_id, risk_score, risk_level, contributing_factors)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update risk score: {str(e)}")
            return False
    
    def _calculate_risk_trend(self, risk_history_df: pd.DataFrame) -> str:
        """
        Calculate risk trend (increasing, decreasing, stable)
        """
        if len(risk_history_df) < 2:
            return "insufficient_data"
        
        recent_scores = risk_history_df.head(5)['risk_score'].values
        older_scores = risk_history_df.tail(5)['risk_score'].values
        
        recent_avg = np.mean(recent_scores)
        older_avg = np.mean(older_scores)
        
        diff = recent_avg - older_avg
        
        if diff > 2:
            return "increasing"
        elif diff < -2:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_risk_statistics(self, risk_history_df: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive risk statistics
        """
        if risk_history_df.empty:
            return {}
        
        scores = risk_history_df['risk_score'].values
        
        return {
            "average_score": float(np.mean(scores)),
            "max_score": float(np.max(scores)),
            "min_score": float(np.min(scores)),
            "std_deviation": float(np.std(scores)),
            "score_volatility": float(np.std(scores) / np.mean(scores)) if np.mean(scores) > 0 else 0,
            "high_risk_incidents": int(np.sum(scores > 30)),
            "days_tracked": len(scores)
        }
    
    def _generate_recommendations(self, entity_id: str, risk_score: float, 
                                risk_level: str, contributing_factors: List[Dict]):
        """
        Generate actionable recommendations based on risk assessment
        """
        recommendations = []
        
        # High-risk recommendations
        if risk_score > 30:
            recommendations.extend([
                {
                    "type": "access_control",
                    "title": "Implement Enhanced Monitoring",
                    "description": "Enable detailed logging and real-time monitoring for this high-risk entity",
                    "priority": 9
                },
                {
                    "type": "access_restriction",
                    "title": "Review Access Permissions",
                    "description": "Conduct immediate review of access privileges and consider temporary restrictions",
                    "priority": 8
                }
            ])
        
        # Factor-specific recommendations
        for factor in contributing_factors:
            feature = factor.get('feature', '')
            importance = factor.get('importance', 0)
            
            if importance > 0.1:  # Only for significant factors
                if 'login_failure' in feature:
                    recommendations.append({
                        "type": "authentication",
                        "title": "Strengthen Authentication",
                        "description": f"Consider implementing MFA due to high login failure rate: {factor.get('description')}",
                        "priority": 7
                    })
                
                elif 'data_access' in feature:
                    recommendations.append({
                        "type": "data_protection",
                        "title": "Monitor Data Access",
                        "description": f"Enhanced data access monitoring recommended: {factor.get('description')}",
                        "priority": 6
                    })
                
                elif 'after_hours' in feature:
                    recommendations.append({
                        "type": "schedule_monitoring",
                        "title": "After-Hours Alert",
                        "description": f"Set up after-hours activity alerts: {factor.get('description')}",
                        "priority": 5
                    })
                
                elif 'privilege' in feature:
                    recommendations.append({
                        "type": "privilege_management",
                        "title": "Privilege Escalation Review",
                        "description": f"Review privilege escalation patterns: {factor.get('description')}",
                        "priority": 8
                    })
        
        # Configuration recommendations
        if risk_score > 20:
            recommendations.extend([
                {
                    "type": "firewall_config",
                    "title": "Update Firewall Rules",
                    "description": "Review and tighten firewall rules for this entity's typical access patterns",
                    "priority": 4
                },
                {
                    "type": "network_segmentation",
                    "title": "Network Segmentation",
                    "description": "Consider network segmentation to limit potential impact",
                    "priority": 5
                }
            ])
        
        # Store recommendations in database
        self._store_recommendations(entity_id, recommendations)
    
    def _store_recommendations(self, entity_id: str, recommendations: List[Dict]):
        """
        Store recommendations in database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for rec in recommendations:
                cursor.execute('''
                    INSERT INTO recommendations 
                    (entity_id, recommendation_type, title, description, priority, impact_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    entity_id,
                    rec.get('type'),
                    rec.get('title'),
                    rec.get('description'),
                    rec.get('priority', 5),
                    rec.get('impact_score', 1.0)
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store recommendations: {str(e)}")
    
    def get_all_entities_summary(self) -> List[Dict]:
        """
        Get summary of all entities with current risk scores
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = '''
                SELECT 
                    e.entity_id,
                    e.entity_type,
                    e.department,
                    e.role,
                    e.status,
                    COALESCE(rs.risk_score, 5.0) as current_risk_score,
                    COALESCE(rs.risk_level, 'Low') as current_risk_level,
                    rs.timestamp as last_assessed,
                    COUNT(rec.id) as pending_recommendations
                FROM entities e
                LEFT JOIN (
                    SELECT entity_id, risk_score, risk_level, timestamp,
                           ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY timestamp DESC) as rn
                    FROM risk_scores
                ) rs ON e.entity_id = rs.entity_id AND rs.rn = 1
                LEFT JOIN recommendations rec ON e.entity_id = rec.entity_id AND rec.status = 'pending'
                GROUP BY e.entity_id, e.entity_type, e.department, e.role, e.status, 
                         rs.risk_score, rs.risk_level, rs.timestamp
                ORDER BY current_risk_score DESC
            '''
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Failed to get entities summary: {str(e)}")
            return []
    
    def implement_recommendation(self, recommendation_id: int, implementation_notes: str = "") -> bool:
        """
        Mark a recommendation as implemented
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE recommendations 
                SET status = 'implemented', 
                    implemented_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (recommendation_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to implement recommendation: {str(e)}")
            return False
    
    def add_security_rule(self, rule_data: Dict) -> bool:
        """
        Add a new security rule for pattern detection
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO security_rules 
                (rule_id, rule_name, rule_type, conditions, weight, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                rule_data.get('rule_id'),
                rule_data.get('rule_name'),
                rule_data.get('rule_type'),
                json.dumps(rule_data.get('conditions', [])),
                rule_data.get('weight', 1.0),
                rule_data.get('enabled', True)
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to add security rule: {str(e)}")
            return False
    
    def get_security_rules(self) -> List[Dict]:
        """
        Get all security rules
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM security_rules WHERE enabled = 1", conn)
            conn.close()
            
            rules = df.to_dict('records')
            for rule in rules:
                rule['conditions'] = json.loads(rule.get('conditions', '[]'))
            
            return rules
            
        except Exception as e:
            logger.error(f"Failed to get security rules: {str(e)}")
            return []


class RecommendationEngine:
    """
    Advanced recommendation engine for cybersecurity actions
    """
    
    def __init__(self):
        self.recommendation_templates = {
            "authentication": {
                "mfa_enable": {
                    "title": "Enable Multi-Factor Authentication",
                    "description": "Implement MFA to reduce authentication-related risks",
                    "implementation_steps": [
                        "Configure MFA in identity provider",
                        "Notify user of new requirement",
                        "Monitor adoption and compliance"
                    ],
                    "expected_impact": 0.7
                },
                "password_policy": {
                    "title": "Enforce Strong Password Policy",
                    "description": "Update password requirements for enhanced security",
                    "implementation_steps": [
                        "Update password complexity requirements",
                        "Set password expiration policy",
                        "Implement password history checking"
                    ],
                    "expected_impact": 0.5
                }
            },
            "access_control": {
                "privilege_review": {
                    "title": "Conduct Privilege Review",
                    "description": "Review and optimize user access privileges",
                    "implementation_steps": [
                        "Audit current permissions",
                        "Remove unnecessary access",
                        "Document changes and rationale"
                    ],
                    "expected_impact": 0.6
                },
                "session_timeout": {
                    "title": "Implement Session Timeout",
                    "description": "Reduce session timeout to minimize exposure window",
                    "implementation_steps": [
                        "Configure shorter session timeouts",
                        "Implement automatic logout",
                        "Notify users of changes"
                    ],
                    "expected_impact": 0.4
                }
            },
            "monitoring": {
                "enhanced_logging": {
                    "title": "Enable Enhanced Logging",
                    "description": "Increase logging detail for better threat detection",
                    "implementation_steps": [
                        "Configure detailed audit logging",
                        "Set up log analysis alerts",
                        "Review log retention policies"
                    ],
                    "expected_impact": 0.8
                },
                "real_time_alerts": {
                    "title": "Configure Real-time Alerts",
                    "description": "Set up immediate notifications for suspicious activities",
                    "implementation_steps": [
                        "Define alert thresholds",
                        "Configure notification channels",
                        "Test alert mechanisms"
                    ],
                    "expected_impact": 0.9
                }
            }
        }
    
    def generate_custom_recommendations(self, entity_data: Dict, risk_factors: List[Dict]) -> List[Dict]:
        """
        Generate customized recommendations based on specific risk factors
        """
        recommendations = []
        
        # Analyze risk factors and suggest appropriate actions
        for factor in risk_factors:
            feature = factor.get('feature', '')
            importance = factor.get('importance', 0)
            
            if importance < 0.1:  # Skip low-importance factors
                continue
            
            category = self._categorize_risk_factor(feature)
            if category and category in self.recommendation_templates:
                template_key = self._select_best_template(category, factor)
                if template_key:
                    template = self.recommendation_templates[category][template_key]
                    
                    recommendation = {
                        "category": category,
                        "template_key": template_key,
                        "title": template["title"],
                        "description": template["description"],
                        "priority": self._calculate_priority(importance, factor),
                        "expected_impact": template["expected_impact"],
                        "implementation_steps": template["implementation_steps"],
                        "estimated_effort": self._estimate_effort(template_key),
                        "risk_reduction": importance * template["expected_impact"]
                    }
                    recommendations.append(recommendation)
        
        # Sort by risk reduction potential
        recommendations.sort(key=lambda x: x['risk_reduction'], reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _categorize_risk_factor(self, feature: str) -> Optional[str]:
        """
        Categorize risk factor into recommendation category
        """
        if any(term in feature.lower() for term in ['login', 'auth', 'password']):
            return "authentication"
        elif any(term in feature.lower() for term in ['access', 'privilege', 'permission']):
            return "access_control"
        elif any(term in feature.lower() for term in ['log', 'monitor', 'alert']):
            return "monitoring"
        return None
    
    def _select_best_template(self, category: str, factor: Dict) -> Optional[str]:
        """
        Select the most appropriate template for a given factor
        """
        feature = factor.get('feature', '').lower()
        
        if category == "authentication":
            if 'failure' in feature or 'failed' in feature:
                return "mfa_enable"
            else:
                return "password_policy"
        elif category == "access_control":
            if 'privilege' in feature:
                return "privilege_review"
            else:
                return "session_timeout"
        elif category == "monitoring":
            if factor.get('importance', 0) > 0.3:
                return "real_time_alerts"
            else:
                return "enhanced_logging"
        
        return None
    
    def _calculate_priority(self, importance: float, factor: Dict) -> int:
        """
        Calculate recommendation priority (1-10)
        """
        base_priority = min(10, max(1, int(importance * 10)))
        
        # Adjust based on factor value
        value = factor.get('value', 0)
        if value > 10:  # High values indicate higher risk
            base_priority = min(10, base_priority + 2)
        
        return base_priority
    
    def _estimate_effort(self, template_key: str) -> str:
        """
        Estimate implementation effort
        """
        effort_map = {
            "mfa_enable": "Medium",
            "password_policy": "Low",
            "privilege_review": "High",
            "session_timeout": "Low",
            "enhanced_logging": "Medium",
            "real_time_alerts": "High"
        }
        
        return effort_map.get(template_key, "Medium")