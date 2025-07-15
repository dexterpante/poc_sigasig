# SIGASIG - Smart Intelligent Genetic Algorithm Scheduler for Institutional Governance

SIGASIG is an advanced class scheduling system that uses linear programming optimization to automatically generate optimal timetables for educational institutions. The system intelligently assigns teachers, rooms, and classes while respecting constraints such as teacher qualifications, room availability, and workload limits.

## Features

- **Intelligent Scheduling**: Uses PuLP linear programming to optimize class assignments
- **Multi-shift Support**: Supports full day, AM/PM, and AM/PM/Evening shifts
- **Teacher Qualification Matching**: Assigns classes based on teacher major/minor subjects
- **Constraint Management**: Handles room conflicts, teacher availability, and workload limits
- **REST API**: FastAPI-based backend with automatic OpenAPI documentation
- **Multiple Implementations**: FastAPI and Django versions available

## Project Structure

```
sigasig/
├── fastapi_scheduler/          # Complete FastAPI implementation with web UI
│   ├── main.py                # FastAPI app with full scheduling logic
│   ├── templates/             # Jinja2 templates for web interface
│   │   ├── base.html          # Base template with modern UI components
│   │   └── dashboard.html     # Interactive dashboard with KPIs
│   └── requirements.txt       # Python dependencies
├── streamlit_dashboard/        # Streamlit web application
│   ├── app.py                 # Comprehensive dashboard with data management
│   └── requirements.txt       # Streamlit dependencies
├── sigasig_django/            # Django implementation (in development)
│   └── scheduler/
│       ├── models.py          # Django models
│       ├── views.py           # Django views
│       ├── scheduler_engine.py # Scheduling algorithm
│       └── urls.py            # URL routing
└── sigasig_fastapi/           # Simplified FastAPI version
    └── main.py                # Basic FastAPI stub
```

## Setup and Run

### FastAPI Version (Recommended)

1. **Navigate to the FastAPI scheduler directory:**
   ```bash
   cd fastapi_scheduler
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI application:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the application:**
   - **Web Dashboard**: http://localhost:8000 (Modern UI with KPIs)
   - **API Documentation**: http://localhost:8000/docs (Interactive API docs)
   - **API Endpoints**: http://localhost:8000/api/ (REST API)

### Streamlit Dashboard (Alternative UI)

1. **Navigate to the Streamlit dashboard directory:**
   ```bash
   cd streamlit_dashboard
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit application:**
   ```bash
   streamlit run app.py
   ```

4. **Access the application:**
   - **Streamlit Dashboard**: http://localhost:8501

### Django Version (Under Development)

The Django implementation is currently incomplete and requires additional setup.

## API Usage

### Schedule Generation

Send a POST request to `/schedule/` with the following JSON structure:

```json
{
  "teachers": [
    {"id": "T001", "major": "Math", "minor": "Physics"}
  ],
  "rooms": [
    {"id": "R001", "capacity": 30}
  ],
  "classes": [
    {"id": "C001", "subject": "Math", "times_per_week": 3, "duration": 1}
  ],
  "max_per_day": 6,
  "max_per_week": 30,
  "num_shifts": 1
}
```

### Response Format

```json
{
  "schedule": [
    {
      "teacher": "T001",
      "class": "C001",
      "subject": "Math",
      "room": "R001",
      "day": "Mon",
      "period": "07:00-08:00",
      "occurrence": 1,
      "duration": 1
    }
  ]
}
```

## Current Status

### ✅ Completed Features
- Core scheduling algorithm with PuLP optimization
- FastAPI REST API with automatic documentation
- **Modern Web Dashboard** with interactive KPIs and charts
- **Streamlit Alternative Dashboard** with comprehensive data management
- Multi-shift scheduling support
- Teacher qualification system
- Constraint solving for conflicts and workload limits
- Pydantic data models for validation
- **Real-time anomaly detection** display
- **Teacher specialization mismatch tracking**

### 🚧 In Development
- Database integration with SQLite/PostgreSQL
- User authentication and role management
- Advanced schedule editor with drag-and-drop
- Real-time collaborative editing
- Mobile-responsive enhancements

### 📋 Planned Features
- User authentication and role management
- Real-time collaborative editing
- Calendar integration (Google Calendar, iCal)
- Mobile-responsive interface
- Advanced conflict resolution
- Teacher preference management

## KPI Dashboard - Teacher Specialization Mismatch Reduction

SIGASIG provides comprehensive Key Performance Indicators (KPIs) specifically designed to monitor and reduce teacher specialization mismatch, based on international best practices and ESF7 framework:

### 🎯 Core Specialization Mismatch Metrics

#### **Teacher Specialization Match Rate (TSMR)**
- **Target**: >85% of teachers teaching in their major specialization
- **Current Global Benchmark**: Philippines ~40% (need to improve to 85%+)
- **Calculation**: (Teachers in major subjects / Total teachers) × 100

#### **License Alignment Index (LAI)**
- **Target**: >90% alignment between teaching license and assigned subjects
- **Measurement**: Percentage of teachers with proper licensure for assigned subjects
- **Scoring**: Major+License=0, Minor/12+ units=1, No alignment=2

#### **Subject-Specific Mismatch Rate (SSMR)**
- **Critical Subjects**: Math, Science, English (highest mismatch impact)
- **Target**: <10% mismatch rate in core subjects
- **Tracking**: Individual subject mismatch percentages

#### **School Mismatch Intensity Score (SMIS)**
- **Range**: 0-2 (0=perfect match, 2=severe mismatch)
- **Weighted Score**: Considers subject criticality and teacher experience
- **Adjustment Factors**: NEAP training (-1), 5+ years experience (-0.5)

### 📊 Specialization Optimization Metrics

#### **Deployment Efficiency Ratio (DER)**
- **Target**: >80% of specialists deployed in their subject area
- **Measurement**: Percentage of subject specialists teaching their specialty
- **Impact**: Directly correlates with student learning outcomes

#### **Out-of-Field Assignment Rate**
- **Benchmark**: Philippines currently 60%+ (target <20%)
- **Critical Tracking**: High-stakes subjects (Math, Science, English)
- **Intervention Trigger**: >30% in any subject area

#### **Professional Development Alignment**
- **CPD Match Rate**: Training aligned with teaching assignments
- **INSET Effectiveness**: Post-training assignment optimization
- **Upskilling ROI**: Improved match rates after professional development

### ⏰ Workload Management & Overtime Tracking

#### **Teacher Overload Detection**
- **Policy Compliance**: Adherence to DO 31 s.2012 maximum teaching load limits
- **Overload Rate**: Percentage of teachers exceeding standard workload
- **Critical Threshold**: Teachers with >30 hours/week teaching load
- **Overload Distribution**: Workload equity across faculty members

#### **Overtime Hours Monitoring**
- **Weekly Overtime**: Hours beyond standard teaching load per teacher
- **Monthly Overtime Accumulation**: Cumulative overtime tracking
- **Overtime by Subject**: Identification of subjects causing excessive workload
- **Overtime Cost Impact**: Financial implications of overload assignments

#### **Workload Equity Index**
- **Load Distribution Fairness**: Standard deviation of teaching hours across teachers
- **Balanced Assignment Rate**: Percentage of teachers within normal load range
- **Underload Identification**: Teachers with insufficient teaching assignments
- **Optimal Load Achievement**: Teachers meeting ideal workload targets (18-24 hours)

#### **Stress & Burnout Indicators**
- **Consecutive Period Overload**: Teachers with back-to-back classes beyond limits
- **Subject Overload**: Teachers handling >3 different subjects simultaneously
- **Preparation Time Deficit**: Insufficient planning periods relative to teaching load
- **Advisory Load Balance**: Additional responsibilities beyond teaching hours

### � Anomaly Detection KPIs

#### **Gaming Detection Metrics**
- **Low-enrollment Gaming**: Sections <15 students with full teaching load
- **Ghost Subjects**: Subjects not in MELC curriculum
- **Advisory Overuse**: Teachers marked "advisory only" with zero load
- **Subject Rotation Gaming**: Yearly subject changes to preserve positions

#### **Resource Allocation Anomalies**
- **Duplicate Ancillary Roles**: Multiple teachers with same vague functions
- **Present-but-Idle**: Teachers present but no teaching/advisory load
- **Overload/Underload**: Violations of DO 31 s.2012 policies

### 📈 Impact Assessment Metrics

#### **Student Learning Outcome Correlation**
- **NAT Score Improvement**: Correlation with specialization match
- **Subject Performance**: Grade improvements in properly matched classes
- **Learning Gap Reduction**: Decreased achievement gaps in core subjects

#### **Teacher Satisfaction & Retention**
- **Job Satisfaction**: Correlation with subject-specialization match
- **Retention Rate**: Lower turnover in properly matched assignments
- **Career Development**: Promotion rates for specialized teachers

### 🌐 International Benchmarking

#### **Global Comparison Metrics**
- **Australia SiAS Survey**: Subject vs. training alignment
- **USA NCES SASS**: License vs. subject matching
- **Finland Model**: Weighted scoring including degree, minor, CPD, experience
- **WHO Health Model**: Skill mix mismatch adjusted by training & practice

#### **Best Practice Indicators**
- **Competency Equivalence**: German TVET model adaptation
- **Continuous Improvement**: Finnish professional development integration
- **Policy Compliance**: Australian mandatory qualification standards

## Technology Stack

- **Backend**: FastAPI, Django
- **Frontend**: Jinja2 Templates + Alpine.js + Tailwind CSS, Streamlit
- **Optimization**: PuLP (Linear Programming)
- **Data Validation**: Pydantic
- **Server**: Uvicorn
- **Database**: PostgreSQL/SQLite (planned)
- **Analytics**: Pandas, NumPy (for KPI calculations)
- **Visualization**: Chart.js, Plotly (for interactive charts)
- **Styling**: Tailwind CSS (utility-first CSS framework)
- **JavaScript**: Alpine.js (lightweight reactive framework)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
