#!/bin/bash

# Cybersecurity Risk Scoring System Startup Script

echo "🛡️  Starting Cybersecurity Risk Scoring System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p backend/data

echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt

echo "🚀 Starting Backend API Server..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd ../frontend

echo "📦 Installing Node.js dependencies..."
npm install

echo "🌐 Starting Frontend Development Server..."
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ System started successfully!"
echo ""
echo "🔗 Access the application at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "📝 Quick Start Guide:"
echo "   1. Click 'Initialize Sample Data' to create test entities"
echo "   2. Click 'Train Model' to train the ML models"
echo "   3. Navigate to 'Risk Assessment' to analyze entities"
echo "   4. Use 'Security Rules' to configure detection patterns"
echo ""
echo "🛑 To stop the system, press Ctrl+C"

# Wait for user interruption
trap "echo '🛑 Stopping system...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait