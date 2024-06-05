import spacy
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Read data from CSV file
df = pd.read_csv('streaming_viewership_data.csv')

# Function to generate column aliases
def generate_column_aliases(df):
    column_aliases = {}
    for col in df.columns:
        col_variations = [col, col.lower(), col.replace("_", " "), col.replace("_", "").lower()]
        col_variations += [re.sub(r'\W+', '', col).lower()]
        col_variations = list(set(col_variations))
        for variation in col_variations:
            column_aliases[variation] = col
    return column_aliases

# Generate dynamic column aliases
column_aliases = generate_column_aliases(df)

def parse_request(request, df, column_aliases):
    doc = nlp(request)
    entities = {'chart_type': None, 'columns': [], 'conditions': []}

    chart_types = ['pie', 'bar', 'histogram', 'line', 'area', 'scatter', 'box', 'heatmap', 'violin', 'bubble']
    
    for token in doc:
        if token.text.lower() in chart_types:
            entities['chart_type'] = token.text.lower()

    request_lower = request.lower()

    for alias, actual_col in column_aliases.items():
        if alias in request_lower and actual_col not in entities['columns']:
            entities['columns'].append(actual_col)

    condition_patterns = [
        (r"(greater|more|older|above)\s*than\s*(\d+)", "greater"),
        (r"(less|below|younger)\s*than\s*(\d+)", "less"),
        (r"(equal|equals|exactly)\s*to\s*(\d+)", "equal"),
        (r"(greater|more|older|above)\s*(\d+)", "greater"),
        (r"(less|below|younger)\s*(\d+)", "less"),
        (r"(equal|equals|exactly)\s*(\d+)", "equal"),
    ]

    for pattern, operator in condition_patterns:
        match = re.search(pattern, request_lower)
        if match:
            value = int(match.group(2))
            for token in doc:
                if fuzz.ratio(token.text.lower(), "age") > 80:
                    entities['conditions'].append({'column': 'Age', 'operator': operator, 'value': value})
                    break

    print("Identified chart type:", entities['chart_type'])
    print("Identified columns:", entities['columns'])
    print("Identified conditions:", entities['conditions'])

    return entities

def extract_details(structured_query):
    chart_type = structured_query['chart_type']
    columns = structured_query['columns']
    conditions = structured_query['conditions']
    if conditions:
        condition = conditions[0]
        filter_col = condition['column']
        operator = condition['operator']
        value = condition['value']
        return chart_type, columns, filter_col, operator, value
    else:
        return chart_type, columns, None, None, None

def filter_data(df, filter_col, condition, value):
    if filter_col is not None and value is not None:
        if condition in ['greater', 'more', 'older', 'above']:
            return df[df[filter_col] > value]
        elif condition in ['less', 'below', 'younger']:
            return df[df[filter_col] < value]
        elif condition in ['equal', 'equals']:
            return df[df[filter_col] == value]
    return df

import matplotlib.pyplot as plt
import seaborn as sns

def generate_chart(df, chart_type, columns):
    plt.figure(figsize=(10, 6))
    if chart_type == 'line':
        plt.plot(df[columns[0]], df[columns[1]], marker='o', linestyle='-')
        plt.xlabel(columns[0].capitalize())
        plt.ylabel(columns[1].capitalize())
        plt.title(f'{columns[1].capitalize()} vs {columns[0].capitalize()}')
    elif chart_type == 'bar':
        sns.barplot(x=columns[0], y=columns[1], data=df)
        plt.xlabel(columns[0].capitalize())
        plt.ylabel(columns[1].capitalize())
        plt.title(f'{columns[1].capitalize()} by {columns[0].capitalize()}')
    elif chart_type == 'histogram':
        plt.hist(df[columns[0]], bins=10, alpha=0.5, color='blue')
        plt.xlabel(columns[0].capitalize())
        plt.ylabel('Frequency')
        plt.title(f'{columns[0].capitalize()} Histogram')
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
        plt.title(f'{columns[1].capitalize()} Distribution by {columns[0].capitalize()}')
    elif chart_type == 'area':
        plt.fill_between(df[columns[0]], df[columns[1]], color="skyblue", alpha=0.4)
        plt.plot(df[columns[0]], df[columns[1]], color="Slateblue", alpha=0.6)
        plt.xlabel(columns[0].capitalize())
        plt.ylabel(columns[1].capitalize())
        plt.title(f'{columns[1].capitalize()} vs {columns[0].capitalize()} Area Chart')
    elif chart_type == 'bubble':
        plt.scatter(df[columns[0]], df[columns[1]], s=df[columns[2]], alpha=0.5)
        plt.xlabel(columns[0].capitalize())
        plt.ylabel(columns[1].capitalize())
        plt.title(f'{columns[1].capitalize()} vs {columns[0].capitalize()} (Bubble Chart)')
    else:
        print(f"Chart type {chart_type} is not supported.")
    plt.show()

# Example request
user_request = "I want to create a bar chart that studies the relationship between Gender and country where the  age above 50"
structured_query = parse_request(user_request, df, column_aliases)
print(structured_query)

# Process the structured query
chart_type, columns, filter_col, condition, value = extract_details(structured_query)
filtered_df = filter_data(df, filter_col, condition, value)
#generate_chart(filtered_df, chart_type, columns)
