# Learner Graph RAG System

A comprehensive **Recommendation Algorithm/Graph (RAG)** system designed to boost learner engagement through personalized learning recommendations, mastery tracking, and gamified streak goals.

## 🚀 Features

- **ML-Powered Recommendation Engine**: Collaborative filtering + content-based algorithms
- **Real-time Learning Analytics**: Track mastery levels, learning gaps, and progress
- **A/B Testing Framework**: Statistical experimentation for algorithm optimization  
- **High Performance**: <100ms P99 recommendation latency target
- **Gamification**: Streak tracking and personalized goal setting
- **Explainable AI**: "Why Genie recommended this" explanations
- **Success Metrics**: Target +15% practice minute boost within 7 days

## 🏗️ Architecture

```
├── app/
│   ├── core/           # Configuration, database, exceptions
│   ├── models/         # SQLAlchemy models (User, Concept, Question, etc.)
│   ├── repository/     # Database access layer
│   ├── services/       # Business logic (RecommendationEngine, A/B Testing)
│   ├── schemas/        # Pydantic schemas for API
│   ├── routes/         # FastAPI route handlers
│   └── main.py         # Application entry point
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: SQLite (designed for Neo4j/Neptune migration)
- **Caching**: Redis
- **ML/Analytics**: NumPy, Pandas, Scikit-learn
- **API**: RESTful with OpenAPI documentation
- **Testing**: Pytest with async support

## 📊 Database Schema

### Core Models
- **User**: Learner profiles with A/B test group assignments
- **Concept**: Learning topics with prerequisite relationships
- **Question**: Practice items with difficulty levels
- **LearningSession**: Practice logs and interaction data
- **MasteryLevel**: Concept understanding over time
- **Streak**: Gamification and habit tracking
- **Recommendation**: Generated suggestions with explainability
- **ABTestExperiment**: A/B testing experiment definitions

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd learner_graph

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m app.main
```

### API Documentation

Start the server and visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🎯 Key API Endpoints

### Recommendations
```http
POST /api/v1/recommendations/generate
GET  /api/v1/recommendations/active/{user_id}
POST /api/v1/recommendations/feedback
GET  /api/v1/recommendations/explanation/{recommendation_id}
```

### Users & Analytics
```http
POST /api/v1/users/
GET  /api/v1/users/{user_id}/stats
GET  /api/v1/users/{user_id}/progress
GET  /api/v1/users/{user_id}/learning-profile
```

### System Monitoring
```http
GET  /api/v1/metrics/system
GET  /api/v1/experiments/active
```

## 🧠 Recommendation Engine

The RAG system uses a hybrid approach:

### 1. **Next Best Questions** (40% of recommendations)
- Zone of proximal development optimization
- Difficulty adaptation based on mastery levels
- Learning objective alignment

### 2. **Concept Review** (30% of recommendations) 
- Forgetting curve analysis
- Temporal learning gap detection
- Spaced repetition scheduling

### 3. **Streak Goals** (30% of recommendations)
- Personalized habit formation targets
- Gamification with milestone rewards
- Consistency score optimization

### Algorithm Features
- **Collaborative Filtering**: Learn from similar user patterns
- **Content-Based**: Match user preferences to item characteristics
- **Context-Aware**: Consider time, device, session history
- **Multi-Objective**: Balance engagement, mastery, and retention

## 🔬 A/B Testing Framework

### Features
- **Consistent User Assignment**: Hash-based stable group allocation
- **Statistical Significance**: Automated p-value calculation
- **Effect Size Measurement**: Cohen's d for practical significance
- **Multiple Metrics**: Practice minutes, retention rate, mastery gains

### Example Experiment
```python
ab_testing_service.create_experiment(
    name="recommendation_algorithm_test",
    hypothesis="Collaborative filtering increases practice time vs content-based",
    control_algorithm="content_based_v1",
    treatment_algorithm="collaborative_filtering_v2", 
    primary_metric="practice_minutes",
    target_improvement=15.0,  # 15% improvement target
    duration_days=30
)
```

## 📈 Performance Targets & Metrics

### Latency Requirements
- **P99 Recommendation Latency**: <100ms
- **API Response Time**: <50ms average
- **Database Queries**: <10ms P95

### Success Metrics
- **Practice Boost**: +15% practice minutes within 7 days
- **Retention Impact**: Track WAU/MAU improvements
- **Engagement**: Click-through rate >25%
- **System Uptime**: 99.9% availability

### Key Performance Indicators
```python
{
    "recommendation_engine": {
        "avg_latency_ms": 45,
        "p99_latency_ms": 89,
        "cache_hit_rate": 0.85,
        "recommendations_generated_today": 1247
    },
    "learning_analytics": {
        "total_active_learners": 1423,
        "avg_practice_minutes_per_user": 23.5,
        "concepts_mastered_today": 89,
        "streak_maintenance_rate": 0.67
    }
}
```

## 🔍 Explainable AI

The system provides transparent recommendation explanations:

### Explanation Types
- **Simple**: High-level reasoning for general users
- **Detailed**: Feature importance and user factors
- **Technical**: Algorithm specifics for developers

### Example Explanation
```json
{
    "main_reasons": [
        "Based on your current mastery levels",
        "Optimized for your learning style", 
        "Aligned with your practice goals"
    ],
    "feature_importance": {
        "mastery_gap": 0.4,
        "difficulty_match": 0.3,
        "temporal_spacing": 0.2,
        "user_preference": 0.1
    },
    "confidence_factors": {
        "algorithm_confidence": 0.85,
        "data_quality": 0.90,
        "personalization_strength": 0.75
    }
}
```

## 📊 Data Pipeline Architecture

### Real-time Processing
- **Practice Logs**: Immediate mastery level updates
- **Interaction Events**: Click-through and engagement tracking
- **Streak Updates**: Real-time habit formation monitoring

### Batch Processing
- **Daily Analytics**: User progress reports and insights
- **Weekly Summaries**: Learning path recommendations
- **A/B Test Analysis**: Statistical significance calculations


## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///./learner_graph.db

# Redis
REDIS_URL=redis://localhost:6379

# A/B Testing
AB_TEST_ENABLED=true
DEFAULT_AB_SPLIT=0.5

# Performance Targets
RECOMMENDATION_LATENCY_P99_MS=100
TARGET_PRACTICE_BOOST_PERCENT=15.0
```

## 🚀 Deployment

### Production Considerations
- **Database**: Migrate to Neo4j or Amazon Neptune for graph operations
- **Caching**: Redis Cluster for high availability
- **Monitoring**: Prometheus + Grafana for metrics
- **Logging**: Structured logging with correlation IDs

## 📚 Future Enhancements

### Graph Database Migration
- **Neo4j Integration**: Enhanced concept relationship modeling
- **Graph Algorithms**: PageRank for concept importance
- **Knowledge Graph**: Semantic understanding of learning paths

### Advanced ML Features
- **Deep Learning**: Neural collaborative filtering
- **Transfer Learning**: Cross-domain knowledge transfer
- **Reinforcement Learning**: Dynamic difficulty adjustment

### Platform Extensions
- **Mobile SDK**: React Native recommendation components
- **Browser Extension**: Context-aware learning suggestions
- **API Gateway**: Multi-tenant support and rate limiting


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

