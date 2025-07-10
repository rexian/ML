## Customer Support Agent for problem categorization
* The customer support agent in written using LangGraph orchestration framework.
* The agent uses LLM model - llama3-70b-instruct from Meta to generate the problem category column.
* The input CSV file - problems.csv is generated using Pandas DataFrame.
* The input file - problems.csv contains 2 columns - problem_id, problem_description.
* The agent used the problem_description to generate problem_category column using LLM model.
* The final output contains columns - problem_id, problem_description and problem_category.
* The final output is written to CSV file - categorized_problems.csv.