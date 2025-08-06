# Cybersecurity Risk Scoring System

A comprehensive insider threat detection and risk assessment platform using advanced machine learning techniques to identify and score potential security risks within an organization.

## 🛡️ Overview

This system provides dynamic, data-driven risk scoring for entities (users, service accounts, contractors) within an organization. It combines machine learning models with rule-based pattern detection to identify potential insider threats and provide actionable security recommendations.

## ✨ Key Features

- **Dynamic Risk Scoring**: ML-powered risk assessment with scores from 5-50
- **Ensemble Models**: Combines Isolation Forest and Random Forest for accurate anomaly detection
- **Pattern Detection**: Rule-based system to identify suspicious behavior patterns
- **Actionable Recommendations**: Automated security improvement suggestions
- **Real-time Dashboard**: Interactive visualizations and monitoring capabilities
- **Entity Management**: Comprehensive user and entity profile management
- **Granular Analysis**: Detailed breakdown of risk factors and contributing elements

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **ML Models**: Isolation Forest + Random Forest ensemble
- **Entity Management**: SQLite database for entity profiles and risk history
- **Pattern Detection**: Configurable rule engine
- **Recommendation Engine**: Context-aware security recommendations
- **API Layer**: RESTful APIs for frontend integration

### Frontend (React.js)
- **Dashboard**: Risk overview with charts and statistics
- **Risk Assessment**: Interactive risk analysis tools
- **Entity Profiles**: Detailed entity information and history
- **Security Rules**: Rule management interface
- **Responsive Design**: Modern UI with Ant Design components

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Install Python dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Start the API server**:
```bash
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

### Frontend Setup

1. **Install Node.js dependencies**:
```bash
cd frontend
npm install
```

2. **Start the React development server**:
```bash
npm start
```

The frontend will be available at: http://localhost:3000

## 📊 Usage Guide

### 1. Initialize Sample Data
- Click "Initialize Sample Data" in the dashboard to generate 50 sample entities
- This creates realistic user profiles with departments, roles, and behavioral data

### 2. Train the Model
- Click "Train Model" to train the ML ensemble on sample data
- The model uses both supervised and unsupervised learning techniques

### 3. Assess Risk
- Navigate to "Risk Assessment" page
- Select entities for analysis
- Run assessment to get real-time risk scores and recommendations

### 4. Configure Security Rules
- Use "Security Rules" page to create custom detection patterns
- Define thresholds for various behavioral metrics
- Enable/disable rules as needed

### 5. Monitor Entities
- View individual entity profiles with historical risk data
- Track risk trends and implement recommendations

## 🔧 Configuration

### Security Rules
Configure detection rules in the Security Rules interface:

```json
{
  "rule_id": "high_login_failures",
  "rule_name": "High Login Failures",
  "rule_type": "authentication",
  "conditions": [
    {
      "field": "failed_logins",
      "operator": "gt",
      "value": 5
    }
  ],
  "weight": 2.0,
  "enabled": true
}
```

### Risk Scoring Parameters
- **Score Range**: 5-50 (low to critical risk)
- **Risk Levels**: Low (5-15), Medium (15-25), High (25-35), Critical (35-50)
- **Model Weights**: Isolation Forest (60%) + Random Forest (40%)

## 📈 Risk Factors

The system analyzes various behavioral metrics:

### Authentication
- Failed login attempts
- Login failure rate
- Multi-location access patterns

### Data Access
- Data volume accessed (GB)
- Suspicious file access patterns
- Database query anomalies

### Temporal Patterns
- After-hours activity
- Weekend access patterns
- Time-based anomalies

### Privilege Usage
- Privilege escalation attempts
- Administrative command usage
- Access level violations

### Network Behavior
- VPN connection patterns
- Network anomaly detection
- Device usage patterns

## 🛠️ API Endpoints

### Core Endpoints
- `GET /` - Health check
- `GET /api/entities` - List all entities
- `POST /api/entities` - Create new entity
- `GET /api/entities/{entity_id}` - Get entity profile
- `POST /api/assess-risk` - Run risk assessment
- `POST /api/train-model` - Train ML model
- `GET /api/dashboard-stats` - Dashboard statistics
- `POST /api/security-rules` - Create security rule
- `POST /api/detect-patterns` - Run pattern detection

### Model Management
- `GET /api/model-info` - Get model status and info
- `POST /api/initialize-sample-data` - Generate sample data

## 🔍 Machine Learning Details

### Isolation Forest
- **Purpose**: Unsupervised anomaly detection
- **Parameters**: 100 estimators, 10% contamination
- **Usage**: Identifies outliers in behavioral patterns

### Random Forest
- **Purpose**: Supervised classification
- **Parameters**: 200 estimators, max depth 10
- **Usage**: Learns from labeled risk examples

### Feature Engineering
- Login failure rate calculation
- Data access anomaly ratios
- After-hours activity patterns
- Privilege risk scoring
- Temporal behavior analysis

## 📋 Entity Data Model

```json
{
  "entity_id": "USER_0001",
  "entity_type": "user",
  "department": "IT",
  "role": "Developer",
  "access_level": 3,
  "current_risk_score": 18.5,
  "risk_level": "Medium",
  "risk_trend": "stable",
  "metadata": {
    "hire_date": "2023-01-15",
    "security_clearance": "Standard",
    "training_completed": true
  }
}
```

## 🎯 Recommendation Types

### Authentication
- Enable Multi-Factor Authentication
- Strengthen password policies
- Implement session timeouts

### Access Control
- Privilege review and optimization
- Access restriction recommendations
- Role-based access improvements

### Monitoring
- Enhanced logging configuration
- Real-time alert setup
- Audit trail improvements

## 🔒 Security Considerations

- **Data Privacy**: No sensitive personal data stored
- **Access Control**: Implement authentication for production use
- **Audit Logging**: All risk assessments and changes logged
- **Model Security**: Regular model retraining and validation

## 🧪 Testing

### Sample Scenarios
The system includes predefined anomaly scenarios:
- Insider data theft simulation
- Credential compromise patterns
- Privilege abuse detection
- After-hours suspicious activity

### Model Validation
- Cross-validation on training data
- Anomaly detection accuracy metrics
- False positive/negative analysis

## 📦 Dependencies

### Backend
- FastAPI: Web framework
- scikit-learn: Machine learning
- pandas/numpy: Data processing
- SQLite: Database
- uvicorn: ASGI server

### Frontend
- React: UI framework
- Ant Design: Component library
- Recharts: Data visualization
- Axios: HTTP client
- React Router: Navigation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions or issues:
1. Check the API documentation at `/docs` when running the backend
2. Review the console logs for debugging information
3. Ensure all dependencies are installed correctly

## 🔮 Future Enhancements

- Integration with SIEM systems
- Advanced ML models (Deep Learning)
- Real-time data streaming
- Mobile application
- Multi-tenant support
- Cloud deployment templates

---

**Built with ❤️ for cybersecurity professionals**
