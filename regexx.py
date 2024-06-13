import pandas as pd
import re
import matplotlib.pyplot as plt

def parse_user_request_with_regex(request, df):
    # Convert column names to a consistent format for comparison
    columns = {col.lower().replace(" ", "_"): col for col in df.columns}
    
    # Define the regular expression patterns
    chart_type_pattern = r"(bar|pie|line|scatter|histogram|box)"
    data_columns_pattern = r"of\s+([\w\s,]+?)(?:\s+where|$|\s+group\s+by|$|\s+filter\s+by|$|\s+order\s+by|$)"
    conditions_pattern = r"where\s+(.+?)(?:\s+group\s+by|$|\s+filter\s+by|$|\s+order\s+by|$)"
    group_by_pattern = r"group\s+by\s+(.+?)(?:\s+filter\s+by|$|\s+order\s+by|$)"
    filters_pattern = r"filter\s+by\s+(.+?)(?:\s+order\s+by|$)"
    order_by_pattern = r"order\s+by\s+(.+)"
    condition_extraction_pattern = r"(\w+)\s*(=|>|<|>=|<=)\s*'*(\w+)'*"

    # Initialize results
    chart_type = None
    data_columns = []
    conditions = []
    group_by = None
    order_by = None

    # Search for chart type
    chart_type_match = re.search(chart_type_pattern, request, re.IGNORECASE)
    if chart_type_match:
        chart_type = chart_type_match.group(1).lower()

    # Search for data columns
    data_columns_match = re.search(data_columns_pattern, request, re.IGNORECASE)
    if data_columns_match:
        data_columns = [columns.get(col.strip().lower().replace(" ", "_"), col.strip()) for col in re.split(r'\s+and\s+|\s*,\s*', data_columns_match.group(1))]
    
    # Search for conditions
    conditions_match = re.search(conditions_pattern, request, re.IGNORECASE)
    if conditions_match:
        condition_string = conditions_match.group(1)
        conditions = re.findall(condition_extraction_pattern, condition_string)
    
    # Search for group by
    group_by_match = re.search(group_by_pattern, request, re.IGNORECASE)
    if group_by_match:
        group_by_column = columns.get(group_by_match.group(1).strip().lower().replace(" ", "_"), group_by_match.group(1).strip())
        if group_by_column not in data_columns:
            data_columns.append(group_by_column)
        group_by = group_by_column
    
    # Search for filters
    filters_match = re.search(filters_pattern, request, re.IGNORECASE)
    if filters_match:
        filters_string = filters_match.group(1)
        filter_conditions = re.findall(condition_extraction_pattern, filters_string)
        conditions.extend(filter_conditions)
    
    # Search for order by
    order_by_match = re.search(order_by_pattern, request, re.IGNORECASE)
    if order_by_match:
        order_by_column = columns.get(order_by_match.group(1).strip().lower().replace(" ", "_"), order_by_match.group(1).strip())
        if order_by_column not in data_columns:
            data_columns.append(order_by_column)
        order_by = order_by_column

    # Validate and filter data based on conditions
    filtered_df = df
    if conditions:
        for cond in conditions:
            column, operator, value = cond
            column = columns.get(column.lower().replace(" ", "_"), column)
            if column in df.columns:
                if df[column].dtype == 'O':  # Check if the column is of object type (string)
                    value = str(value)
                else:
                    value = float(value)
                if operator == "=":
                    filtered_df = filtered_df[filtered_df[column] == value]
                elif operator == ">":
                    filtered_df = filtered_df[filtered_df[column] > value]
                elif operator == "<":
                    filtered_df = filtered_df[filtered_df[column] < value]
                elif operator == ">=":
                    filtered_df = filtered_df[filtered_df[column] >= value]
                elif operator == "<=":
                    filtered_df = filtered_df[filtered_df[column] <= value]
            else:
                print(f"Warning: Column '{column}' not found in dataframe.")
    
    # Ensure data columns are present in the dataframe
    data_columns = [col for col in data_columns if col in df.columns]

    # Handle missing chart type or data columns
    if not chart_type:
        print("Error: Please specify a chart type.")
        return None
    if not data_columns:
        print("Error: No valid data columns found based on your request or available data.")
        return None
    
    # Sort dataframe based on order by clause
    if order_by and order_by in df.columns:
        filtered_df = filtered_df.sort_values(by=order_by)
    
    # Group by column if specified
    if group_by and group_by in df.columns:
        filtered_df = filtered_df.groupby(group_by).mean().reset_index()

    # Generate the chart (using Matplotlib)
    print(f"Generating a {chart_type} for columns: {', '.join(data_columns)} with conditions: {', '.join([f'{c[0]} {c[1]} {c[2]}' for c in conditions])}")
    plt.figure(figsize=(10, 6))
    if chart_type == "bar":
        filtered_df[data_columns].plot(kind='bar')
    elif chart_type == "pie":
        filtered_df[data_columns[0]].value_counts().plot(kind='pie', autopct='%1.1f%%')
    elif chart_type == "line":
        for col in data_columns[1:]:
            plt.plot(filtered_df[data_columns[0]], filtered_df[col], label=col)
        plt.legend()
    elif chart_type == "scatter":
        if len(data_columns) >= 2:
            plt.scatter(filtered_df[data_columns[0]], filtered_df[data_columns[1]])
            plt.xlabel(data_columns[0])
            plt.ylabel(data_columns[1])
    elif chart_type == "histogram":
        filtered_df[data_columns[0]].plot(kind='hist', bins=10)
    elif chart_type == "box":
        filtered_df[data_columns].plot(kind='box')
    
    plt.title(f"{chart_type.title()} for {', '.join(data_columns)}")
    plt.show()

def main():
    #user_input = "Give me a bar plot of the math_score , reading_score where reading_score = 75 order by math_score"
    user_input = "Show me a pie chart of race ethnicity where lunch = 'standard' and test_preparation_course = 'none' "
    df = pd.read_csv("study_performance.csv")


   # user_input = "Show me a pie chart of Duration Watched where genre ='Comedy' "
   # df = pd.read_csv("streaming_viewership_data.csv")
    parse_user_request_with_regex(user_input, df)

if __name__ == "__main__":
    main()
