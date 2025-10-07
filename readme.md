# **Ticketing System with AI Assistant**

A comprehensive mock ticketing API with simulated network conditions and an LLM-powered conversational agent that can interact with the API reliably, demonstrating advanced agent orchestration capabilities.

🌟 **Project Overview**  
This project implements a complete enterprise-grade ticketing system that showcases:

- Mock API with realistic network simulation (latency, failures, recovery)
- AI-Powered Agent using Azure OpenAI GPT-4o with function calling
- Smart Recommendations powered by AI for similar tickets and solutions
- Robust Error Handling with automatic retry logic and exponential backoff
- Advanced Agent Orchestration demonstrating intelligent tool selection and error interpretation
- Predictive Analytics for trending issues and proactive problem resolution

## **🏗️ System Architecture**

```markdown
## System Architecture

┌─────────────────┐     ┌─────────────────┐
│   AI Agent      │────▶│   API Server    │
│  (GPT-4o CLI)   │     │   (FastAPI)     │
└─────────────────┘     └─────────────────┘
         │                        │
         │                        ▼
         │               ┌─────────────────┐
         │               │   Database      │
         │               │ (In-Memory)     │ 
         │               └─────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐     ┌─────────────────┐
│  Azure OpenAI   │     │ Recommendation  │
│   Function      │     │    Engine       │
│   Calling       │     │  (AI-Powered)   │
└─────────────────┘     └─────────────────
Network Simulation Layer:

- • Random latency (0.25-2 seconds)
- • 25% failure rate (500/503 errors)
- • Business logic validation
- • Automatic retry with exponential backoff

AI Recommendation Engine:
• Content similarity analysis
• Historical pattern recognition
• Automatic categorization
• Solution suggestions
• Trending issue detection

 ```

## 📁 Project Structure

    .
    ├── api/
    │   ├── init.py
    │   ├── main.py
    │   ├── models.py
    │   ├── routes.py
    │   ├── middleware.py
    │   ├── database.py
    │   ├── exceptions.py
    │   └── recommendations.py/
    │      
    ├── agents/
    │   ├── _init.py
    │   ├── cli.py
    │   ├── config.py
    │   ├── conversational_agent.py
    │   ├── llm_client.py
    │   ├── tools.py
    │   └── main.py/
    │ 
    ├── config/
    │   ├── _init__.py
    │   └── settings.py/
    │ 
    ├── scripts/
    │   ├── run_tests.py
    │   ├── start_agent.py
    │   └── start_api.py/
    │ 
    ├── tests/
    │   ├── __init.py.py
    │   ├── conftest.py
    │   ├── test_agent_tools.py
    │   ├── test_api.py
    │   └── test_integration.py/
    │ 
    ├── .env.example
    ├── .gitignore
    ├── pyproject.toml
    ├── requirement-dev.txt
    └── requirement.txt


## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (Recommended: Python 3.9 or higher)
- **pip** (Python package installer)
- **Internet connection** (for Azure OpenAI API calls)

### Installation

1. **Clone or download the project**:
    ```bash
    git clone <repository-url>
    cd ticketing-system
    ```

2. **Install production dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Install development dependencies (optional, for testing)**:
    ```bash
    pip install -r requirements-dev.txt
    ```

### Running the System
**Terminal 1 - Start API Server:**

```bash
python scripts/start_api.py
```
- 🌐 API available at: http://localhost:8000
- 📚 Interactive docs: http://localhost:8000/docs
- 🏥 Health check: http://localhost:8000/health

**Terminal 2 - Start AI Agent:**

**Start API:**

```bash
python -m api.main
```

**Start Agent:**

```bash
python -m agent.cli
```
## **First Steps - Try the AI Features!**
Once both services are running, try these enhanced commands:

```bash
# Basic help and test scenarios
You: help
Agent: [Shows all available commands including new AI features]

You: test
Agent: [Runs all 6 orchestration scenarios plus recommendation demos]

# Smart ticket creation with recommendations
You: Create a ticket about keyboard issues and show me similar problems
Agent: [Creates ticket + shows similar tickets + suggests solutions]

# Get recommendations without creating tickets
You: What are common solutions for printer connectivity problems?
Agent: [Shows solutions from similar resolved tickets]

# Analytics and insights
You: What are the trending issues this week?
Agent: [Shows most common problems and keywords]

# Intelligent search
You: Find tickets similar to network connection problems
Agent: [Shows related tickets and their resolutions]
```

## 🎯 Agent Orchestration Scenarios

### Core Orchestration (Original 6)

- Create Ticket with Retry Logic - Automatic retry when API returns 5xx errors
- Retrieve with Intermittency Handling - Graceful handling of API intermittency
- Get Specific Ticket Details - Successful data retrieval and formatting
- Invalid Status Error Handling - Intelligent error interpretation and guidance
- Successful Update with Resolution - Complete workflow orchestration
- Non-existent Ticket Handling - Proper 404 error handling and messaging

### AI-Enhanced Orchestration (New 4)

- Smart Ticket Creation - Create tickets with AI recommendations
- Proactive Solution Suggestions - Get recommendations before ticket creation
- Trend Analysis - Identify and analyze trending issues
- Intelligent Search - Find similar tickets and solutions

## Ticket Model

```json
{
  "id": "ticket-12345678",
  "title": "Issue title",
  "description": "Detailed description",
  "status": "OPEN|RESOLVED|CLOSED",
  "category": "HARDWARE|SOFTWARE|NETWORK|ACCESS|PERFORMANCE|OTHER",
  "priority": "LOW|MEDIUM|HIGH|CRITICAL", 
  "tags": ["printer", "connectivity", "office"],
  "created": "2023-12-01T10:00:00Z",
  "updated": "2023-12-01T11:00:00Z",
  "resolution": "Resolution notes (required for RESOLVED)",
  "comments": ["Comment 1", "Comment 2"]
}
```

## Recommendations Response

```json
{
  "similar_tickets": [
    {
      "id": "ticket-001",
      "title": "Similar issue",
      "similarity_score": 0.85,
      "resolution": "How it was resolved",
      "status": "RESOLVED"
    }
  ],
  "recommended_solutions": [
    {
      "solution": "Try restarting the device and checking connections",
      "confidence": 0.9,
      "source_tickets": ["ticket-001", "ticket-002"],
      "category": "HARDWARE"
    }
  ],
  "suggested_category": "HARDWARE",
  "suggested_priority": "MEDIUM",
  "auto_tags": ["printer", "hardware", "connectivity"]
}
```

## 🤖 Agent Architecture
### LLM Integration

- Model: Azure OpenAI GPT-4o (pre-configured for assessment)
- Enhanced Function Calling: 9 specialized functions including recommendations
- Temperature: 0.1 for consistent, reliable responses
- Built-in Retry Logic: Automatic recovery from LLM service failures


## 🎯 Comprehensive Demo Guide
### Quick Demo (5 minutes)

1. **Start Services**:
    ```bash
   python scripts/start_api.py
   python scripts/start_agent.py
    ```
2. **Try AI Features**:
    ```bash
    Create a ticket about printer issues and show recommendations
    What are trending issues this week?
    ```

## 🧪 Comprehensive Testing
### Run All Tests
 **Try AI Features**:

    ``` bash
    python scripts/run_tests.py
    ```
**Enhanced Test Categories**:

   ```bash
    # All API tests including recommendations
python scripts/run_tests.py --api

# Agent tools with recommendation features  
python scripts/run_tests.py tests/test_agent_tools.py

# Recommendation engine tests
python scripts/run_tests.py tests/test_recommendations.py

# Complete integration tests
python scripts/run_tests.py --integration

# With detailed coverage report
python scripts/run_tests.py --coverage --html-report

# Fast parallel execution
python scripts/run_tests.py --fast --verbose
  ```



## 🚀 Running in Notebook Environment
### For Jupyter/Databricks users, follow these steps:

1. **Setup**:
    ```python
    %pip install fastapi uvicorn pydantic pydantic-settings openai requests rich nest-asyncio
    import nest_asyncio
    nest_asyncio.apply()
    ```

2. **Cell 2: Start API**:
    ```python
    import threading
    import uvicorn
    from api.main import app

    def run_api():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    time.sleep(3)
    print("✅ API running at http://127.0.0.1:8000")

   ```

3. **Initialize Agent**:
    ```python
    from agent.conversational_agent import TicketingAgent
    agent = TicketingAgent("http://127.0.0.1:8000")
    print("✅ Agent ready")

   ```

4. **Test AI Features**:
    ```python
    # Test AI recommendations
    response = agent.chat("Create a ticket about keyboard issues and show recommendations")
    print(response)

    # Test trending analysis  
    response = agent.chat("What are the trending issues?")
    print(response)
    ```

## 🚀 Getting Started Now!
 ```python
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start API (Terminal 1)
python scripts/start_api.py

# 3. Start Enhanced Agent (Terminal 2)  
python scripts/start_agent.py

# 4. Try AI-powered features
> Create a ticket about network issues and show me recommendations
> What are the trending problems this week?
> Find similar tickets about printer connectivity

# 5. Run comprehensive test suite
> test

# 🎉 Explore the intelligent ticketing system!
 ```

 

