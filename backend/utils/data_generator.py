import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
import uuid

class DataGenerator:
    """
    Generates realistic sample data for training and testing the risk scoring system
    """
    
    def __init__(self):
        self.departments = ["IT", "Finance", "HR", "Sales", "Marketing", "Operations", "Legal", "Research"]
        self.roles = ["Manager", "Analyst", "Developer", "Administrator", "Specialist", "Director", "Executive", "Intern"]
        self.entity_types = ["user", "service_account", "contractor", "admin"]
        
        # Risk factors for different entity characteristics
        self.risk_profiles = {
            "low_risk": {
                "failed_logins_range": (0, 2),
                "data_accessed_gb_range": (1, 50),
                "after_hours_activity_range": (0, 5),
                "privilege_escalations_range": (0, 1),
                "suspicious_file_access_range": (0, 2),
                "network_anomalies_range": (0, 3)
            },
            "medium_risk": {
                "failed_logins_range": (2, 8),
                "data_accessed_gb_range": (50, 150),
                "after_hours_activity_range": (5, 20),
                "privilege_escalations_range": (1, 3),
                "suspicious_file_access_range": (2, 8),
                "network_anomalies_range": (3, 10)
            },
            "high_risk": {
                "failed_logins_range": (8, 25),
                "data_accessed_gb_range": (150, 500),
                "after_hours_activity_range": (20, 50),
                "privilege_escalations_range": (3, 8),
                "suspicious_file_access_range": (8, 20),
                "network_anomalies_range": (10, 25)
            }
        }
    
    def generate_sample_entities(self, count: int = 50) -> List[Dict]:
        """
        Generate sample entities with realistic profiles
        """
        entities = []
        
        for i in range(count):
            entity_id = f"USER_{i+1:04d}"
            department = random.choice(self.departments)
            role = random.choice(self.roles)
            entity_type = random.choice(self.entity_types)
            
            # Access level based on role
            access_level = self._determine_access_level(role, department)
            
            entity = {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "department": department,
                "role": role,
                "access_level": access_level,
                "metadata": {
                    "hire_date": (datetime.now() - timedelta(days=random.randint(30, 3650))).isoformat(),
                    "last_login": (datetime.now() - timedelta(hours=random.randint(1, 168))).isoformat(),
                    "location": random.choice(["Office", "Remote", "Hybrid"]),
                    "security_clearance": random.choice(["Standard", "Elevated", "Administrative"]),
                    "training_completed": random.choice([True, False])
                }
            }
            
            entities.append(entity)
        
        return entities
    
    def _determine_access_level(self, role: str, department: str) -> int:
        """
        Determine access level based on role and department
        """
        base_level = 1
        
        # Role-based adjustments
        if role in ["Director", "Executive"]:
            base_level += 3
        elif role in ["Manager", "Administrator"]:
            base_level += 2
        elif role in ["Developer", "Analyst"]:
            base_level += 1
        
        # Department-based adjustments
        if department in ["IT", "Finance", "Legal"]:
            base_level += 1
        
        return min(base_level, 5)  # Cap at level 5
    
    def generate_entity_data(self, entity_id: str, days: int = 7) -> pd.DataFrame:
        """
        Generate behavioral data for a specific entity over specified days
        """
        data = []
        
        # Determine risk profile based on entity characteristics
        risk_profile = self._determine_entity_risk_profile(entity_id)
        
        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            
            # Generate daily metrics based on risk profile
            daily_data = self._generate_daily_metrics(entity_id, date, risk_profile)
            data.append(daily_data)
        
        return pd.DataFrame(data)
    
    def _determine_entity_risk_profile(self, entity_id: str) -> str:
        """
        Determine risk profile based on entity ID (for consistency)
        """
        # Use entity_id hash to consistently assign risk profiles
        hash_val = hash(entity_id) % 100
        
        if hash_val < 70:  # 70% low risk
            return "low_risk"
        elif hash_val < 90:  # 20% medium risk
            return "medium_risk"
        else:  # 10% high risk
            return "high_risk"
    
    def _generate_daily_metrics(self, entity_id: str, date: datetime, risk_profile: str) -> Dict:
        """
        Generate daily behavioral metrics for an entity
        """
        profile = self.risk_profiles[risk_profile]
        
        # Base metrics with some randomness
        failed_logins = random.randint(*profile["failed_logins_range"])
        data_accessed_gb = random.uniform(*profile["data_accessed_gb_range"])
        after_hours_activity = random.randint(*profile["after_hours_activity_range"])
        privilege_escalations = random.randint(*profile["privilege_escalations_range"])
        suspicious_file_access = random.randint(*profile["suspicious_file_access_range"])
        network_anomalies = random.randint(*profile["network_anomalies_range"])
        
        # Calculate derived metrics
        login_attempts = failed_logins + random.randint(10, 100)
        total_activity = after_hours_activity + random.randint(20, 80)
        avg_data_access_gb = data_accessed_gb * random.uniform(0.5, 1.5)
        
        # Add some weekend/weekday patterns
        if date.weekday() >= 5:  # Weekend
            after_hours_activity = int(after_hours_activity * 0.3)
            total_activity = int(total_activity * 0.4)
            login_attempts = int(login_attempts * 0.2)
        
        # Add time-based anomalies
        if random.random() < 0.1:  # 10% chance of anomaly
            failed_logins = int(failed_logins * random.uniform(2, 5))
            data_accessed_gb = data_accessed_gb * random.uniform(2, 4)
        
        return {
            "entity_id": entity_id,
            "timestamp": date.isoformat(),
            "login_attempts": login_attempts,
            "failed_logins": failed_logins,
            "data_accessed_gb": round(data_accessed_gb, 2),
            "avg_data_access_gb": round(avg_data_access_gb, 2),
            "after_hours_activity": after_hours_activity,
            "total_activity": total_activity,
            "privilege_escalations": privilege_escalations,
            "suspicious_file_access": suspicious_file_access,
            "network_anomalies": network_anomalies,
            "vpn_connections": random.randint(0, 10),
            "file_downloads": random.randint(0, 50),
            "email_attachments": random.randint(0, 20),
            "database_queries": random.randint(0, 100),
            "admin_commands": random.randint(0, 5),
            "location_changes": random.randint(0, 3),
            "device_count": random.randint(1, 5),
            "browser_anomalies": random.randint(0, 5)
        }
    
    def generate_training_data(self, size: int = 1000) -> pd.DataFrame:
        """
        Generate comprehensive training dataset
        """
        # Generate entities first
        entity_count = min(size // 10, 100)  # 10 days per entity, max 100 entities
        entities = self.generate_sample_entities(entity_count)
        
        all_data = []
        
        for entity in entities:
            entity_id = entity["entity_id"]
            
            # Generate 10 days of data per entity
            entity_data = self.generate_entity_data(entity_id, 10)
            
            # Add entity metadata to each row
            for _, row in entity_data.iterrows():
                row_dict = row.to_dict()
                row_dict.update({
                    "department": entity["department"],
                    "role": entity["role"],
                    "entity_type": entity["entity_type"],
                    "access_level": entity["access_level"]
                })
                all_data.append(row_dict)
        
        df = pd.DataFrame(all_data)
        
        # Shuffle the data
        df = df.sample(frac=1).reset_index(drop=True)
        
        return df
    
    def generate_risk_labels(self, training_data: pd.DataFrame) -> pd.Series:
        """
        Generate risk labels for training data based on behavioral patterns
        """
        labels = []
        
        for _, row in training_data.iterrows():
            # Calculate risk score based on multiple factors
            risk_score = 0
            
            # Login failure risk
            if row['failed_logins'] > 10:
                risk_score += 3
            elif row['failed_logins'] > 5:
                risk_score += 2
            elif row['failed_logins'] > 2:
                risk_score += 1
            
            # Data access risk
            if row['data_accessed_gb'] > 200:
                risk_score += 3
            elif row['data_accessed_gb'] > 100:
                risk_score += 2
            elif row['data_accessed_gb'] > 50:
                risk_score += 1
            
            # After hours activity risk
            if row['after_hours_activity'] > 30:
                risk_score += 3
            elif row['after_hours_activity'] > 15:
                risk_score += 2
            elif row['after_hours_activity'] > 5:
                risk_score += 1
            
            # Privilege escalation risk
            if row['privilege_escalations'] > 5:
                risk_score += 4
            elif row['privilege_escalations'] > 2:
                risk_score += 3
            elif row['privilege_escalations'] > 0:
                risk_score += 2
            
            # Suspicious file access risk
            if row['suspicious_file_access'] > 15:
                risk_score += 3
            elif row['suspicious_file_access'] > 8:
                risk_score += 2
            elif row['suspicious_file_access'] > 3:
                risk_score += 1
            
            # Network anomalies risk
            if row['network_anomalies'] > 20:
                risk_score += 3
            elif row['network_anomalies'] > 10:
                risk_score += 2
            elif row['network_anomalies'] > 5:
                risk_score += 1
            
            # Convert to binary classification (0 = low risk, 1 = high risk)
            label = 1 if risk_score >= 8 else 0
            labels.append(label)
        
        return pd.Series(labels)
    
    def generate_time_series_data(self, entity_id: str, days: int = 30) -> pd.DataFrame:
        """
        Generate time series data for trend analysis
        """
        data = []
        risk_profile = self._determine_entity_risk_profile(entity_id)
        
        # Add gradual trends
        trend_factor = random.uniform(0.8, 1.2)  # Overall trend multiplier
        
        for day in range(days):
            date = datetime.now() - timedelta(days=days - day - 1)
            
            # Progressive risk increase/decrease
            day_multiplier = 1 + (trend_factor - 1) * (day / days)
            
            daily_data = self._generate_daily_metrics(entity_id, date, risk_profile)
            
            # Apply trend to key metrics
            daily_data['failed_logins'] = int(daily_data['failed_logins'] * day_multiplier)
            daily_data['data_accessed_gb'] = daily_data['data_accessed_gb'] * day_multiplier
            daily_data['privilege_escalations'] = int(daily_data['privilege_escalations'] * day_multiplier)
            
            data.append(daily_data)
        
        return pd.DataFrame(data)
    
    def generate_anomaly_scenarios(self) -> List[Dict]:
        """
        Generate specific anomaly scenarios for testing
        """
        scenarios = [
            {
                "name": "Insider Data Theft",
                "description": "Employee accessing unusual amounts of data",
                "entity_id": "ANOMALY_001",
                "modifications": {
                    "data_accessed_gb": 500,
                    "after_hours_activity": 40,
                    "suspicious_file_access": 25,
                    "file_downloads": 200
                }
            },
            {
                "name": "Credential Compromise",
                "description": "Account with multiple failed login attempts",
                "entity_id": "ANOMALY_002",
                "modifications": {
                    "failed_logins": 30,
                    "location_changes": 10,
                    "device_count": 8,
                    "login_attempts": 45
                }
            },
            {
                "name": "Privilege Abuse",
                "description": "User escalating privileges repeatedly",
                "entity_id": "ANOMALY_003",
                "modifications": {
                    "privilege_escalations": 15,
                    "admin_commands": 25,
                    "database_queries": 300,
                    "network_anomalies": 20
                }
            },
            {
                "name": "After-Hours Suspicious Activity",
                "description": "Unusual activity during off-hours",
                "entity_id": "ANOMALY_004",
                "modifications": {
                    "after_hours_activity": 60,
                    "vpn_connections": 15,
                    "data_accessed_gb": 200,
                    "suspicious_file_access": 30
                }
            }
        ]
        
        return scenarios
    
    def apply_anomaly_scenario(self, scenario: Dict, base_data: Dict) -> Dict:
        """
        Apply anomaly scenario modifications to base data
        """
        modified_data = base_data.copy()
        
        for key, value in scenario["modifications"].items():
            if key in modified_data:
                modified_data[key] = value
        
        return modified_data