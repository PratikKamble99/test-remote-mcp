from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated , List, Any, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.graph.message import add_messages
# from pydantic import BaseModel
from fastmcp import Client

from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
import asyncio
# import requests
# import random
from dotenv import load_dotenv
load_dotenv()

# create llm instance
llm = ChatOpenAI()

# Define tools
@tool
def calculator (a: int, b: int, operation: str) -> dict:
    """
    Perform basic arithmetic operation on two numbers.
    Supported Operations: add, sub, mul, div 

    Args:
        a (float): _description_
        b (float): _description_
        operation (str): _description_

    Returns:
        dict: _description_
    """
    try:
        if operation == "sub":
            result = a-b
        elif operation == "add":
            result = a+b
        elif operation == "mul":
            result = a*b
        elif operation == "div":
            result = a/b
        else:
            return {"error":f"Unsupported Operation {operation}"}
        
        return result

            
    except Exception as e:
        return {'error':str(e)}
    
# make tools
async def create_tools_from_mcp(client: Client):
    """Create LangChain tools from MCP tools."""
    
    tools_data = await client.list_tools()
    langchain_tools = []
    
    for mcp_tool in tools_data:
        # Dynamically create a function that calls the MCP tool
        async def tool_func(**kwargs):
            result = await client.call_tool(mcp_tool.name, kwargs)
            return result.content[0].text
        
        # Wrap with the @tool decorator
        tool_name = mcp_tool.name
        tool_desc = mcp_tool.description
        tool_schema = mcp_tool.inputSchema
        
        # Create the tool dynamically
        wrapped_tool = tool(
            name=tool_name,
            description=tool_desc,
            args_schema=None  # You'd need to create schema properly
        )(tool_func)
        
        langchain_tools.append(wrapped_tool)
    
    return langchain_tools


# tools = [calculator]

# llm_with_tools = llm.bind_tools(tools)

# Create State
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    
# Define Nodes
# tool_node = ToolNode(tools=tools)

# Replaced with agent function
# def chat_node(state: State):
#     messages = state['messages']
#     response = llm_with_tools.invoke(messages)
    
#     return {"messages":[response]}

# Create Graph
# graph = StateGraph(State)

# graph.add_node("tools",tool_node)
# graph.add_node("chat_node",chat_node)

# Define Edges
# graph.add_edge(START, 'chat_node')
# graph.add_conditional_edges("chat_node", tools_condition)
# graph.add_edge('tools', 'chat_node')

# #compile graph
# chatbot = graph.compile()

# # invoke graph
# res = chatbot.invoke({'messages':[HumanMessage("Hello")]})

# print(res["messages"][-1].content)

async def main():
     async with Client("https://test-remote-mcp.fastmcp.app/mcp") as client:
        # Create tools
        tools = await create_tools_from_mcp(client)
        tools = tools + [calculator]
        
        # Create tool node
        tool_node = ToolNode(tools=tools)
        
        # Create LLM with tools
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        llm_with_tools = llm.bind_tools(tools)
        
        # Define agent function
        def agent(state: State):
            response = llm_with_tools.invoke(state["messages"])
            return {"messages": [response]}
        
        def should_continue(state: State):
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return "__end__"
        
        # Build graph
        workflow = StateGraph(State)
        workflow.add_node("agent", agent)
        workflow.add_node("tools", tool_node)
        
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("tools", "agent")
        
        graph = workflow.compile()
        
        # Use the graph
        result = await graph.ainvoke({
            "messages": [HumanMessage(content="What is 15 + 27?")]
        })

        print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())