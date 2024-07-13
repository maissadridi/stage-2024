import spacy
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Read data from CSV file (replace with your data file)
df = pd.read_csv('converted.csv')

# Generate dynamic column aliases
def generate_column_aliases(df):
    column_aliases = {}
    for col in df.columns:
        col_variations = [col, col.lower(), col.replace("_", " "), col.replace("_", "").lower()]
        col_variations += [re.sub(r'\W+', '', col).lower()]
        col_variations = list(set(col_variations))
        for variation in col_variations:
            column_aliases[variation] = col
    return column_aliases

column_aliases = generate_column_aliases(df)

def parse_user_request(request, df, column_aliases):
    entities = {'chart_type': None, 'columns': [], 'conditions': [], 'group_by': None, 'order_by': None}
    request_lower = request.lower()

    # Extract chart type
    chart_types = ['pie', 'bar', 'histogram', 'line', 'area', 'scatter', 'box', 'heatmap', 'violin', 'bubble']
    chart_type_pattern = r'\b(' + '|'.join(chart_types) + r')\b'
    chart_type_match = re.search(chart_type_pattern, request_lower)
    if chart_type_match:
        entities['chart_type'] = chart_type_match.group(1)

    # Extract columns
    for alias, actual_col in column_aliases.items():
        if alias in request_lower and actual_col not in entities['columns']:
            entities['columns'].append(actual_col)

    # Extract conditions using regex
    condition_extraction_pattern = r"(\w+)\s*(=|>|<|>=|<=|equals|greater than|less than|above|below|more than|older than|younger than)\s*'*(\w+\.?\w*)'*"
    conditions_match = re.findall(condition_extraction_pattern, request_lower)
    for match in conditions_match:
        condition_col_text = match[0].strip().lower()
        operator_text = match[1].strip().lower()
        value = match[2].strip()

        condition_col = None
        for alias, actual_col in column_aliases.items():
            if alias == condition_col_text:
                condition_col = actual_col
                break

        if condition_col:
            if operator_text in ['=', 'equals', 'equal']:
                operator = '='
            elif operator_text in ['>', 'greater than', 'above', 'more than', 'older than']:
                operator = '>'
            elif operator_text in ['<', 'less than', 'below', 'younger than']:
                operator = '<'
            elif operator_text == '>=':
                operator = '>='
            elif operator_text == '<=':
                operator = '<='
            entities['conditions'].append({'column': condition_col, 'operator': operator, 'value': value.lower()})  # Convert value to lowercase

    # Extract group by
    group_by_pattern = r'group\s+by\s+(\w+)'
    group_by_match = re.search(group_by_pattern, request_lower)
    if group_by_match:
        group_by_col = group_by_match.group(1).strip().lower()
        for alias, actual_col in column_aliases.items():
            if alias == group_by_col:
                entities['group_by'] = actual_col
                break

    # Extract order by
    order_by_pattern = r'order\s+by\s+(\w+)'
    order_by_match = re.search(order_by_pattern, request_lower)
    if order_by_match:
        order_by_col = order_by_match.group(1).strip().lower()
        for alias, actual_col in column_aliases.items():
            if alias == order_by_col:
                entities['order_by'] = actual_col
                break

    return entities

def filter_data(df, conditions):
    filtered_df = df.copy()
    if conditions:
        for condition in conditions:
            filter_col = condition['column']
            operator = condition['operator']
            value = condition['value']
            if df[filter_col].dtype == 'O':
                value = str(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    print(f"Unable to convert value '{value}' to float for column '{filter_col}'. Skipping filter.")
                    continue
            if operator == '=':
                filtered_df = filtered_df[filtered_df[filter_col].str.lower() == value]
            elif operator == '>':
                filtered_df = filtered_df[filtered_df[filter_col] > value]
            elif operator == '<':
                filtered_df = filtered_df[filtered_df[filter_col] < value]
            elif operator == '>=':
                filtered_df = filtered_df[filtered_df[filter_col] >= value]
            elif operator == '<=':
                filtered_df = filtered_df[filtered_df[filter_col] <= value]
    return filtered_df

def generate_chart(df, chart_type, columns, group_by=None, order_by=None):
    plt.figure(figsize=(10, 6))
    
    if chart_type == 'pie':
        if len(columns) == 1 and group_by:  # Ensure we have one column for the pie and a valid group_by column
            if group_by in df.columns and columns[0] in df.columns:
                pie_data = df.groupby(group_by)[columns[0]].count()
                plt.pie(pie_data, labels=pie_data.index, autopct='%1.1f%%', startangle=140)
                plt.title(f'Pie Chart of {columns[0].capitalize()} by {group_by.capitalize()}')
            else:
                print(f"Group by column '{group_by}' or pie chart column '{columns[0]}' not found in DataFrame.")
        else:
            print("Invalid columns provided for pie chart.")
    else:
        print(f"Chart type '{chart_type}' is not supported for this request.")
    
    plt.tight_layout()
    plt.show()

def main():
    while True:
        user_input = input("Enter your request (or 'exit' to quit): ").strip().lower()
        if user_input == 'exit':
            break
        parsed_request = parse_user_request(user_input, df, column_aliases)
        print("\nParsed Request:")
        print(parsed_request)
        chart_type = parsed_request['chart_type']
        columns = parsed_request['columns']
        conditions = parsed_request['conditions']
        group_by = parsed_request['group_by']
        order_by = parsed_request['order_by']

        filtered_df = filter_data(df, conditions)

        if filtered_df.empty:
            print("\nNo data available after filtering. Skipping chart generation.")
        else:
            print(f"\nFiltered DataFrame:\n{filtered_df.head()}\n")
            generate_chart(filtered_df, chart_type, columns, group_by, order_by)

if __name__ == "__main__":
    main()
