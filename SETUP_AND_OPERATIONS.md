# SIGASIG Setup and Operations Documentation

## Overview
SIGASIG is a comprehensive teacher scheduling system with FastAPI backend and Streamlit dashboard, featuring intelligent algorithm selection, caching, and performance optimizations.

## System Architecture
- **FastAPI Backend**: Port 8000 - API server with scheduling algorithms
- **Streamlit Dashboard**: Port 8501 - Interactive web interface
- **Algorithms**: Greedy (primary) + PuLP optimization (fallback)
- **Caching**: MD5-based intelligent caching with 30-minute TTL

## Quick Start Commands

### Starting the FastAPI Server
```bash
cd c:\Users\DEXTER\pyproj\sigasig\fastapi_scheduler
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Starting the Streamlit Dashboard
**⚠️ IMPORTANT: Use absolute path to avoid file not found errors**
```bash
python -m streamlit run "c:\Users\DEXTER\pyproj\sigasig\streamlit_dashboard\app.py" --server.port 8501
```

**Alternative method (if in correct directory):**
```bash
cd c:\Users\DEXTER\pyproj\sigasig\streamlit_dashboard
python -m streamlit run app.py --server.port 8501
```

## System URLs
- **FastAPI Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Streamlit Dashboard**: http://localhost:8501
- **Performance Test**: http://localhost:8000/test/performance

## Key Features

### Performance Optimizations
1. **Intelligent Algorithm Selection**
   - Greedy algorithm for complex datasets (>100 assignments)
   - PuLP optimization for simple datasets
   - Automatic complexity detection

2. **Aggressive Performance Tuning**
   - 15-second solver timeout
   - 20% gap tolerance
   - Priority-based teacher scheduling
   - Subject importance ranking

3. **Caching System**
   - MD5-based cache keys
   - 30-minute TTL
   - LRU eviction
   - Cache management UI

### Error Handling
- 3-minute timeout buffer
- Real-time progress tracking
- Graceful fallback mechanisms
- Comprehensive error logging

## Testing Commands

### Performance Test
```bash
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/test/performance" -Method GET | Select-Object -ExpandProperty Content

# Expected result: ~0.38 seconds for test dataset
```

### Health Check
```bash
# FastAPI Health
Invoke-WebRequest -Uri "http://localhost:8000/" -Method GET

# Streamlit Health
Invoke-WebRequest -Uri "http://localhost:8501/" -Method GET
```

## Troubleshooting

### Common Issues

1. **Streamlit "File does not exist" Error**
   - **Solution**: Always use absolute path
   - **Command**: `python -m streamlit run "c:\Users\DEXTER\pyproj\sigasig\streamlit_dashboard\app.py" --server.port 8501`

2. **Port Already in Use**
   - **FastAPI**: Change port in uvicorn command
   - **Streamlit**: Use `--server.port XXXX` parameter

3. **Timeout Errors**
   - **Status**: Resolved with greedy algorithm
   - **Fallback**: System automatically uses greedy for complex datasets

4. **Cache Issues**
   - **Solution**: Use cache management buttons in Streamlit UI
   - **Manual**: Clear cache via dashboard controls

### Performance Benchmarks
- **Test Dataset**: 12 assignments in 0.38 seconds
- **Full Dataset (15 teachers)**: <20 seconds
- **Timeout Prevention**: Guaranteed completion under 30 seconds

## File Structure
```
sigasig/
├── fastapi_scheduler/
│   ├── main.py                 # FastAPI server with optimizations
│   ├── requirements.txt        # Backend dependencies
│   └── templates/             # Web interface templates
├── streamlit_dashboard/
│   ├── app.py                 # Streamlit dashboard
│   └── requirements.txt       # Frontend dependencies
└── SETUP_AND_OPERATIONS.md   # This documentation
```

## Dependencies

### FastAPI Backend
- fastapi
- uvicorn
- pulp
- aiohttp
- python-multipart

### Streamlit Dashboard
- streamlit
- requests
- pandas
- plotly

## Development Notes

### Algorithm Selection Logic
```python
# Complexity threshold: >100 assignments = greedy
if len(teachers) * len(classes) > 100:
    use_greedy_algorithm()
else:
    use_pulp_optimization()
```

### Cache Management
- Cache keys generated using MD5 of input data
- TTL: 30 minutes
- Storage: In-memory with LRU eviction
- UI controls for cache status and clearing

### Progress Tracking
7-stage progress system:
1. Initializing scheduler
2. Processing constraints
3. Generating assignments
4. Optimizing schedule
5. Validating constraints
6. Finalizing schedule
7. Complete

## Production Deployment

### Environment Setup
1. Install Python 3.13+
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Start services using absolute paths

### Monitoring
- Check server logs for errors
- Monitor performance via `/test/performance` endpoint
- Use Streamlit cache management for optimization

### Backup and Recovery
- Cache data is ephemeral (30-minute TTL)
- No persistent data storage required
- System self-heals via algorithm fallbacks

## Version History
- **v1.0**: Basic scheduling system
- **v2.0**: Added async support and caching
- **v3.0**: Implemented greedy algorithm and performance optimizations
- **v3.1**: Resolved timeout issues with intelligent algorithm selection

## Support
For issues or questions, refer to this documentation or check the system logs for detailed error messages.
