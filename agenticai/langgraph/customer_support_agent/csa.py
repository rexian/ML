import os
import pandas as pd
from typing import TypedDict, List, Dict, Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
import asyncio
import json

os.environ["NVIDIA_API_KEY"] = 'NVIDIA_API_KEY'
llm = ChatNVIDIA(model="meta/llama3-70b-instruct", temperature=0.1)

# --- Graph State ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        input_csv_path: Path to the input CSV file.
        output_csv_path: Path to the output CSV file.
        dataframe: The pandas DataFrame being processed.
        error_message: Any error message encountered during processing.
    """
    input_csv_path: str
    output_csv_path: str
    dataframe: Any
    error_message: str


def read_csv_tool(state: GraphState) -> Dict[str, Any]:
    """
    Reads a CSV file from the given path and returns a pandas DataFrame.
    Updates the 'dataframe' in the state.
    """
    input_csv_path = state['input_csv_path']
    print(f"Reading CSV from: {input_csv_path}")
    try:
        df = pd.read_csv(input_csv_path)
        if 'problem_id' not in df.columns or 'problem_description' not in df.columns:
            raise ValueError("CSV must contain 'problem_id' and 'problem_description' columns.")
        print(f"Successfully read CSV. Shape: {df.shape}")
        return {"dataframe": df, "error_message": ""}
    except FileNotFoundError:
        error_msg = f"Error: File not found at {input_csv_path}"
        print(error_msg)
        return {"dataframe": pd.DataFrame(), "error_message": error_msg}
    except Exception as e:
        error_msg = f"Error reading CSV file: {e}"
        print(error_msg)
        return {"dataframe": pd.DataFrame(), "error_message": error_msg}

async def categorize_problem_tool(state: GraphState) -> Dict[str, Any]:
    """
    Iterates through problem descriptions in a DataFrame and assigns a category to each using an LLM.
    Updates the 'dataframe' in the state with a new 'problem_category' column.
    """
    df = state['dataframe']
    if df.empty:
        return {"error_message": "DataFrame is empty, cannot categorize problems."}

    categorized_descriptions = []
    print("Starting problem categorization using LLM...")

    for index, row in df.iterrows():
        problem_description = row['problem_description']
        prompt = f"""You are an expert in categorizing technical and business problems.
        Your task is to analyze the following problem description and assign it to a single, concise category.
        Examples of categories could be 'Software Bug', 'Hardware Issue', 'Network Problem',
        'Customer Service', 'Billing Issue', 'Feature Request', 'Performance Issue',
        'Security Vulnerability', 'Data Issue', 'User Interface (UI)', 'Documentation', 'Other'.
        If none of these fit perfectly, choose the closest one or suggest a new, equally concise category.
        Respond with only the category name, nothing else.

        Problem Description: {problem_description}
        """
        try:
            # Use the ChatNVIDIA LLM for categorization
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            category = response.content.strip()
            categorized_descriptions.append(category)
            print(f"Categorized problem_id {row['problem_id']} ('{problem_description[:50]}...') as: {category}")
        except Exception as e:
            print(f"Error categorizing problem_id {row['problem_id']}: {e}")
            categorized_descriptions.append("Error Categorizing")

    df['problem_category'] = categorized_descriptions
    print("Categorization complete.")
    return {"dataframe": df, "error_message": ""}

def write_csv_tool(state: GraphState) -> Dict[str, Any]:
    """
    Writes a pandas DataFrame to a CSV file at the specified output path.
    """
    df = state['dataframe']
    output_csv_path = state['output_csv_path']
    print(f"Writing categorized data to: {output_csv_path}")
    if df.empty:
        error_msg = "DataFrame is empty, cannot write to CSV."
        print(error_msg)
        return {"error_message": error_msg}
    try:
        df.to_csv(output_csv_path, index=False)
        print(f"Successfully wrote DataFrame to {output_csv_path}")
        return {"error_message": ""}
    except Exception as e:
        error_msg = f"Error writing CSV file: {e}"
        print(error_msg)
        return {"error_message": error_msg}

# --- Define the Graph ---
workflow = StateGraph(GraphState)

# Add nodes for each step
workflow.add_node("read_csv", read_csv_tool)
workflow.add_node("categorize_problems", categorize_problem_tool)
workflow.add_node("write_csv", write_csv_tool)

# Set the entry point
workflow.set_entry_point("read_csv")

# Define the edges (flow)
workflow.add_edge("read_csv", "categorize_problems")
workflow.add_edge("categorize_problems", "write_csv")

# Set the end point
workflow.add_edge("write_csv", END)

# Compile the graph
app = workflow.compile()

# --- Main Execution ---
async def run_workflow():
    # Create a dummy CSV file for demonstration
    dummy_data = {
        'problem_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'problem_description': [
            "Application crashes when clicking the 'Save' button after editing a record.",
            "My internet connection is constantly dropping, affecting video calls.",
            "I want a new feature that allows users to customize their dashboard layout.",
            "The monthly bill shows an incorrect charge for services I cancelled last month.",
            "Website loads very slowly, especially during peak hours. Database queries are taking too long.",
            "The printer is not responding, and I can't print any documents.",
            "Need to update the privacy policy document on the website.",
            "User reported unauthorized access attempts to their account.",
            "The data in the report does not match the source system records.",
            "The mobile app's navigation menu is confusing and hard to use."
        ]
    }
    dummy_df = pd.DataFrame(dummy_data)
    input_csv_file = "problems.csv"
    dummy_df.to_csv(input_csv_file, index=False)
    print(f"Created dummy CSV file: {input_csv_file}")

    output_csv_file = "categorized_problems_langgraph.csv"

    # Initial state for the graph
    initial_state = {
        "input_csv_path": input_csv_file,
        "output_csv_path": output_csv_file,
        "dataframe": pd.DataFrame(), # Initialize as empty, will be populated by read_csv_tool
        "error_message": ""
    }

    async for s in app.astream(initial_state):
        print(f"Current state: {s}")
        if "__end__" in s:
            break


    # Verify the output CSV
    if os.path.exists(output_csv_file):
        categorized_df = pd.read_csv(output_csv_file)
        print(f"\n--- Categorized Problems CSV Content ({output_csv_file}) ---")
        print(categorized_df)
    else:
        print("\nOutput CSV file was not created or an error occurred.")
        # If there was an error, print it from the final state
        final_state = await app.aget_state(initial_state)
        if final_state and final_state.values.get("error_message"):
            print(f"Workflow Error: {final_state.values['error_message']}")

if __name__ == "__main__":
    # Run the asynchronous workflow
    asyncio.run(run_workflow())