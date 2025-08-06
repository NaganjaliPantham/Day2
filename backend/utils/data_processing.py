import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Advanced data processing utilities for the risk scoring system
    """
    
    def __init__(self):
        self.feature_columns = [
            'login_attempts', 'failed_logins', 'data_accessed_gb', 'avg_data_access_gb',
            'after_hours_activity', 'total_activity', 'privilege_escalations',
            'suspicious_file_access', 'network_anomalies', 'vpn_connections',
            'file_downloads', 'email_attachments', 'database_queries',
            'admin_commands', 'location_changes', 'device_count', 'browser_anomalies'
        ]
    
    def clean_and_validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate input data
        """
        try:
            cleaned_data = data.copy()
            
            # Remove duplicates
            cleaned_data = cleaned_data.drop_duplicates()
            
            # Handle missing values
            for col in self.feature_columns:
                if col in cleaned_data.columns:
                    # Fill missing numeric values with median
                    if cleaned_data[col].dtype in [np.int64, np.float64]:
                        cleaned_data[col] = cleaned_data[col].fillna(cleaned_data[col].median())
                    else:
                        cleaned_data[col] = cleaned_data[col].fillna(0)
            
            # Remove outliers using IQR method
            cleaned_data = self._remove_outliers(cleaned_data)
            
            # Validate data ranges
            cleaned_data = self._validate_data_ranges(cleaned_data)
            
            logger.info(f"Data cleaned: {len(data)} -> {len(cleaned_data)} rows")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Data cleaning failed: {str(e)}")
            return data
    
    def _remove_outliers(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Remove outliers using IQR method
        """
        cleaned_data = data.copy()
        
        for col in self.feature_columns:
            if col in cleaned_data.columns and cleaned_data[col].dtype in [np.int64, np.float64]:
                Q1 = cleaned_data[col].quantile(0.25)
                Q3 = cleaned_data[col].quantile(0.75)
                IQR = Q3 - Q1
                
                # Define outlier bounds
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR
                
                # Cap values instead of removing rows
                cleaned_data[col] = cleaned_data[col].clip(lower=lower_bound, upper=upper_bound)
        
        return cleaned_data
    
    def _validate_data_ranges(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and correct data ranges
        """
        validated_data = data.copy()
        
        # Ensure non-negative values for count-based metrics
        count_columns = [
            'login_attempts', 'failed_logins', 'after_hours_activity', 'total_activity',
            'privilege_escalations', 'suspicious_file_access', 'network_anomalies',
            'vpn_connections', 'file_downloads', 'email_attachments', 'database_queries',
            'admin_commands', 'location_changes', 'device_count', 'browser_anomalies'
        ]
        
        for col in count_columns:
            if col in validated_data.columns:
                validated_data[col] = validated_data[col].clip(lower=0)
        
        # Ensure data access values are non-negative
        if 'data_accessed_gb' in validated_data.columns:
            validated_data['data_accessed_gb'] = validated_data['data_accessed_gb'].clip(lower=0)
        
        if 'avg_data_access_gb' in validated_data.columns:
            validated_data['avg_data_access_gb'] = validated_data['avg_data_access_gb'].clip(lower=0)
        
        # Ensure failed logins <= login attempts
        if all(col in validated_data.columns for col in ['failed_logins', 'login_attempts']):
            validated_data['failed_logins'] = np.minimum(
                validated_data['failed_logins'], 
                validated_data['login_attempts']
            )
        
        # Ensure after hours activity <= total activity
        if all(col in validated_data.columns for col in ['after_hours_activity', 'total_activity']):
            validated_data['after_hours_activity'] = np.minimum(
                validated_data['after_hours_activity'], 
                validated_data['total_activity']
            )
        
        return validated_data
    
    def engineer_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create engineered features for better risk detection
        """
        try:
            feature_data = data.copy()
            
            # Calculate ratios and derived metrics
            if all(col in feature_data.columns for col in ['failed_logins', 'login_attempts']):
                feature_data['login_failure_rate'] = (
                    feature_data['failed_logins'] / 
                    (feature_data['login_attempts'] + 1)
                )
            
            if all(col in feature_data.columns for col in ['data_accessed_gb', 'avg_data_access_gb']):
                feature_data['data_access_anomaly'] = (
                    feature_data['data_accessed_gb'] / 
                    (feature_data['avg_data_access_gb'] + 1)
                )
            
            if all(col in feature_data.columns for col in ['after_hours_activity', 'total_activity']):
                feature_data['after_hours_ratio'] = (
                    feature_data['after_hours_activity'] / 
                    (feature_data['total_activity'] + 1)
                )
            
            # Create composite risk indicators
            if 'privilege_escalations' in feature_data.columns and 'admin_commands' in feature_data.columns:
                feature_data['privilege_risk_score'] = (
                    feature_data['privilege_escalations'] * 2 + 
                    feature_data['admin_commands']
                )
            
            if all(col in feature_data.columns for col in ['suspicious_file_access', 'file_downloads']):
                feature_data['file_access_risk'] = (
                    feature_data['suspicious_file_access'] * 3 + 
                    feature_data['file_downloads'] * 0.1
                )
            
            # Network behavior indicators
            if all(col in feature_data.columns for col in ['network_anomalies', 'vpn_connections']):
                feature_data['network_risk_score'] = (
                    feature_data['network_anomalies'] * 2 + 
                    feature_data['vpn_connections'] * 0.5
                )
            
            # Device and location anomalies
            if all(col in feature_data.columns for col in ['location_changes', 'device_count']):
                feature_data['mobility_risk'] = (
                    feature_data['location_changes'] * 2 + 
                    np.maximum(0, feature_data['device_count'] - 2)
                )
            
            # Time-based features if timestamp is available
            if 'timestamp' in feature_data.columns:
                feature_data = self._add_temporal_features(feature_data)
            
            logger.info(f"Feature engineering completed: {len(feature_data.columns)} features")
            return feature_data
            
        except Exception as e:
            logger.error(f"Feature engineering failed: {str(e)}")
            return data
    
    def _add_temporal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add temporal features based on timestamp
        """
        temporal_data = data.copy()
        
        try:
            # Convert timestamp to datetime
            temporal_data['timestamp'] = pd.to_datetime(temporal_data['timestamp'])
            
            # Extract temporal features
            temporal_data['hour_of_day'] = temporal_data['timestamp'].dt.hour
            temporal_data['day_of_week'] = temporal_data['timestamp'].dt.dayofweek
            temporal_data['is_weekend'] = temporal_data['day_of_week'].isin([5, 6]).astype(int)
            temporal_data['is_business_hours'] = (
                (temporal_data['hour_of_day'] >= 9) & 
                (temporal_data['hour_of_day'] <= 17) & 
                (temporal_data['is_weekend'] == 0)
            ).astype(int)
            
            # Risk indicators based on time
            temporal_data['off_hours_indicator'] = (1 - temporal_data['is_business_hours']).astype(int)
            
            return temporal_data
            
        except Exception as e:
            logger.error(f"Temporal feature extraction failed: {str(e)}")
            return data
    
    def aggregate_entity_data(self, data: pd.DataFrame, entity_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Aggregate data for a specific entity over a time period
        """
        try:
            entity_data = data[data['entity_id'] == entity_id].copy()
            
            if entity_data.empty:
                return {}
            
            # Sort by timestamp
            if 'timestamp' in entity_data.columns:
                entity_data['timestamp'] = pd.to_datetime(entity_data['timestamp'])
                entity_data = entity_data.sort_values('timestamp')
                
                # Filter to recent days
                cutoff_date = datetime.now() - timedelta(days=days)
                entity_data = entity_data[entity_data['timestamp'] >= cutoff_date]
            
            # Calculate aggregations
            aggregations = {}
            
            for col in self.feature_columns:
                if col in entity_data.columns:
                    aggregations[f'{col}_sum'] = entity_data[col].sum()
                    aggregations[f'{col}_mean'] = entity_data[col].mean()
                    aggregations[f'{col}_max'] = entity_data[col].max()
                    aggregations[f'{col}_std'] = entity_data[col].std()
                    aggregations[f'{col}_trend'] = self._calculate_trend(entity_data[col])
            
            # Add derived aggregations
            aggregations['total_records'] = len(entity_data)
            aggregations['date_range'] = (
                entity_data['timestamp'].max() - entity_data['timestamp'].min()
            ).days if 'timestamp' in entity_data.columns else days
            
            return aggregations
            
        except Exception as e:
            logger.error(f"Entity aggregation failed: {str(e)}")
            return {}
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """
        Calculate trend direction (-1 to 1)
        """
        if len(series) < 2:
            return 0
        
        # Simple linear trend calculation
        x = np.arange(len(series))
        y = series.values
        
        # Calculate correlation coefficient as trend indicator
        correlation = np.corrcoef(x, y)[0, 1]
        
        return correlation if not np.isnan(correlation) else 0
    
    def calculate_risk_velocity(self, risk_history: List[Dict]) -> Dict[str, float]:
        """
        Calculate risk velocity (rate of change)
        """
        try:
            if len(risk_history) < 2:
                return {"velocity": 0, "acceleration": 0}
            
            # Extract risk scores and timestamps
            scores = [r['risk_score'] for r in risk_history]
            timestamps = [datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')) for r in risk_history]
            
            # Sort by timestamp
            sorted_data = sorted(zip(timestamps, scores))
            timestamps, scores = zip(*sorted_data)
            
            # Calculate velocity (change per day)
            time_diffs = [(timestamps[i] - timestamps[i-1]).total_seconds() / 86400 for i in range(1, len(timestamps))]
            score_diffs = [scores[i] - scores[i-1] for i in range(1, len(scores))]
            
            velocities = [score_diffs[i] / max(time_diffs[i], 0.1) for i in range(len(time_diffs))]
            
            avg_velocity = np.mean(velocities) if velocities else 0
            
            # Calculate acceleration (change in velocity)
            if len(velocities) > 1:
                acceleration = np.mean([velocities[i] - velocities[i-1] for i in range(1, len(velocities))])
            else:
                acceleration = 0
            
            return {
                "velocity": float(avg_velocity),
                "acceleration": float(acceleration)
            }
            
        except Exception as e:
            logger.error(f"Risk velocity calculation failed: {str(e)}")
            return {"velocity": 0, "acceleration": 0}
    
    def detect_data_anomalies(self, data: pd.DataFrame) -> List[Dict]:
        """
        Detect anomalies in the input data
        """
        anomalies = []
        
        try:
            for col in self.feature_columns:
                if col in data.columns and data[col].dtype in [np.int64, np.float64]:
                    # Statistical anomaly detection
                    mean_val = data[col].mean()
                    std_val = data[col].std()
                    
                    # Find values beyond 3 standard deviations
                    anomaly_threshold = 3
                    anomalous_indices = data[
                        (data[col] > mean_val + anomaly_threshold * std_val) |
                        (data[col] < mean_val - anomaly_threshold * std_val)
                    ].index
                    
                    for idx in anomalous_indices:
                        anomalies.append({
                            "entity_id": data.loc[idx, 'entity_id'] if 'entity_id' in data.columns else 'unknown',
                            "feature": col,
                            "value": float(data.loc[idx, col]),
                            "mean": float(mean_val),
                            "std": float(std_val),
                            "z_score": float((data.loc[idx, col] - mean_val) / std_val),
                            "timestamp": data.loc[idx, 'timestamp'] if 'timestamp' in data.columns else None
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return []
    
    def create_data_quality_report(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report
        """
        try:
            report = {
                "total_records": len(data),
                "total_features": len(data.columns),
                "missing_values": {},
                "data_types": {},
                "value_ranges": {},
                "duplicate_records": len(data) - len(data.drop_duplicates()),
                "anomalies_detected": len(self.detect_data_anomalies(data))
            }
            
            # Missing values analysis
            for col in data.columns:
                missing_count = data[col].isnull().sum()
                missing_pct = (missing_count / len(data)) * 100
                report["missing_values"][col] = {
                    "count": int(missing_count),
                    "percentage": float(missing_pct)
                }
            
            # Data types
            for col in data.columns:
                report["data_types"][col] = str(data[col].dtype)
            
            # Value ranges for numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                report["value_ranges"][col] = {
                    "min": float(data[col].min()),
                    "max": float(data[col].max()),
                    "mean": float(data[col].mean()),
                    "std": float(data[col].std())
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Data quality report failed: {str(e)}")
            return {"error": str(e)}