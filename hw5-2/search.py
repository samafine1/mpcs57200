"""
LangGraph Search Agent with Multiple Tools

This app creates an intelligent agent that can:
- Search the web using Tavily
- Perform calculations
- Get current time/date information
- Route queries to appropriate tools
"""

import os
from typing import Annotated, Literal, TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage

import toml


# Load API keys from secrets.toml
def load_secrets():
    """Load secrets from secrets.toml file"""
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        os.environ["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]
        os.environ["TAVILY_API_KEY"] = secrets["TAVILY_API_KEY"]
    except FileNotFoundError:
        print("Error: secrets.toml file not found!")
        print("Please create .streamlit/secrets.toml with:")
        print('OPENAI_API_KEY = "your-key-here"')
        print('TAVILY_API_KEY = "your-key-here"')
        raise


# Define custom tools
@tool
def calculator(expression: str) -> str:
    """Evaluate mathematical expressions. Use for calculations like '2+2' or '15*7'."""
    try:
        # Safe evaluation of mathematical expressions
        result = eval(expression, {"__builtins__": {}}, {})
        return f"The result is: {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    now = datetime.now()
    return f"Current date and time: {now.strftime('%B %d, %Y at %I:%M %p')}"


# Define the agent state
class AgentState(TypedDict):
    """State of the agent containing messages"""
    messages: Annotated[list, add_messages]


# Create the agent
def create_agent():
    """Create and configure the LangGraph agent"""
    
    # Initialize tools
    search_tool = TavilySearchResults(
        max_results=3,
        description="Search the web for current information, news, facts, and real-time data"
    )
    
    tools = [search_tool, calculator, get_current_time]
    
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    
    # Define the agent node
    def agent_node(state: AgentState):
        """Main agent logic - decides which tool to use"""
        system_message = SystemMessage(
            content="""You are a helpful AI assistant with access to multiple tools:
            1. tavily_search_results_json: Search the web for current information
            2. calculator: Perform mathematical calculations
            3. get_current_time: Get current date and time
            
            Use these tools to provide accurate, up-to-date information.
            For questions about current events, people, sports teams, or recent information, use search.
            For math problems, use the calculator.
            For time-related queries, use get_current_time.
            
            Always provide clear, concise answers based on the tool results."""
        )
        
        messages = [system_message] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Define routing logic
    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """Determine if we should use tools or end"""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    
    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()


def run_query(agent, query: str) -> str:
    """Run a query through the agent"""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]},
        {"recursion_limit": 10}
    )
    
    response = result["messages"][-1].content
    print(f"\nResponse: {response}\n")
    return response


def main():
    """Main function to run the agent"""
    
    # Load secrets
    load_secrets()
    
    # Create the agent
    print("Initializing LangGraph Search Agent...")
    agent = create_agent()
    print("Agent ready!\n")
    
    # Example queries
    example_queries = [
        "Who is the quarterback for the Bears?",
        "What is 157 * 234?",
        "What time is it right now?",
        "Who won the latest Nobel Prize in Physics?",
        "Calculate the square root of 144 times 5"
    ]
    
    print("Running example queries...\n")
    
    for query in example_queries:
        run_query(agent, query)
    
    # Interactive mode
    print("\n" + "="*60)
    print("Interactive Mode - Enter your queries (type 'quit' to exit)")
    print("="*60 + "\n")
    
    while True:
        user_input = input("Your query: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            run_query(agent, user_input)
        except Exception as e:
            print(f"Error: {str(e)}\n")


if __name__ == "__main__":
    main()