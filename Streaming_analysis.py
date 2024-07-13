import spacy
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Read data from CSV file
df = pd.read_csv('converted.csv')

# Function to generate column aliases
import re

def generate_column_aliases(df):
    column_aliases = {}
    for col in df.columns:
        col_variations = [
            col,
            col.lower(),
            col.upper(),
            col.title(),
            col.replace("_", " ").lower(),
            col.replace("_", " ").title(),
            col.replace("_", "").lower(),
            col.replace("_", "").title(),
            re.sub(r'\W+', '', col).lower()  # Remove non-word characters
        ]
        col_variations = list(set(col_variations))  # Ensure unique variations
        for variation in col_variations:
            column_aliases[variation] = col
    return column_aliases

# Example usage:
# Assuming df is your DataFrame with columns as defined earlier

# Generate dynamic column aliases
column_aliases = generate_column_aliases(df)

# Print out the generated aliases for verification
#for alias, original_col in column_aliases.items():
   # print(f"Alias: {alias} -> Original Column: {original_col}")


def parse_request(request, df, column_aliases):
    entities = {'chart_type': 'table', 'columns': [], 'conditions': [], 'group_by': None, 'order_by': None, 'top_x': None}
    request_lower = request.lower()

    # Extract chart type
    chart_types = ['pie', 'bar', 'histogram', 'line', 'area', 'scatter', 'box', 'heatmap', 'violin', 'bubble', 'table']
    chart_type_pattern = r'\b(' + '|'.join(chart_types) + r')\b'
    chart_type_match = re.search(chart_type_pattern, request_lower)
    if chart_type_match:
        entities['chart_type'] = chart_type_match.group(1)

    # Extract columns
    for alias, actual_col in column_aliases.items():
        if alias in request_lower and actual_col not in entities['columns']:
            entities['columns'].append(actual_col)

    # Extract conditions
    condition_patterns = [
        (r'(\b\w+\b)\s*(equals|greater than|less than|above|below|more than|older than|younger than)\s*(\d+)', "single"),
        (r'(\b\w+\b)\s*(equals|greater than|less than|above|below|more than|older than|younger than)\s*(\d+)\s+and\s+(\b\w+\b)\s*(equals|greater than|less than|above|below|more than|older than|younger than)\s*(\d+)', "multiple")
    ]

    for pattern, pattern_type in condition_patterns:
        matches = re.findall(pattern, request_lower)
        if pattern_type == "multiple":
            for match in matches:
                for i in [0, 3]:
                    condition_col_text = match[i].strip().lower()
                    operator_text = match[i + 1].strip().lower()
                    value = int(match[i + 2].strip())

                    condition_col = None
                    for alias, actual_col in column_aliases.items():
                        if alias == condition_col_text:
                            condition_col = actual_col
                            break

                    if condition_col:
                        if operator_text in ['equals', 'equal']:
                            operator = 'equal'
                        elif operator_text in ['greater than', 'above', 'more than', 'older than']:
                            operator = 'greater'
                        elif operator_text in ['less than', 'below', 'younger than']:
                            operator = 'less'
                        entities['conditions'].append({'column': condition_col, 'operator': operator, 'value': value})
        elif pattern_type == "single":
            for match in matches:
                condition_col_text = match[0].strip().lower()
                operator_text = match[1].strip().lower()
                value = int(match[2].strip())

                condition_col = None
                for alias, actual_col in column_aliases.items():
                    if alias == condition_col_text:
                        condition_col = actual_col
                        break

                if condition_col:
                    if operator_text in ['equals', 'equal']:
                        operator = 'equal'
                    elif operator_text in ['greater than', 'above', 'more than', 'older than']:
                        operator = 'greater'
                    elif operator_text in ['less than', 'below', 'younger than']:
                        operator = 'less'
                    entities['conditions'].append({'column': condition_col, 'operator': operator, 'value': value})

    # Extract group by
    group_by_match = re.search(r'group by (\b\w+\b)', request_lower)
    if group_by_match:
        group_by_col_text = group_by_match.group(1).strip().lower()
        for alias, actual_col in column_aliases.items():
            if alias == group_by_col_text:
                entities['group_by'] = actual_col
                break

    # Extract order by
    order_by_match = re.search(r'order by (\b\w+\b)', request_lower)
    if order_by_match:
        order_by_col_text = order_by_match.group(1).strip().lower()
        for alias, actual_col in column_aliases.items():
            if alias == order_by_col_text:
                entities['order_by'] = actual_col
                break

    # Extract top X
    top_x_match = re.search(r'top (\d+) based on (\b\w+\b)', request_lower)
    if top_x_match:
        entities['top_x'] = (int(top_x_match.group(1)), top_x_match.group(2).strip().lower())

    # Print statements for debugging
    print("Identified chart type:", entities['chart_type'])
    print("Identified columns:", entities['columns'])
    print("Identified conditions:", entities['conditions'])
    print("Identified group by:", entities['group_by'])
    print("Identified order by:", entities['order_by'])
    print("Identified top X:", entities['top_x'])

    return entities

def extract_details(structured_query):
    chart_type = structured_query['chart_type']
    columns = structured_query['columns']
    conditions = structured_query['conditions']
    group_by = structured_query['group_by']
    order_by = structured_query['order_by']
    top_x = structured_query['top_x']
    return chart_type, columns, conditions, group_by, order_by, top_x

def filter_data(df, conditions, top_x=None):
    # Apply conditions
    if conditions:
        for condition in conditions:
            filter_col = condition['column']
            operator = condition['operator']
            value = condition['value']
            if operator in ['greater', 'more', 'older', 'above']:
                df = df[df[filter_col] > value]
            elif operator in ['less', 'below', 'younger']:
                df = df[df[filter_col] < value]
            elif operator in ['equal', 'equals']:
                df = df[df[filter_col] == value]
    
    # Apply top X if specified
    if top_x:
        num_rows, column = top_x
        actual_column = column_aliases.get(column, column)
        if actual_column in df.columns:
            df = df.sort_values(by=actual_column, ascending=False).head(num_rows)
    
    return df

def generate_chart(df, chart_type, columns, group_by=None, order_by=None, save_path=None):
    if chart_type == 'table':
        columns_to_display = columns
        df_to_display = df[columns_to_display]
        fig, ax = plt.subplots(figsize=(10, 4))  # Create a new figure with a specified size
        ax.axis('tight')
        ax.axis('off')
        table = ax.table(cellText=df_to_display.values, colLabels=df_to_display.columns, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.2)  # Adjust the scale to fit the table better

        if save_path:
            plt.savefig(save_path, format='png')
            print(f"Chart saved successfully as {save_path}")

        plt.show()
        return
    
    plt.figure(figsize=(10, 6))
    # Convert relevant columns to numeric (if they are not already numeric)
    numeric_columns = ['bytesFromClient','bytesFromServer','lostBytesClient','transationDuration','lostBytesServer','srttMsClient','srttMsServer','PublicSourcePort','PublicDestinationPort']
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
    
    # Handle any remaining non-numeric values or NaNs depending on your analysis needs
    df.dropna(subset=numeric_columns, inplace=True)
    
    # Perform group by and mean calculation
    if group_by:
        try:
            group_by_cols = [group_by] if isinstance(group_by, str) else group_by
            df = df.groupby(group_by_cols).mean(numeric_only=True).reset_index()
        except TypeError as e:
            print(f"Error occurred during groupby and mean calculation: {e}")
            return
    
    if chart_type in ['line', 'scatter', 'area', 'bubble'] and len(columns) < 2:
        print(f"Chart type '{chart_type}' requires at least two columns.")
        return
    if chart_type in ['bubble'] and len(columns) < 3:
        print(f"Bubble chart requires at least three columns.")
        return
    
    if order_by:
        df = df.sort_values(by=order_by)

    if chart_type == 'bar':
        df.plot(kind='bar', x=columns[0], y=columns[1])
        plt.xlabel(columns[0].capitalize())
        plt.ylabel(columns[1].capitalize())
        plt.title(f'{columns[1].capitalize()} by {columns[0].capitalize()}')
    elif chart_type == 'histogram':
        df[columns[0]].plot(kind='hist', bins=20)
        plt.xlabel(columns[0].capitalize())
        plt.title(f'{columns[0].capitalize()} Histogram')
    elif chart_type == 'line':
        for col in columns[1:]:
            plt.plot(df[columns[0]], df[col], label=col.capitalize())
        plt.xlabel(columns[0].capitalize())
        plt.ylabel('Values')
        plt.title(f'{columns[0].capitalize()} Line Plot')
        plt.legend()
    elif chart_type == 'pie':
        data = df[columns[0]].value_counts()
        plt.pie(data, labels=data.index, autopct='%1.1f%%')
        plt.title(f'{columns[0].capitalize()} Distribution')
    elif chart_type == 'scatter':
        plt.scatter(df[columns[0]], df[columns[1]])
        plt.xlabel(columns[0].capitalize())
        plt.ylabel(columns[1].capitalize())
        plt.title(f'{columns[1].capitalize()} vs {columns[0].capitalize()}')
    elif chart_type == 'box':
        sns.boxplot(x=columns[0], y=columns[1], data=df)
        plt.xlabel(columns[0].capitalize())
        plt.ylabel(columns[1].capitalize())
        plt.title(f'{columns[1].capitalize()} by {columns[0].capitalize()}')
    elif chart_type == 'heatmap':
        sns.heatmap(df.pivot_table(index=columns[0], columns=columns[1], aggfunc='size'))
        plt.xlabel(columns[1].capitalize())
        plt.ylabel(columns[0].capitalize())
        plt.title(f'{columns[0].capitalize()} vs {columns[1].capitalize()} Heatmap')
    elif chart_type == 'violin':
        sns.violinplot(x=columns[0], y=columns[1], data=df)
        plt.xlabel(columns[0].capitalize())
        plt.ylabel(columns[1].capitalize())
        plt.title(f'{columns[1].capitalize()} by {columns[0].capitalize()}')
    elif chart_type == 'area':
        plt.fill_between(df[columns[0]], df[columns[1]], alpha=0.5)
        plt.xlabel(columns[0].capitalize())
        plt.ylabel(columns[1].capitalize())
        plt.title(f'{columns[1].capitalize()} vs {columns[0].capitalize()}')
    elif chart_type == 'bubble':
        plt.scatter(df[columns[0]], df[columns[1]], s=df[columns[2]]*100, alpha=0.5)
        plt.xlabel(columns[0].capitalize())
        plt.ylabel(columns[1].capitalize())
        plt.title(f'{columns[1].capitalize()} vs {columns[0].capitalize()}')
    
    if save_path:
        plt.savefig(save_path, format='png')
        print(f"Chart saved successfully as {save_path}")
    
    plt.show()

# User request
request = 'pie chart on devicetype '

# Parse the user request
parsed_request = parse_request(request, df, column_aliases)

# Extract details
chart_type, columns, conditions, group_by, order_by, top_x = extract_details(parsed_request)

# Filter data based on conditions
filtered_data = filter_data(df, conditions, top_x)

# Corrected save path
save_path = r'C:\Users\Maissa\Desktop\savedcharts\table_chart.png'

# Generate the chart
generate_chart(filtered_data, chart_type, columns, group_by, order_by, save_path)
