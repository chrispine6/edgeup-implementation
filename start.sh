#!/bin/bash

# Document AI Assistant - Startup Script
# This script starts both the Python API server and React client

echo "🚀 Starting Document AI Assistant..."
echo "=================================="

# Check if we're in the right directory
if [ ! -d "python" ] || [ ! -d "client" ]; then
    echo "❌ Error: Please run this script from the edgeup-implementation directory"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    fi
    return 0
}

# Check ports
echo "🔍 Checking ports..."
if ! check_port 8000; then
    echo "   Python API port 8000 is busy. Please stop the existing process."
fi

if ! check_port 3000; then
    echo "   React client port 3000 is busy. Please stop the existing process."
fi

echo ""
echo "📋 Instructions:"
echo "1. Open TWO terminal windows"
echo "2. In the first terminal, run:"
echo "   cd python && python api.py"
echo "3. In the second terminal, run:"
echo "   cd client && npm start"
echo ""
echo "🌐 URLs:"
echo "   React Client: http://localhost:3000"
echo "   Python API:   http://localhost:8000"
echo "   API Health:   http://localhost:8000/health"
echo ""
echo "💡 Tips:"
echo "   - Make sure your .env file in python/ has OPENAI_API_KEY set"
echo "   - Make sure MongoDB and Pinecone credentials are configured"
echo "   - Upload PDF files and ask questions about them!"
