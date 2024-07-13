import requests
import json
import pandas as pd
import re
from fuzzywuzzy import fuzz

# Read data from CSV file
df = pd.read_csv('streaming_viewership_data.csv')

# Generate column aliases
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

def parse_request(request, column_aliases):
    entities = {'chart_type': None, 'columns': [], 'conditions': []}

    # Define regex patterns for chart types, columns, and conditions
    chart_type_pattern = r"(pie|bar|histogram|line|area|scatter|box|heatmap|violin|bubble) chart"
    column_pattern = r"\b(" + "|".join(re.escape(alias) for alias in column_aliases.keys()) + r")\b"
    condition_pattern = r"(greater|more|older|above|less|below|younger|equal|equals|exactly) (than|to)? (\d+)"

    # Extract chart type
    chart_type_match = re.search(chart_type_pattern, request, re.IGNORECASE)
    if chart_type_match:
        entities['chart_type'] = chart_type_match.group(1).lower()

    # Extract columns
    columns_matches = re.findall(column_pattern, request, re.IGNORECASE)
    for match in columns_matches:
        actual_col = column_aliases.get(match.lower())
        if actual_col and actual_col not in entities['columns']:
            entities['columns'].append(actual_col)

    # Extract conditions
    condition_matches = re.findall(condition_pattern, request, re.IGNORECASE)
    for match in condition_matches:
        operator, _, value = match
        value = int(value)
        for alias, actual_col in column_aliases.items():
            if re.search(rf"\b{re.escape(alias)}\b", request, re.IGNORECASE):
                entities['conditions'].append({'column': actual_col, 'operator': operator, 'value': value})
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

def update_grafana_panel(grafana_url, api_key, dashboard_uid, panel_id, chart_type, columns, filter_col, operator, value):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Load the current dashboard configuration
    response = requests.get(f'{grafana_url}/api/dashboards/uid/{dashboard_uid}', headers=headers)
    dashboard = response.json()['dashboard']

    # Find the panel and update its configuration
    for panel in dashboard['panels']:
        if panel['id'] == panel_id:
            panel['type'] = chart_type

            # Example: Update panel targets (query) - this needs to be customized based on your data source and query
            panel['targets'] = [
                {
                    "refId": "A",
                    "target": columns,
                    "datasource": None,  # Replace with your datasource
                }
            ]

            # Update other panel settings as needed
            break

    # Save the updated dashboard configuration
    update_response = requests.post(f'{grafana_url}/api/dashboards/db', headers=headers, data=json.dumps({'dashboard': dashboard, 'overwrite': True}))

    if update_response.status_code == 200:
        print('Dashboard updated successfully')
    else:
        print('Error updating dashboard:', update_response.content)

def render_grafana_panel(grafana_url, api_key, dashboard_uid, panel_id, output_path):
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    render_url = f'{grafana_url}/render/d-solo/{dashboard_uid}/?panelId={panel_id}&width=1000&height=500'
    response = requests.get(render_url, headers=headers)

    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f'Panel rendered and saved to {output_path}')
    else:
        print('Error rendering panel:', response.content)

# Example request
user_request = "I want to create a bar chart that studies the relationship between Gender and country where the Age of the user is equal to 30"
structured_query = parse_request(user_request, column_aliases)
print(structured_query)

# Process the structured query
chart_type, columns, filter_col, condition, value = extract_details(structured_query)
filtered_df = filter_data(df, filter_col, condition, value)

# Update Grafana panel
grafana_url = 'http://localhost:3000'
api_key = 'YOUR_GRAFANA_API_KEY'
dashboard_uid = 'YOUR_DASHBOARD_UID'
panel_id = YOUR_PANEL_ID

update_grafana_panel(grafana_url, api_key, dashboard_uid, panel_id, chart_type, columns, filter_col, condition, value)

# Render Grafana panel and save image
output_path = 'grafana_panel.png'
render_grafana_panel(grafana_url, api_key, dashboard_uid, panel_id, output_path)
