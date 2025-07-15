import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure Streamlit page
st.set_page_config(
    page_title="SIGASIG - Class Scheduler Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .kpi-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    .success-metric {
        color: #28a745;
        font-weight: bold;
    }
    .warning-metric {
        color: #ffc107;
        font-weight: bold;
    }
    .danger-metric {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'teachers' not in st.session_state:
    st.session_state.teachers = []
if 'rooms' not in st.session_state:
    st.session_state.rooms = []
if 'classes' not in st.session_state:
    st.session_state.classes = []
if 'schedule' not in st.session_state:
    st.session_state.schedule = []

def load_sample_data():
    """Load comprehensive sample data for testing"""
    
    # Sample Teachers Data - Reduced to 15 for better performance
    sample_teachers = [
        # Mathematics Department
        {"id": "T001", "name": "Dr. Maria Santos", "major": "Mathematics", "minor": "Physics", "experience": 15, "status": "active"},
        {"id": "T002", "name": "Prof. Juan Dela Cruz", "major": "Mathematics", "minor": "Statistics", "experience": 12, "status": "active"},
        {"id": "T003", "name": "Ms. Ana Reyes", "major": "Mathematics", "minor": "Computer Science", "experience": 8, "status": "active"},
        
        # Science Department
        {"id": "T004", "name": "Dr. Carlos Mendoza", "major": "Physics", "minor": "Mathematics", "experience": 18, "status": "active"},
        {"id": "T005", "name": "Prof. Lisa Garcia", "major": "Chemistry", "minor": "Biology", "experience": 14, "status": "active"},
        {"id": "T006", "name": "Ms. Rosa Fernandez", "major": "Biology", "minor": "Health Science", "experience": 10, "status": "active"},
        
        # Language Arts Department
        {"id": "T007", "name": "Prof. Isabel Torres", "major": "English", "minor": "Literature", "experience": 16, "status": "active"},
        {"id": "T008", "name": "Ms. Carmen Valdez", "major": "English", "minor": "Creative Writing", "experience": 11, "status": "active"},
        {"id": "T009", "name": "Mr. Diego Ramos", "major": "Filipino", "minor": "History", "experience": 13, "status": "active"},
        
        # Social Studies Department
        {"id": "T010", "name": "Prof. Miguel Herrera", "major": "History", "minor": "Geography", "experience": 19, "status": "active"},
        {"id": "T011", "name": "Ms. Patricia Jimenez", "major": "Geography", "minor": "Economics", "experience": 12, "status": "active"},
        {"id": "T012", "name": "Mr. Francisco Gutierrez", "major": "Economics", "minor": "Business Studies", "experience": 14, "status": "active"},
        
        # Technology & Arts Department
        {"id": "T013", "name": "Mr. Antonio Lopez", "major": "Computer Science", "minor": "Mathematics", "experience": 10, "status": "active"},
        {"id": "T014", "name": "Prof. Ricardo Vargas", "major": "Arts", "minor": "Music", "experience": 20, "status": "active"},
        {"id": "T015", "name": "Mr. Fernando Rojas", "major": "Physical Education", "minor": "Health Science", "experience": 11, "status": "active"}
    ]
    
    # Sample Rooms Data
    sample_rooms = [
        # Regular Classrooms
        {"id": "R001", "capacity": 35, "type": "Classroom", "building": "Main Building", "floor": 1, "equipment": "Projector, Whiteboard, AC"},
        {"id": "R002", "capacity": 30, "type": "Classroom", "building": "Main Building", "floor": 1, "equipment": "Smart Board, AC"},
        {"id": "R003", "capacity": 40, "type": "Classroom", "building": "Main Building", "floor": 2, "equipment": "Projector, Whiteboard"},
        {"id": "R004", "capacity": 32, "type": "Classroom", "building": "Main Building", "floor": 2, "equipment": "Smart Board, AC"},
        {"id": "R005", "capacity": 28, "type": "Classroom", "building": "East Wing", "floor": 1, "equipment": "Projector, Whiteboard"},
        {"id": "R006", "capacity": 36, "type": "Classroom", "building": "East Wing", "floor": 2, "equipment": "Smart Board, AC"},
        {"id": "R007", "capacity": 38, "type": "Classroom", "building": "West Wing", "floor": 1, "equipment": "Projector, Whiteboard, AC"},
        {"id": "R008", "capacity": 30, "type": "Classroom", "building": "West Wing", "floor": 2, "equipment": "Smart Board"},
        
        # Science Laboratories
        {"id": "R101", "capacity": 25, "type": "Laboratory", "building": "Science Building", "floor": 1, "equipment": "Lab Tables, Fume Hood, Safety Equipment"},
        {"id": "R102", "capacity": 24, "type": "Laboratory", "building": "Science Building", "floor": 1, "equipment": "Chemistry Lab Setup, Safety Shower"},
        {"id": "R103", "capacity": 20, "type": "Laboratory", "building": "Science Building", "floor": 2, "equipment": "Physics Lab Equipment, Oscilloscopes"},
        {"id": "R104", "capacity": 22, "type": "Laboratory", "building": "Science Building", "floor": 2, "equipment": "Biology Lab, Microscopes"},
        
        # Computer Labs
        {"id": "R201", "capacity": 30, "type": "Computer Lab", "building": "Technology Building", "floor": 1, "equipment": "30 PCs, Projector, Network"},
        {"id": "R202", "capacity": 28, "type": "Computer Lab", "building": "Technology Building", "floor": 2, "equipment": "28 PCs, Interactive Board"},
        {"id": "R203", "capacity": 32, "type": "Computer Lab", "building": "Technology Building", "floor": 3, "equipment": "32 PCs, Server Room Access"},
        
        # Specialized Rooms
        {"id": "R301", "capacity": 50, "type": "Library", "building": "Library Building", "floor": 1, "equipment": "Study Tables, Computers, WiFi"},
        {"id": "R302", "capacity": 45, "type": "Library", "building": "Library Building", "floor": 2, "equipment": "Reading Area, Silent Study"},
        {"id": "R401", "capacity": 40, "type": "Music Room", "building": "Arts Building", "floor": 1, "equipment": "Piano, Sound System, Instruments"},
        {"id": "R402", "capacity": 35, "type": "Art Room", "building": "Arts Building", "floor": 2, "equipment": "Art Supplies, Easels, Natural Light"},
        {"id": "R403", "capacity": 60, "type": "Gymnasium", "building": "Sports Complex", "floor": 1, "equipment": "Sports Equipment, Bleachers"},
        {"id": "R404", "capacity": 20, "type": "Counseling Room", "building": "Admin Building", "floor": 1, "equipment": "Comfortable Seating, Privacy"},
        
        # Large Venues
        {"id": "R501", "capacity": 100, "type": "Auditorium", "building": "Main Building", "floor": 1, "equipment": "Stage, Sound System, Lighting"},
        {"id": "R502", "capacity": 150, "type": "Multi-Purpose Hall", "building": "Events Center", "floor": 1, "equipment": "Flexible Seating, AV Equipment"},
        
        # Small Group Rooms
        {"id": "R601", "capacity": 15, "type": "Tutorial Room", "building": "Academic Support", "floor": 1, "equipment": "Round Table, Whiteboard"},
        {"id": "R602", "capacity": 12, "type": "Tutorial Room", "building": "Academic Support", "floor": 1, "equipment": "Collaborative Setup"},
        {"id": "R603", "capacity": 18, "type": "Tutorial Room", "building": "Academic Support", "floor": 2, "equipment": "Flexible Furniture"}
    ]
    
    # Sample Classes Data
    sample_classes = [
        # Grade 7 Classes
        {"id": "G7-MATH-A", "subject": "Mathematics", "times_per_week": 5, "duration": 1, "grade": "7", "section": "A", "students": 32},
        {"id": "G7-MATH-B", "subject": "Mathematics", "times_per_week": 5, "duration": 1, "grade": "7", "section": "B", "students": 30},
        {"id": "G7-SCI-A", "subject": "Science", "times_per_week": 4, "duration": 1, "grade": "7", "section": "A", "students": 32},
        {"id": "G7-SCI-B", "subject": "Science", "times_per_week": 4, "duration": 1, "grade": "7", "section": "B", "students": 30},
        {"id": "G7-ENG-A", "subject": "English", "times_per_week": 5, "duration": 1, "grade": "7", "section": "A", "students": 32},
        {"id": "G7-ENG-B", "subject": "English", "times_per_week": 5, "duration": 1, "grade": "7", "section": "B", "students": 30},
        {"id": "G7-FIL-A", "subject": "Filipino", "times_per_week": 4, "duration": 1, "grade": "7", "section": "A", "students": 32},
        {"id": "G7-FIL-B", "subject": "Filipino", "times_per_week": 4, "duration": 1, "grade": "7", "section": "B", "students": 30},
        {"id": "G7-HIST-A", "subject": "History", "times_per_week": 3, "duration": 1, "grade": "7", "section": "A", "students": 32},
        {"id": "G7-HIST-B", "subject": "History", "times_per_week": 3, "duration": 1, "grade": "7", "section": "B", "students": 30},
        
        # Grade 8 Classes
        {"id": "G8-MATH-A", "subject": "Mathematics", "times_per_week": 5, "duration": 1, "grade": "8", "section": "A", "students": 34},
        {"id": "G8-MATH-B", "subject": "Mathematics", "times_per_week": 5, "duration": 1, "grade": "8", "section": "B", "students": 31},
        {"id": "G8-PHYS-A", "subject": "Physics", "times_per_week": 4, "duration": 1, "grade": "8", "section": "A", "students": 34},
        {"id": "G8-PHYS-B", "subject": "Physics", "times_per_week": 4, "duration": 1, "grade": "8", "section": "B", "students": 31},
        {"id": "G8-CHEM-A", "subject": "Chemistry", "times_per_week": 3, "duration": 1, "grade": "8", "section": "A", "students": 34},
        {"id": "G8-CHEM-B", "subject": "Chemistry", "times_per_week": 3, "duration": 1, "grade": "8", "section": "B", "students": 31},
        {"id": "G8-ENG-A", "subject": "English", "times_per_week": 5, "duration": 1, "grade": "8", "section": "A", "students": 34},
        {"id": "G8-ENG-B", "subject": "English", "times_per_week": 5, "duration": 1, "grade": "8", "section": "B", "students": 31},
        {"id": "G8-GEO-A", "subject": "Geography", "times_per_week": 3, "duration": 1, "grade": "8", "section": "A", "students": 34},
        {"id": "G8-GEO-B", "subject": "Geography", "times_per_week": 3, "duration": 1, "grade": "8", "section": "B", "students": 31},
        
        # Grade 9 Classes
        {"id": "G9-MATH-A", "subject": "Mathematics", "times_per_week": 5, "duration": 1, "grade": "9", "section": "A", "students": 29},
        {"id": "G9-MATH-B", "subject": "Mathematics", "times_per_week": 5, "duration": 1, "grade": "9", "section": "B", "students": 33},
        {"id": "G9-BIO-A", "subject": "Biology", "times_per_week": 4, "duration": 1, "grade": "9", "section": "A", "students": 29},
        {"id": "G9-BIO-B", "subject": "Biology", "times_per_week": 4, "duration": 1, "grade": "9", "section": "B", "students": 33},
        {"id": "G9-LIT-A", "subject": "Literature", "times_per_week": 4, "duration": 1, "grade": "9", "section": "A", "students": 29},
        {"id": "G9-LIT-B", "subject": "Literature", "times_per_week": 4, "duration": 1, "grade": "9", "section": "B", "students": 33},
        {"id": "G9-ECON-A", "subject": "Economics", "times_per_week": 3, "duration": 1, "grade": "9", "section": "A", "students": 29},
        {"id": "G9-ECON-B", "subject": "Economics", "times_per_week": 3, "duration": 1, "grade": "9", "section": "B", "students": 33},
        {"id": "G9-CS-A", "subject": "Computer Science", "times_per_week": 3, "duration": 1, "grade": "9", "section": "A", "students": 29},
        {"id": "G9-CS-B", "subject": "Computer Science", "times_per_week": 3, "duration": 1, "grade": "9", "section": "B", "students": 33},
        
        # Grade 10 Classes
        {"id": "G10-MATH-A", "subject": "Mathematics", "times_per_week": 5, "duration": 1, "grade": "10", "section": "A", "students": 35},
        {"id": "G10-MATH-B", "subject": "Mathematics", "times_per_week": 5, "duration": 1, "grade": "10", "section": "B", "students": 28},
        {"id": "G10-PHYS-A", "subject": "Physics", "times_per_week": 4, "duration": 1, "grade": "10", "section": "A", "students": 35},
        {"id": "G10-PHYS-B", "subject": "Physics", "times_per_week": 4, "duration": 1, "grade": "10", "section": "B", "students": 28},
        {"id": "G10-CHEM-A", "subject": "Chemistry", "times_per_week": 4, "duration": 1, "grade": "10", "section": "A", "students": 35},
        {"id": "G10-CHEM-B", "subject": "Chemistry", "times_per_week": 4, "duration": 1, "grade": "10", "section": "B", "students": 28},
        {"id": "G10-ENG-A", "subject": "English", "times_per_week": 5, "duration": 1, "grade": "10", "section": "A", "students": 35},
        {"id": "G10-ENG-B", "subject": "English", "times_per_week": 5, "duration": 1, "grade": "10", "section": "B", "students": 28},
        {"id": "G10-POL-A", "subject": "Political Science", "times_per_week": 3, "duration": 1, "grade": "10", "section": "A", "students": 35},
        {"id": "G10-POL-B", "subject": "Political Science", "times_per_week": 3, "duration": 1, "grade": "10", "section": "B", "students": 28},
        
        # Specialized Classes
        {"id": "SPEC-ART-A", "subject": "Arts", "times_per_week": 2, "duration": 2, "grade": "Mixed", "section": "A", "students": 25},
        {"id": "SPEC-ART-B", "subject": "Arts", "times_per_week": 2, "duration": 2, "grade": "Mixed", "section": "B", "students": 22},
        {"id": "SPEC-MUS-A", "subject": "Music", "times_per_week": 2, "duration": 1, "grade": "Mixed", "section": "A", "students": 30},
        {"id": "SPEC-MUS-B", "subject": "Music", "times_per_week": 2, "duration": 1, "grade": "Mixed", "section": "B", "students": 28},
        {"id": "SPEC-PE-A", "subject": "Physical Education", "times_per_week": 3, "duration": 1, "grade": "7-8", "section": "A", "students": 40},
        {"id": "SPEC-PE-B", "subject": "Physical Education", "times_per_week": 3, "duration": 1, "grade": "7-8", "section": "B", "students": 38},
        {"id": "SPEC-PE-C", "subject": "Physical Education", "times_per_week": 3, "duration": 1, "grade": "9-10", "section": "C", "students": 42},
        
        # Advanced/Elective Classes
        {"id": "ADV-STAT-A", "subject": "Statistics", "times_per_week": 3, "duration": 1, "grade": "10", "section": "Advanced", "students": 20},
        {"id": "ADV-IT-A", "subject": "Information Technology", "times_per_week": 4, "duration": 1, "grade": "9-10", "section": "Tech", "students": 24},
        {"id": "ADV-EARTH-A", "subject": "Earth Science", "times_per_week": 3, "duration": 1, "grade": "9-10", "section": "Science", "students": 18},
        {"id": "ADV-HEALTH-A", "subject": "Health Science", "times_per_week": 2, "duration": 1, "grade": "Mixed", "section": "Health", "students": 26},
        {"id": "ADV-BUS-A", "subject": "Business Studies", "times_per_week": 3, "duration": 1, "grade": "10", "section": "Business", "students": 22},
        
        # Special Education
        {"id": "SPED-MATH-A", "subject": "Special Education", "times_per_week": 4, "duration": 1, "grade": "Mixed", "section": "Math Support", "students": 8},
        {"id": "SPED-READ-A", "subject": "Special Education", "times_per_week": 5, "duration": 1, "grade": "Mixed", "section": "Reading Support", "students": 10},
        
        # Support Classes
        {"id": "COUNS-GROUP-A", "subject": "Guidance Counseling", "times_per_week": 1, "duration": 1, "grade": "Mixed", "section": "Group", "students": 12},
        {"id": "LIB-SKILLS-A", "subject": "Library Science", "times_per_week": 1, "duration": 1, "grade": "Mixed", "section": "Research", "students": 15}
    ]
    
    # Load the data into session state
    st.session_state.teachers = sample_teachers
    st.session_state.rooms = sample_rooms
    st.session_state.classes = sample_classes
    
    return len(sample_teachers), len(sample_rooms), len(sample_classes)

def main():
    # Main header
    st.markdown('<h1 class="main-header">📚 SIGASIG Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Smart Intelligent Genetic Algorithm Scheduler for Institutional Governance</p>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🎛️ Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Dashboard Overview", "Data Management", "Schedule Generator", "KPI Analytics", "Teacher Workload", "Anomaly Detection"]
    )
    
    if page == "Dashboard Overview":
        show_dashboard_overview()
    elif page == "Data Management":
        show_data_management()
    elif page == "Schedule Generator":
        show_schedule_generator()
    elif page == "KPI Analytics":
        show_kpi_analytics()
    elif page == "Teacher Workload":
        show_teacher_workload()
    elif page == "Anomaly Detection":
        show_anomaly_detection()

def show_dashboard_overview():
    st.header("📊 Dashboard Overview")
    
    # Sample data button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Load Sample Data", type="primary", help="Load comprehensive sample data for testing"):
            # Create progress bar for data loading
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📊 Loading teachers data...")
            progress_bar.progress(20)
            time.sleep(0.2)
            
            status_text.text("🏢 Loading rooms data...")
            progress_bar.progress(40)
            time.sleep(0.2)
            
            status_text.text("📚 Loading classes data...")
            progress_bar.progress(60)
            time.sleep(0.2)
            
            status_text.text("🔗 Initializing relationships...")
            progress_bar.progress(80)
            time.sleep(0.2)
            
            with st.spinner("Finalizing data load..."):
                teachers_count, rooms_count, classes_count = load_sample_data()
                progress_bar.progress(100)
                time.sleep(0.3)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"✅ Loaded {teachers_count} teachers, {rooms_count} rooms, and {classes_count} classes!")
            st.rerun()
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📚 Total Teachers",
            value=len(st.session_state.teachers),
            delta=f"+{len([t for t in st.session_state.teachers if t.get('status') == 'active'])}" if st.session_state.teachers else "0"
        )
    
    with col2:
        st.metric(
            label="🏢 Total Rooms",
            value=len(st.session_state.rooms),
            delta=f"Capacity: {sum(r.get('capacity', 0) for r in st.session_state.rooms)}"
        )
    
    with col3:
        st.metric(
            label="📖 Total Classes",
            value=len(st.session_state.classes),
            delta=f"Weekly: {sum(c.get('times_per_week', 0) for c in st.session_state.classes)} sessions"
        )
    
    with col4:
        specialization_match = calculate_specialization_match()
        st.metric(
            label="🎯 Specialization Match",
            value=f"{specialization_match:.1f}%",
            delta="Target: 85%"
        )
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.teachers:
            show_teacher_distribution_chart()
        else:
            st.info("Add teachers to see distribution charts")
    
    with col2:
        if st.session_state.schedule:
            show_schedule_utilization_chart()
        else:
            st.info("Generate a schedule to see utilization charts")
    
    # Recent activity
    st.subheader("📈 Recent Activity")
    activity_data = [
        {"Time": "10:30 AM", "Action": "Schedule Generated", "Status": "✅ Success"},
        {"Time": "10:15 AM", "Action": "Teacher Added", "Status": "✅ Success"},
        {"Time": "10:00 AM", "Action": "Room Updated", "Status": "✅ Success"},
        {"Time": "09:45 AM", "Action": "Class Modified", "Status": "⚠️ Warning"},
    ]
    st.dataframe(pd.DataFrame(activity_data), use_container_width=True)

def show_data_management():
    st.header("📝 Data Management")
    
    tab1, tab2, tab3 = st.tabs(["👨‍🏫 Teachers", "🏢 Rooms", "📚 Classes"])
    
    with tab1:
        manage_teachers()
    
    with tab2:
        manage_rooms()
    
    with tab3:
        manage_classes()

def manage_teachers():
    st.subheader("👨‍🏫 Teacher Management")
    
    # Add new teacher form
    with st.expander("➕ Add New Teacher"):
        with st.form("add_teacher"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                teacher_id = st.text_input("Teacher ID*", placeholder="T001")
                major = st.text_input("Major Subject*", placeholder="Mathematics")
            
            with col2:
                minor = st.text_input("Minor Subject", placeholder="Physics")
                experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=5)
            
            with col3:
                license_type = st.selectbox("License Type", ["LET Passer", "Non-LET", "Master's Degree", "PhD"])
                status = st.selectbox("Status", ["Active", "On Leave", "Substitute"])
            
            submitted = st.form_submit_button("Add Teacher")
            
            if submitted and teacher_id and major:
                new_teacher = {
                    "id": teacher_id,
                    "major": major,
                    "minor": minor,
                    "experience": experience,
                    "license": license_type,
                    "status": status.lower()
                }
                st.session_state.teachers.append(new_teacher)
                st.success(f"Teacher {teacher_id} added successfully!")
                st.rerun()
    
    # Display teachers table
    if st.session_state.teachers:
        df = pd.DataFrame(st.session_state.teachers)
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        with col1:
            major_filter = st.multiselect("Filter by Major", df['major'].unique())
        with col2:
            status_filter = st.multiselect("Filter by Status", df['status'].unique())
        with col3:
            exp_filter = st.slider("Minimum Experience", 0, int(df['experience'].max()) if not df.empty else 10, 0)
        
        # Apply filters
        filtered_df = df.copy()
        if major_filter:
            filtered_df = filtered_df[filtered_df['major'].isin(major_filter)]
        if status_filter:
            filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
        filtered_df = filtered_df[filtered_df['experience'] >= exp_filter]
        
        # Display filtered table with edit/delete options
        st.dataframe(filtered_df, use_container_width=True)
        
        # Bulk operations
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📁 Import from CSV"):
                st.info("CSV import feature coming soon!")
        with col2:
            if st.button("📊 Export to CSV"):
                csv = df.to_csv(index=False)
                st.download_button("Download CSV", csv, "teachers.csv", "text/csv")
        with col3:
            if st.button("🗑️ Clear All"):
                if st.button("Confirm Delete All", type="primary"):
                    st.session_state.teachers = []
                    st.rerun()
    else:
        st.info("No teachers added yet. Use the form above to add teachers.")

def manage_rooms():
    st.subheader("🏢 Room Management")
    
    # Add new room form
    with st.expander("➕ Add New Room"):
        with st.form("add_room"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                room_id = st.text_input("Room ID*", placeholder="R001")
                capacity = st.number_input("Capacity*", min_value=1, max_value=100, value=30)
            
            with col2:
                room_type = st.selectbox("Room Type", [
                    "Classroom", "Laboratory", "Computer Lab", "Library", "Music Room", 
                    "Art Room", "Gymnasium", "Counseling Room", "Auditorium", 
                    "Multi-Purpose Hall", "Tutorial Room"
                ])
                equipment = st.text_area("Equipment", placeholder="Projector, Whiteboard, etc.")
            
            with col3:
                building = st.text_input("Building", placeholder="Main Building")
                floor = st.number_input("Floor", min_value=1, max_value=10, value=1)
            
            submitted = st.form_submit_button("Add Room")
            
            if submitted and room_id and capacity:
                new_room = {
                    "id": room_id,
                    "capacity": capacity,
                    "type": room_type,
                    "equipment": equipment,
                    "building": building,
                    "floor": floor
                }
                st.session_state.rooms.append(new_room)
                st.success(f"Room {room_id} added successfully!")
                st.rerun()
    
    # Display rooms table
    if st.session_state.rooms:
        df = pd.DataFrame(st.session_state.rooms)
        st.dataframe(df, use_container_width=True)
        
        # Room statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Capacity", sum(r['capacity'] for r in st.session_state.rooms))
        with col2:
            st.metric("Average Capacity", f"{sum(r['capacity'] for r in st.session_state.rooms) / len(st.session_state.rooms):.1f}")
        with col3:
            room_types = pd.Series([r['type'] for r in st.session_state.rooms])
            st.metric("Most Common Type", room_types.mode().iloc[0] if not room_types.empty else "N/A")
    else:
        st.info("No rooms added yet. Use the form above to add rooms.")

def manage_classes():
    st.subheader("📚 Class Management")
    
    # Add new class form
    with st.expander("➕ Add New Class"):
        with st.form("add_class"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                class_id = st.text_input("Class ID*", placeholder="C001")
                subject = st.text_input("Subject*", placeholder="Mathematics")
            
            with col2:
                times_per_week = st.number_input("Times per Week*", min_value=1, max_value=10, value=3)
                duration = st.number_input("Duration (hours)*", min_value=1, max_value=4, value=1)
            
            with col3:
                grade_level = st.selectbox("Grade Level", ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"])
                section = st.text_input("Section", placeholder="A")
            
            submitted = st.form_submit_button("Add Class")
            
            if submitted and class_id and subject and times_per_week and duration:
                new_class = {
                    "id": class_id,
                    "subject": subject,
                    "times_per_week": times_per_week,
                    "duration": duration,
                    "grade_level": grade_level,
                    "section": section
                }
                st.session_state.classes.append(new_class)
                st.success(f"Class {class_id} added successfully!")
                st.rerun()
    
    # Display classes table
    if st.session_state.classes:
        df = pd.DataFrame(st.session_state.classes)
        st.dataframe(df, use_container_width=True)
        
        # Class statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            total_sessions = sum(c['times_per_week'] for c in st.session_state.classes)
            st.metric("Total Weekly Sessions", total_sessions)
        with col2:
            subjects = pd.Series([c['subject'] for c in st.session_state.classes])
            st.metric("Unique Subjects", len(subjects.unique()))
        with col3:
            avg_duration = sum(c['duration'] for c in st.session_state.classes) / len(st.session_state.classes)
            st.metric("Average Duration", f"{avg_duration:.1f} hours")
    else:
        st.info("No classes added yet. Use the form above to add classes.")

def show_schedule_generator():
    st.header("🎯 Schedule Generator")
    
    if not st.session_state.teachers or not st.session_state.rooms or not st.session_state.classes:
        st.warning("⚠️ Please add teachers, rooms, and classes in the Data Management section before generating a schedule.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Schedule Parameters")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            max_per_day = st.slider("Max Hours per Day", 1, 10, 6)
            max_per_week = st.slider("Max Hours per Week", 10, 40, 30)
        
        with col_b:
            num_shifts = st.selectbox("Number of Shifts", [1, 2, 3], 
                                    format_func=lambda x: {1: "Whole Day", 2: "AM/PM", 3: "AM/PM/Evening"}[x])
        
        with col_c:
            optimization_focus = st.selectbox("Optimization Focus", 
                                            ["Specialization Match", "Workload Balance", "Room Utilization"])
    
    with col2:
        st.subheader("Quick Stats")
        st.metric("Teachers", len(st.session_state.teachers))
        st.metric("Rooms", len(st.session_state.rooms))
        st.metric("Classes", len(st.session_state.classes))
    
    # Add cache management section
    with st.expander("🗄️ Cache Management", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Cache"):
                try:
                    response = requests.get("http://localhost:8000/cache/clear", timeout=10)
                    if response.status_code == 200:
                        st.success("✅ Cache cleared successfully!")
                    else:
                        st.error("❌ Failed to clear cache")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error clearing cache: {e}")
        
        with col2:
            if st.button("📊 Cache Status"):
                try:
                    response = requests.get("http://localhost:8000/cache/status", timeout=10)
                    if response.status_code == 200:
                        cache_info = response.json()
                        st.info(f"📈 Cache size: {cache_info['cache_size']}/{cache_info['max_size']}")
                        st.info(f"⏱️ TTL: {cache_info['ttl_seconds']} seconds")
                    else:
                        st.error("❌ Failed to get cache status")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error getting cache status: {e}")
    
    st.divider()
    
    # Generate schedule button
    if st.button("🚀 Generate Schedule", type="primary", use_container_width=True):
        if not st.session_state.teachers or not st.session_state.rooms or not st.session_state.classes:
            st.error("⚠️ Please load sample data first or add teachers, rooms, and classes manually.")
        else:
            st.info("🔄 Starting schedule generation. This may take a few minutes...")
            
            # Create containers for progress tracking
            progress_container = st.container()
            
            with progress_container:
                schedule_data = generate_schedule(max_per_day, max_per_week, num_shifts)
                
                if schedule_data:
                    st.session_state.schedule = schedule_data
                    # Clear any cached DataFrame and filter states to ensure fresh data
                    if 'original_schedule_df' in st.session_state:
                        del st.session_state.original_schedule_df
                    # Clear filter states
                    for key in ['tab1_teacher_filter', 'tab1_day_filter', 'tab1_subject_filter']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.success("✅ Schedule generated successfully!")
                    
                    # Force rerun to show schedule results in fresh state
                    st.rerun()
                else:
                    st.error("❌ Failed to generate schedule. Please check your constraints.")
    
    # Always show schedule results if schedule exists
    if st.session_state.schedule:
        st.divider()
        show_schedule_results()

def generate_schedule(max_per_day, max_per_week, num_shifts):
    """Generate schedule using the FastAPI backend with progress tracking"""
    try:
        # Prepare data for API
        request_data = {
            "teachers": [{"id": t["id"], "major": t["major"], "minor": t.get("minor", "")} for t in st.session_state.teachers],
            "rooms": [{"id": r["id"], "capacity": r["capacity"]} for r in st.session_state.rooms],
            "classes": [{"id": c["id"], "subject": c["subject"], "times_per_week": c["times_per_week"], "duration": c["duration"]} for c in st.session_state.classes],
            "max_per_day": max_per_day,
            "max_per_week": max_per_week,
            "num_shifts": num_shifts
        }
        
        # Create progress bar and status containers
        progress_bar = st.progress(0)
        status_text = st.empty()
        timer_text = st.empty()
        
        # Start schedule generation
        import threading
        import time
        
        def call_api():
            """Call the API in a separate thread"""
            try:
                response = requests.post("http://localhost:8000/schedule/", json=request_data, timeout=180)  # 3 minutes timeout
                return response
            except Exception as e:
                return None
        
        # Start API call in background
        result_container = {"response": None, "error": None}
        
        def api_thread():
            try:
                result_container["response"] = requests.post("http://localhost:8000/schedule/", json=request_data, timeout=180)  # 3 minutes timeout
            except Exception as e:
                result_container["error"] = e
        
        thread = threading.Thread(target=api_thread)
        thread.start()
        
        # Monitor progress
        start_time = time.time()
        
        while thread.is_alive():
            try:
                # Get progress from API
                progress_response = requests.get("http://localhost:8000/schedule/progress", timeout=5)
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    
                    # Update progress bar
                    progress_bar.progress(progress_data["progress"] / 100)
                    
                    # Update status
                    elapsed_time = time.time() - start_time
                    status_text.text(f"🔄 {progress_data['current_stage']}")
                    
                    # Update timer
                    mins, secs = divmod(int(elapsed_time), 60)
                    timer_text.text(f"⏱️ Time elapsed: {mins:02d}:{secs:02d}")
                    
                    # If there's an estimated time remaining
                    if progress_data.get("estimated_time"):
                        est_mins, est_secs = divmod(int(progress_data["estimated_time"]), 60)
                        timer_text.text(f"⏱️ Elapsed: {mins:02d}:{secs:02d} | Est. remaining: {est_mins:02d}:{est_secs:02d}")
                
            except:
                # If progress API fails, just show elapsed time
                elapsed_time = time.time() - start_time
                mins, secs = divmod(int(elapsed_time), 60)
                timer_text.text(f"⏱️ Time elapsed: {mins:02d}:{secs:02d}")
                status_text.text("🔄 Generating schedule...")
            
            time.sleep(1)  # Update every second
        
        # Wait for thread to complete
        thread.join()
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        timer_text.empty()
        
        # Handle results
        if result_container["error"]:
            raise result_container["error"]
        
        response = result_container["response"]
        if response and response.status_code == 200:
            return response.json()["schedule"]
        else:
            st.error(f"API Error: {response.status_code if response else 'Connection failed'}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to FastAPI server. Please ensure it's running on localhost:8000")
        return None
    except Exception as e:
        st.error(f"Error generating schedule: {str(e)}")
        return None

def show_schedule_results():
    """Display the generated schedule results"""
    if not st.session_state.schedule:
        st.warning("No schedule available. Please generate a schedule first.")
        return
    
    st.subheader("📅 Generated Schedule")
    
    # Store original schedule in session state if not already there
    if 'original_schedule_df' not in st.session_state:
        st.session_state.original_schedule_df = pd.DataFrame(st.session_state.schedule)
    
    # Always use the original data for all tabs
    original_df = st.session_state.original_schedule_df.copy()
    
    # Initialize filter states in session state if not present
    if 'tab1_teacher_filter' not in st.session_state:
        st.session_state.tab1_teacher_filter = []
    if 'tab1_day_filter' not in st.session_state:
        st.session_state.tab1_day_filter = []
    if 'tab1_subject_filter' not in st.session_state:
        st.session_state.tab1_subject_filter = []
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 All Classes", "👨‍🏫 By Teacher", "📊 Analytics", "🏢 By Room"])
    
    with tab1:
        st.subheader("Complete Schedule Overview")
        # Schedule table with filters - work with a separate copy
        display_df = original_df.copy()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            teacher_filter = st.multiselect(
                "Filter by Teacher", 
                display_df['teacher'].unique(), 
                default=st.session_state.tab1_teacher_filter,
                key="all_classes_teacher_filter_unique"
            )
            st.session_state.tab1_teacher_filter = teacher_filter
        with col2:
            day_filter = st.multiselect(
                "Filter by Day", 
                display_df['day'].unique(), 
                default=st.session_state.tab1_day_filter,
                key="all_classes_day_filter_unique"
            )
            st.session_state.tab1_day_filter = day_filter
        with col3:
            subject_filter = st.multiselect(
                "Filter by Subject", 
                display_df['subject'].unique(), 
                default=st.session_state.tab1_subject_filter,
                key="all_classes_subject_filter_unique"
            )
            st.session_state.tab1_subject_filter = subject_filter
        
        # Apply filters to display copy only
        if teacher_filter:
            display_df = display_df[display_df['teacher'].isin(teacher_filter)]
        if day_filter:
            display_df = display_df[display_df['day'].isin(day_filter)]
        if subject_filter:
            display_df = display_df[display_df['subject'].isin(subject_filter)]
        
        st.dataframe(display_df, use_container_width=True)
        
        # Show summary statistics for filtered data
        if not display_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Filtered Classes", len(display_df))
            with col2:
                st.metric("Teachers Involved", display_df['teacher'].nunique())
            with col3:
                st.metric("Rooms Used", display_df['room'].nunique())
            with col4:
                st.metric("Subjects", display_df['subject'].nunique())
    
    with tab2:
        # Pass fresh copy of original data - completely isolated
        show_teacher_schedule_view(original_df.copy())
    
    with tab3:
        # Pass fresh copy of original data - completely isolated
        show_schedule_visualization(original_df.copy())
    
    with tab4:
        # Pass fresh copy of original data - completely isolated
        show_room_schedule_view(original_df.copy())

def show_schedule_visualization(df):
    """Create schedule visualization charts"""
    if df.empty:
        st.warning("No schedule data available for visualization.")
        return
        
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            # Teacher workload distribution
            if 'duration' in df.columns:
                teacher_workload = df.groupby('teacher')['duration'].sum().reset_index()
                fig = px.bar(teacher_workload, x='teacher', y='duration', 
                            title="Teacher Workload Distribution",
                            labels={'duration': 'Total Hours', 'teacher': 'Teacher'})
            else:
                # Fallback to class count if duration not available
                teacher_workload = df.groupby('teacher').size().reset_index(name='classes')
                fig = px.bar(teacher_workload, x='teacher', y='classes', 
                            title="Teacher Class Count Distribution",
                            labels={'classes': 'Number of Classes', 'teacher': 'Teacher'})
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating teacher workload chart: {str(e)}")
    
    with col2:
        try:
            # Room utilization
            room_usage = df.groupby('room').size().reset_index(name='sessions')
            fig = px.pie(room_usage, values='sessions', names='room', 
                        title="Room Utilization Distribution")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating room utilization chart: {str(e)}")

def show_kpi_analytics():
    st.header("📊 KPI Analytics - Teacher Specialization Mismatch")
    
    # Core metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        tsmr = calculate_tsmr()
        st.metric("Teacher Specialization Match Rate (TSMR)", f"{tsmr:.1f}%", 
                 delta=f"Target: 85%" if tsmr < 85 else "✅ Target Met")
    
    with col2:
        lai = calculate_lai()
        st.metric("License Alignment Index (LAI)", f"{lai:.1f}%",
                 delta=f"Target: 90%" if lai < 90 else "✅ Target Met")
    
    with col3:
        der = calculate_der()
        st.metric("Deployment Efficiency Ratio (DER)", f"{der:.1f}%",
                 delta=f"Target: 80%" if der < 80 else "✅ Target Met")
    
    with col4:
        smis = calculate_smis()
        st.metric("School Mismatch Intensity Score (SMIS)", f"{smis:.2f}",
                 delta="Lower is better (0-2 scale)")
    
    # Detailed analytics
    tab1, tab2, tab3 = st.tabs(["📈 Trend Analysis", "🎯 Subject Analysis", "🌐 Benchmarking"])
    
    with tab1:
        show_trend_analysis()
    
    with tab2:
        show_subject_analysis()
    
    with tab3:
        show_benchmarking()

def show_teacher_workload():
    st.header("⏰ Teacher Workload & Overtime Tracking")
    
    if not st.session_state.schedule:
        st.warning("Generate a schedule first to view workload analytics.")
        return
    
    # Calculate workload metrics
    df = pd.DataFrame(st.session_state.schedule)
    workload_analysis = analyze_teacher_workload(df)
    
    # Workload overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        overload_rate = workload_analysis.get('overload_rate', 0)
        st.metric("Overload Rate", f"{overload_rate:.1f}%",
                 delta="Target: <5%" if overload_rate > 5 else "✅ Target Met")
    
    with col2:
        avg_workload = workload_analysis.get('avg_workload', 0)
        st.metric("Average Workload", f"{avg_workload:.1f} hours/week",
                 delta="Optimal: 18-24 hours")
    
    with col3:
        equity_index = workload_analysis.get('equity_index', 0)
        st.metric("Workload Equity Index", f"{equity_index:.2f}",
                 delta="Lower is better")
    
    with col4:
        overtime_hours = workload_analysis.get('total_overtime', 0)
        st.metric("Total Overtime", f"{overtime_hours:.1f} hours",
                 delta="Target: 0 hours")
    
    # Detailed workload analysis
    show_workload_details(workload_analysis)

def show_anomaly_detection():
    st.header("🔍 Anomaly Detection")
    
    st.info("🚧 Anomaly detection features are under development. Coming soon!")
    
    # Placeholder for anomaly detection features
    anomalies = [
        {"Type": "Low-enrollment Gaming", "Description": "Section with <15 students", "Status": "⚠️ Warning", "Count": 2},
        {"Type": "Ghost Subjects", "Description": "Subject not in MELC", "Status": "❌ Critical", "Count": 0},
        {"Type": "Advisory Overuse", "Description": "Teachers with advisory only", "Status": "⚠️ Warning", "Count": 1},
        {"Type": "Subject Rotation", "Description": "Yearly subject changes", "Status": "ℹ️ Info", "Count": 3},
    ]
    
    st.dataframe(pd.DataFrame(anomalies), use_container_width=True)

# Helper functions for calculations
def calculate_specialization_match():
    """Calculate overall specialization match rate"""
    if not st.session_state.schedule or not st.session_state.teachers:
        return 0.0
    
    # Mock calculation - replace with actual logic
    return 67.5  # Placeholder

def calculate_tsmr():
    """Calculate Teacher Specialization Match Rate"""
    if not st.session_state.schedule:
        return 0.0
    
    df = pd.DataFrame(st.session_state.schedule)
    teacher_dict = {t['id']: t for t in st.session_state.teachers}
    
    matches = 0
    total = len(df)
    
    for _, row in df.iterrows():
        teacher = teacher_dict.get(row['teacher'])
        if teacher and teacher['major'] == row['subject']:
            matches += 1
    
    return (matches / total * 100) if total > 0 else 0.0

def calculate_lai():
    """Calculate License Alignment Index"""
    # Mock calculation - replace with actual logic
    return 78.5  # Placeholder

def calculate_der():
    """Calculate Deployment Efficiency Ratio"""
    # Mock calculation - replace with actual logic
    return 72.3  # Placeholder

def calculate_smis():
    """Calculate School Mismatch Intensity Score"""
    # Mock calculation - replace with actual logic
    return 1.2  # Placeholder

def analyze_teacher_workload(df):
    """Analyze teacher workload from schedule data"""
    workload_by_teacher = df.groupby('teacher')['duration'].sum()
    
    overload_threshold = 30
    overloaded_teachers = (workload_by_teacher > overload_threshold).sum()
    overload_rate = (overloaded_teachers / len(workload_by_teacher) * 100) if len(workload_by_teacher) > 0 else 0
    
    return {
        'overload_rate': overload_rate,
        'avg_workload': workload_by_teacher.mean(),
        'equity_index': workload_by_teacher.std(),
        'total_overtime': max(0, workload_by_teacher.sum() - len(workload_by_teacher) * 24),
        'workload_distribution': workload_by_teacher.to_dict()
    }

def show_teacher_distribution_chart():
    """Show teacher distribution by major subject"""
    df = pd.DataFrame(st.session_state.teachers)
    major_counts = df['major'].value_counts()
    
    fig = px.pie(values=major_counts.values, names=major_counts.index, 
                title="Teacher Distribution by Major Subject")
    st.plotly_chart(fig, use_container_width=True)

def show_schedule_utilization_chart():
    """Show schedule utilization chart"""
    df = pd.DataFrame(st.session_state.schedule)
    day_counts = df['day'].value_counts()
    
    fig = px.bar(x=day_counts.index, y=day_counts.values, 
                title="Classes per Day Distribution")
    st.plotly_chart(fig, use_container_width=True)

def show_trend_analysis():
    """Show trend analysis charts"""
    st.subheader("📈 Historical Trends")
    
    # Mock data for demonstration
    dates = pd.date_range('2024-01-01', '2024-12-01', freq='M')
    tsmr_trend = [40 + i*2 + (i%3)*5 for i in range(len(dates))]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=tsmr_trend, mode='lines+markers', name='TSMR'))
    fig.update_layout(title='Teacher Specialization Match Rate Trend', 
                     xaxis_title='Month', yaxis_title='TSMR (%)')
    st.plotly_chart(fig, use_container_width=True)

def show_subject_analysis():
    """Show subject-specific analysis"""
    st.subheader("🎯 Subject-Specific Mismatch Analysis")
    
    # Mock data
    subjects = ['Mathematics', 'Science', 'English', 'Filipino', 'Social Studies']
    mismatch_rates = [45, 52, 38, 29, 41]
    
    fig = px.bar(x=subjects, y=mismatch_rates, 
                title="Subject-Specific Mismatch Rates",
                color=mismatch_rates, color_continuous_scale='RdYlGn_r')
    st.plotly_chart(fig, use_container_width=True)

def show_benchmarking():
    """Show international benchmarking"""
    st.subheader("🌐 International Benchmarking")
    
    benchmark_data = {
        'Country': ['Philippines (Current)', 'Philippines (Target)', 'Australia', 'Finland', 'Singapore'],
        'TSMR (%)': [40, 85, 88, 92, 95],
        'LAI (%)': [65, 90, 91, 94, 96]
    }
    
    df = pd.DataFrame(benchmark_data)
    st.dataframe(df, use_container_width=True)
    
    fig = px.scatter(df, x='TSMR (%)', y='LAI (%)', text='Country',
                    title="International Benchmarking - TSMR vs LAI")
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)

def show_workload_details(workload_analysis):
    """Show detailed workload analysis"""
    st.subheader("📊 Detailed Workload Analysis")
    
    if 'workload_distribution' in workload_analysis:
        workload_df = pd.DataFrame(list(workload_analysis['workload_distribution'].items()), 
                                  columns=['Teacher', 'Hours per Week'])
        
        # Color code based on workload
        def get_workload_color(hours):
            if hours > 30:
                return '🔴 Overloaded'
            elif hours < 15:
                return '🟡 Underloaded'
            else:
                return '🟢 Optimal'
        
        workload_df['Status'] = workload_df['Hours per Week'].apply(get_workload_color)
        st.dataframe(workload_df, use_container_width=True)
        
        # Workload distribution chart
        fig = px.histogram(workload_df, x='Hours per Week', nbins=10,
                          title="Teacher Workload Distribution")
        fig.add_vline(x=18, line_dash="dash", line_color="green", 
                     annotation_text="Min Optimal")
        fig.add_vline(x=24, line_dash="dash", line_color="green", 
                     annotation_text="Max Optimal")
        fig.add_vline(x=30, line_dash="dash", line_color="red", 
                     annotation_text="Overload Threshold")
        st.plotly_chart(fig, use_container_width=True)

def show_teacher_schedule_view(df):
    """Display individual teacher schedules"""
    st.subheader("Individual Teacher Schedules")
    
    # Check if data exists
    if df.empty:
        st.warning("No schedule data available. Please generate a schedule first.")
        return
    
    # Get unique teachers
    teachers = sorted(df['teacher'].unique())
    
    if not teachers:
        st.warning("No teachers found in schedule data.")
        return
    
    # Teacher selection with unique key
    selected_teacher = st.selectbox("Select Teacher", teachers, key="teacher_selector_unique")
    
    if selected_teacher:
        # Filter data for selected teacher
        teacher_schedule = df[df['teacher'] == selected_teacher].copy()
        
        if teacher_schedule.empty:
            st.warning(f"No classes found for {selected_teacher}")
            return
            
        teacher_schedule = teacher_schedule.sort_values(['day', 'period'])
        
        # Teacher info and summary
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### 👨‍🏫 {selected_teacher}")
            
            # Create a weekly schedule view
            days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
            
            for day in days_order:
                day_schedule = teacher_schedule[teacher_schedule['day'] == day]
                if not day_schedule.empty:
                    st.markdown(f"**{day}:**")
                    for _, row in day_schedule.iterrows():
                        st.markdown(f"• {row['period']} - {row['subject']} ({row['class']}) in {row['room']}")
                else:
                    st.markdown(f"**{day}:** No classes")
                st.markdown("")
        
        with col2:
            # Teacher workload summary
            total_hours = teacher_schedule['duration'].sum()
            total_classes = len(teacher_schedule)
            unique_subjects = teacher_schedule['subject'].nunique()
            unique_rooms = teacher_schedule['room'].nunique()
            
            st.markdown("### 📊 Summary")
            st.metric("Total Hours/Week", f"{total_hours}")
            st.metric("Total Classes", f"{total_classes}")
            st.metric("Subjects Taught", f"{unique_subjects}")
            st.metric("Rooms Used", f"{unique_rooms}")
            
            # Subject breakdown
            if not teacher_schedule.empty:
                subject_counts = teacher_schedule['subject'].value_counts()
                st.markdown("**Subject Breakdown:**")
                for subject, count in subject_counts.items():
                    st.markdown(f"• {subject}: {count} classes")
        
        # Detailed schedule table for selected teacher
        st.markdown("### 📋 Detailed Schedule")
        st.dataframe(teacher_schedule[['day', 'period', 'subject', 'class', 'room', 'duration']], 
                    use_container_width=True)

def show_room_schedule_view(df):
    """Display room utilization schedules"""
    st.subheader("Room Utilization Schedules")
    
    # Check if data exists
    if df.empty:
        st.warning("No schedule data available. Please generate a schedule first.")
        return
    
    # Get unique rooms
    rooms = sorted(df['room'].unique())
    
    if not rooms:
        st.warning("No rooms found in schedule data.")
        return
    
    # Room selection with unique key
    selected_room = st.selectbox("Select Room", rooms, key="room_selector_unique")
    
    if selected_room:
        # Filter data for selected room
        room_schedule = df[df['room'] == selected_room].copy()
        
        if room_schedule.empty:
            st.warning(f"No classes scheduled for {selected_room}")
            return
            
        room_schedule = room_schedule.sort_values(['day', 'period'])
        
        # Room info and summary
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### 🏢 {selected_room}")
            
            # Create a weekly schedule view
            days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
            
            for day in days_order:
                day_schedule = room_schedule[room_schedule['day'] == day]
                if not day_schedule.empty:
                    st.markdown(f"**{day}:**")
                    for _, row in day_schedule.iterrows():
                        st.markdown(f"• {row['period']} - {row['subject']} ({row['class']}) by {row['teacher']}")
                else:
                    st.markdown(f"**{day}:** Available")
                st.markdown("")
        
        with col2:
            # Room utilization summary
            total_sessions = len(room_schedule)
            unique_teachers = room_schedule['teacher'].nunique()
            unique_subjects = room_schedule['subject'].nunique()
            unique_classes = room_schedule['class'].nunique()
            
            st.markdown("### 📊 Utilization")
            st.metric("Total Sessions", f"{total_sessions}")
            st.metric("Different Teachers", f"{unique_teachers}")
            st.metric("Different Subjects", f"{unique_subjects}")
            st.metric("Different Classes", f"{unique_classes}")
            
            # Calculate utilization rate (assuming 8 periods per day, 5 days)
            max_possible_sessions = 8 * 5  # 40 sessions per week
            utilization_rate = (total_sessions / max_possible_sessions) * 100
            st.metric("Utilization Rate", f"{utilization_rate:.1f}%")
        
        # Detailed schedule table for selected room
        st.markdown("### 📋 Room Schedule")
        st.dataframe(room_schedule[['day', 'period', 'teacher', 'subject', 'class', 'duration']], 
                    use_container_width=True)

if __name__ == "__main__":
    main()
