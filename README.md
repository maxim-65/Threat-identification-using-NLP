# Automated Emerging Cyber Threat Identification

## Overview
This is a Django-based NLP project that detects whether a social media or news-like text input indicates a cyber threat. It includes a remote user portal for prediction and a service provider dashboard for model training, analytics, and audit review.

## Problem Statement
Security teams need a fast way to identify threat-related text in large streams of posts, messages, or reports. Manual review is slow, inconsistent, and does not scale.

## Solution
The application converts text into numerical features, trains multiple machine learning models, and classifies incoming text as either `Cyber Threat Found` or `No Cyber Threat Found`. The service provider dashboard also tracks model accuracy, prediction history, and audit logs.

## Features
- User registration, login, profile view, and threat prediction
- Service provider dashboard with analytics and audit logs
- Training pipeline for uploaded CSV files
- Model comparison and accuracy charts
- Export/download support for prediction records
- Render deployment support with static files and Gunicorn

## Tech Stack
- Backend: Django 5.2.3, Python 3.10
- ML/NLP: pandas, NumPy, scikit-learn, joblib
- Vectorization: CountVectorizer
- Models: Multinomial Naive Bayes, Linear SVM, Logistic Regression, Extra Tree Classifier
- Deployment: Render, Gunicorn, WhiteNoise
- Database: SQLite

## Architecture

### System Architecture Overview
The application follows a **service-oriented architecture** that separates concerns into three distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     Django Views Layer                        │
│  (Remote_User/views.py, Service_Provider/views.py)          │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼────────┐  │  ┌─────────▼─────────┐  ┌─────────▼──────────┐
│  Analytics     │  │  │  Training         │  │  Audit             │
│  Service       │  │  │  Service          │  │  Service           │
│  (analytics.py)│  │  │  (training.py)    │  │  (audit.py)        │
└────────────────┘  │  └───────────────────┘  └────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼────────────▼────────────▼─┐
│     Django ORM / Database Layer     │
│  (SQLite, Models, Migrations)      │
└──────────────────────────────────┬┘
                                    │
                        ┌───────────▼┐
                        │  SQLite DB  │
                        └─────────────┘
```

### Layer Breakdown

#### 1. **Presentation Layer** (Views)
- `Remote_User/views.py`: Handles user registration, login, profile, and threat predictions
- `Service_Provider/views.py`: Dashboard views for analytics, training, and audit logs
- Uses templates for rendering HTML responses
- Each view is decorated with role-based access control (`@require_remote_user`, `@require_service_provider`)

#### 2. **Business Logic Layer** (Services)
Located in `apps/core/services/`:

- **AnalyticsService** (`analytics.py`)
  - Aggregates threat statistics and model performance metrics
  - Prepares chart data for dashboard visualization
  - Methods: `get_threat_statistics()`, `get_threat_ratio_data()`, `get_chart_data()`

- **TrainingService** (`training.py`)
  - Handles CSV upload validation and normalization
  - Trains all four ML models on provided dataset
  - Stores training results and accuracy metrics to database
  - Methods: `load_dataset()`, `train_models()`, `store_training_results()`

- **AuditService** (`audit.py`)
  - Filters prediction audit logs with composable query filters
  - Provides trend analysis and user-based reporting
  - Methods: `apply_date_range_filter()`, `get_filtered_audit_log()`, `get_trend_by_date()`

#### 3. **Data Access Layer** (Models & ORM)
- Uses Django ORM for database operations
- Models: `RemoteUserProfile`, `ClientPostsModel`, `PredictionAudit`, `DetectionRatio`, `DetectionAccuracy`
- All queries are parameterized and safe from SQL injection

#### 4. **Utilities**
- `utils/decorators.py`: Session-based access control and error handling
- `utils/context_processors.py`: Shared template context (current year, app name, user role)

### Data Flow

```
User Request
     ↓
Django URL Router
     ↓
View Function (role-checked)
     ↓
Service Class (business logic)
     ↓
Django ORM
     ↓
SQLite Database
     ↓
Response (JSON or HTML)
```

## Project Structure
- `apps/Remote_User/` - user-facing views, models, registration, prediction logic
- `apps/Service_Provider/` - admin/service provider views, analytics, training, downloads
- `apps/core/` - shared Python services and utilities
- `templates/RUser/` - user templates
- `templates/SProvider/` - service provider templates
- `templates/base.html` - shared base layout
- `templates/analytics_chart.html` - consolidated analytics page
- `templates/model_training.html` - consolidated training page
- `data/Datasets.csv` - bundled training dataset
- `static/` - images and static assets

## Dataset Details
- Source: bundled project CSV file (`data/Datasets.csv`)
- Size: 3,280 rows
- Type: structured text dataset
- Key columns: `fid`, `tweet_text`, `timestamp`, `source`, `symbols`, `company_names`, `url`, `source_ip`, `protocol`, `dest_ip`, `Label`

## Data Preprocessing
- Text is converted to numeric features with `CountVectorizer`
- Labels are normalized into threat / no-threat classes
- Timestamp values are parsed for prediction history and dashboard metrics
- Training CSV uploads are validated to ensure required columns exist

## Feature Engineering
- Bag-of-words representation using `CountVectorizer`
- Classification-ready feature matrices built from `tweet_text`

## Model Details
Algorithms used:
- Multinomial Naive Bayes
- Linear SVM
- Logistic Regression
- Extra Tree Classifier

Why these models:
- They are strong baseline classifiers for text classification
- They provide a good comparison of speed, interpretability, and accuracy

## Training Process
- Dataset is split into train and test sets
- Multiple classifiers are trained on the same feature set
- Results are stored in the database for dashboard display
- Prediction cache is refreshed when the service provider requests it

## Evaluation Metrics
- Accuracy
- Model comparison on the dashboard
- Prediction counts and audit statistics

## Current Results
Current saved model scores in the application database:

| Model | Accuracy |
| --- | --- |
| Naive Bayes | 77.00% |
| Linear SVM | 76.84% |
| Logistic Regression | 79.34% |
| Extra Tree Classifier | 75.12% |

Prediction summary currently stored:
- Total predictions: 28
- Cyber Threat Found: 24
- No Cyber Threat Found: 4

## Insights
- Logistic Regression is currently the best saved model in the project database.
- The dataset is moderately imbalanced toward threat-labeled examples.
- CountVectorizer provides a simple and effective baseline for this text classification task.

## Limitations
- The project uses a single bundled CSV dataset, so model quality depends on that data.
- CountVectorizer does not capture semantic context like modern embeddings.
- SQLite is suitable for development and small deployments, but not ideal for large-scale production use.

## Deployment
- Platform: Render
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn config.wsgi:application`
- Static files are served with WhiteNoise

## Installation
1. Create a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Collect static files if needed:
   ```bash
   python manage.py collectstatic --noinput
   ```

## How to Run
```bash
python manage.py runserver
```

Open the app in your browser, then use:
- Remote user login / registration for predictions
- Service provider login for analytics and training

## Testing
```bash
python manage.py check
python manage.py migrate
```

## Security and Ethics
- User input should be validated before prediction.
- Prediction outputs should be treated as decision support, not final security verdicts.
- Real-world deployments should review privacy, bias, and access-control concerns.

## Future Improvements
- Replace CountVectorizer with embeddings or TF-IDF comparisons
- Add precision, recall, F1-score, and confusion matrix reporting
- Move from SQLite to PostgreSQL for production-scale usage
- Add automated tests for model and view behavior

## API Endpoints

### Remote User Routes
| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Home page |
| `/login/` | GET, POST | User login |
| `/register/` | GET, POST | User registration |
| `/logout/` | GET | User logout |
| `/profile/` | GET | View user profile |
| `/predict/` | POST | Submit text for threat prediction |
| `/add_dataset_details/` | GET, POST | Upload custom dataset |

### Service Provider Routes
| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/serviceproviderlogin/` | GET, POST | Service provider login |
| `/service_provider_home/` | GET | Dashboard home |
| `/train_model/` | POST | Train model with uploaded CSV |
| `/train_models/` | POST | Train all four models |
| `/charts/` | GET | Threat statistics chart |
| `/charts1/<chart_type>/` | GET | Performance metrics chart |
| `/likeschart/<chart_type>/` | GET | Model comparison chart |
| `/view_prediction_audit_log/` | GET, POST | View filtered audit logs |
| `/view_user_prediction_history/<username>/` | GET | View specific user's predictions |
| `/Download_Predicted_DataSets/` | GET | Download prediction records as CSV |
| `/download_prediction_audit_log/` | GET | Download audit log as CSV |

## Database Schema

### Key Tables

**users_remoteuser**
- `id` - Primary key
- `username` - Unique username
- `email` - User email
- `password_hash` - Hashed password
- `created_at` - Timestamp

**prediction_audit**
- `id` - Primary key
- `username` - Predicting user
- `text_input` - Input text for prediction
- `prediction` - Model output (threat/no threat)
- `confidence` - Prediction confidence score
- `timestamp` - Prediction time
- `model_used` - Which model made prediction

**detection_accuracy**
- `id` - Primary key
- `model_name` - Name of trained model
- `accuracy` - Accuracy percentage
- `timestamp` - Training time

**detection_ratio**
- `id` - Primary key
- `threat_count` - Total threats detected
- `no_threat_count` - Total non-threats
- `timestamp` - Calculation time

## Dependencies and Requirements

### Core Python Packages
```
Django==5.2.3              # Web framework
scikit-learn==1.3.2        # Machine learning library
pandas>=1.5.0              # Data manipulation
numpy>=1.24.0              # Numerical computing
python-decouple>=3.8       # Environment variables
joblib>=1.3.0              # Model serialization
psycopg2-binary>=2.9.0     # PostgreSQL adapter
gunicorn>=21.0             # Production WSGI server
whitenoise>=6.5.0          # Static file serving
```

For full requirements, see `requirements.txt`.

### System Requirements
- Python 3.10+
- pip (Python package manager)
- Virtual environment (recommended: `venv`)
- 200MB disk space (code + models)

## Configuration

### Environment Variables
Create a `.env` file in the project root:
```
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
DATABASE_URL=sqlite:////path/to/db.sqlite3
```

### Django Settings
- Settings file: `config/settings.py`
- Default database: SQLite (`db.sqlite3`)
- Default port: 8000
- Default host: 127.0.0.1

### Static Files
- Location: `static/`
- Served by: WhiteNoise (in production)
- Collect command: `python manage.py collectstatic`

## Troubleshooting

### Issue: "ModuleNotFoundError" when running server
**Solution**: Ensure virtual environment is activated and all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: Database migrations haven't been applied
**Solution**: Run migrations:
```bash
python manage.py migrate
```

### Issue: Static files not loading in production
**Solution**: Collect static files:
```bash
python manage.py collectstatic --noinput
```

### Issue: Service provider login returns 403 error
**Solution**: Verify user role is set to "service_provider" in the database or login with correct credentials.

### Issue: Model predictions are not stored in the database
**Solution**: Ensure `prediction_audit` table exists. Run `python manage.py migrate` to create it.

### Issue: Training fails with "Column not found" error
**Solution**: Verify uploaded CSV has these columns: `fid`, `tweet_text`, `Label`. See Dataset Details section for format.

## Performance Considerations

- **Text Vectorization**: CountVectorizer can be slow on large datasets (>100k rows). Consider TF-IDF or embeddings for optimization.
- **Database Queries**: Add indices on frequently filtered columns (`username`, `timestamp`) to improve query speed.
- **Model Training**: Training all four models takes ~5-10 seconds on typical hardware.
- **Concurrent Users**: SQLite supports limited concurrent access. Use PostgreSQL for production (>50 concurrent users).
- **Batch Predictions**: For high-volume predictions, consider async task queues (Celery) instead of synchronous views.

## Database Migration Guide

### Creating a New Migration
```bash
python manage.py makemigrations
```

### Applying Migrations
```bash
python manage.py migrate
```

### Reversing a Migration
```bash
python manage.py migrate app_name MIGRATION_NUMBER
```

### Viewing Migration History
```bash
python manage.py showmigrations
```

## Project File Organization

```
cyber_threat_app/
├── apps/
│   ├── Remote_User/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── migrations/
│   ├── Service_Provider/
│   │   ├── models.py
│   │   ├── views.py
│   │   └── migrations/
│   └── core/
│       ├── services/
│       │   ├── analytics.py
│       │   ├── training.py
│       │   └── audit.py
│       └── utils/
│           ├── decorators.py
│           └── context_processors.py
├── templates/
│   ├── base.html
│   ├── analytics_chart.html
│   ├── model_training.html
│   ├── RUser/
│   └── SProvider/
├── static/
│   └── images/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── data/
│   └── Datasets.csv
├── db.sqlite3
├── manage.py
├── requirements.txt
└── README.md
```

## Future Improvements

## License
No explicit license file is included in the repository.
