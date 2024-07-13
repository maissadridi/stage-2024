import urllib.parse
import time
from datetime import datetime
import requests
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import websockets
import asyncio
import json

def parse_date_to_epoch(date_str):
    # Convert date string in dd/mm/yyyy format to epoch timestamp
    dt = datetime.strptime(date_str, "%d/%m/%Y")
    epoch_time = int(time.mktime(dt.timetuple()))
    return epoch_time

def parse_request_to_curl_command(request, api_key):
    # Initialize parameters
    sum_fields = []
    group_by = None
    order_by = None
    filters = []
    filter_values = []
    start_time = None
    end_time = None
    order = None
    chart_type = None
    limit = None
    
    # Define parts and identify components
    parts = request.split(' ')
    
    # Parse sum fields
    if 'sum' in parts:
        index_sum = parts.index('sum') + 1
        while index_sum < len(parts) and parts[index_sum] not in ['group', 'filter', 'start', 'order', 'chart', 'limit']:
            sum_fields.append(parts[index_sum])
            index_sum += 1
        sum_fields = ' + '.join(sum_fields)  # Join with space + space
    
    # Parse group by
    if 'group' in parts and 'by' in parts:
        index_group_by = parts.index('by', parts.index('group')) + 1
        group_by = parts[index_group_by]
    
    # Parse order by
    if 'order' in parts and 'by' in parts:
        index_order_by = parts.index('by', parts.index('order')) + 1
        order_by = parts[index_order_by]
        # Check for ascending or descending
        if 'ascending' in parts or 'descending' in parts:
            index_order = parts.index('ascending') if 'ascending' in parts else parts.index('descending')
            order = parts[index_order]

    # Parse filters
    if 'filter' in parts and 'by' in parts:
        index_filter_by = parts.index('by', parts.index('filter')) + 1
        filter_col = parts[index_filter_by]
        filter_value = parts[index_filter_by + 2].split(',')
        filters.append(f'"""{filter_col}"""')
        filter_values.extend([f'"""{value.strip()}"""' for value in filter_value])

    # Parse start time
    if 'start' in parts and 'time' in parts:
        index_start_time = parts.index('time', parts.index('start')) + 1
        start_time = parse_date_to_epoch(parts[index_start_time])
    
    # Parse end time
    if 'end' in parts and 'time' in parts:
        index_end_time = parts.index('time', parts.index('end')) + 1
        end_time = parse_date_to_epoch(parts[index_end_time])
    
    # Parse chart type
    if 'chart' in parts:
        index_chart = parts.index('chart') + 1
        chart_type = parts[index_chart]
    
    # Parse limit
    if 'limit' in parts:
        index_limit = parts.index('limit') + 1
        limit = parts[index_limit]

    # Construct parameters for the URL
    base_url = "http://197.13.9.211:12054/data"
    params = {
        'start_time': start_time if start_time else '0',
        'end_time': end_time if end_time else '99999999999999999999999999',
        'version': '4',
        'country_code': '0000',
    }
    
    if sum_fields:
        # Encode the sum fields manually to ensure + is encoded correctly
        sum_encoded = sum_fields.replace(' + ', '%20%2B%20')
        params['sum'] = sum_encoded
    
    if group_by:
        params['group_by'] = group_by
    if order_by:
        params['order_by'] = order_by
    if filters and filter_values:
        params['filters'] = '[' + ','.join(filters) + ']'
        params['filter_values'] = '[' + ','.join(filter_values) + ']'
    if order:
        params['order'] = order
    if limit:
        params['limit'] = limit

    # Construct final URL
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    final_url = f"{base_url}?{query_string}"
    
    print(params)
    # Construct curl command
    curl_command = f"curl -X 'GET' '{final_url}' -H 'accept: application/json' -H 'x-api-key: {api_key}'"
    
    return curl_command, final_url, chart_type

def fetch_data_from_api(request, api_key):
    curl_command, final_url, chart_type = parse_request_to_curl_command(request, api_key)
    response = requests.get(final_url, headers={'accept': 'application/json', 'x-api-key': api_key})
    if response.status_code == 200:
        return response.json(), chart_type
    else:
        print(f"Failed to fetch data from API. Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        return None, None

def generate_chart(data, chart_type):
    df = pd.DataFrame(data)
    img = io.BytesIO()

    if chart_type == 'table':
        fig, ax = plt.subplots(figsize=(12, 4))  # Set figure size as required
        ax.axis('tight')
        ax.axis('off')
        table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        plt.title('Table Chart')
    elif chart_type == 'pie':
        plt.figure(figsize=(8, 8))
        df.set_index(df.columns[0]).plot.pie(y=df.columns[1], autopct='%1.1f%%')
        plt.title('Pie Chart')
    elif chart_type == 'bar':
        plt.figure(figsize=(10, 6))
        df.plot(kind='bar')
        plt.title('Bar Chart')
    elif chart_type == 'line':
        plt.figure(figsize=(10, 6))
        df.plot(kind='line')
        plt.title('Line Chart')
    elif chart_type == 'scatter':
        plt.figure(figsize=(10, 6))
        if df.shape[1] > 2:
            sns.scatterplot(data=df, x=df.columns[0], y=df.columns[1], hue=df.columns[2])
        else:
            sns.scatterplot(data=df, x=df.columns[0], y=df.columns[1])
        plt.title('Scatter Plot')
    else:
        print("Chart type not supported")
        return None

    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    return img

async def handle_client(websocket, path):
    try:
        message = await websocket.recv()
        request_data = json.loads(message)
        request = request_data['request']
        api_key = request_data['api_key']

        # Fetch data from API
        api_data, chart_type = fetch_data_from_api(request, api_key)

        if api_data:
            img = generate_chart(api_data, chart_type)
            if img:
               img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
               await websocket.send(img_base64)
            else:
                await websocket.send("Failed to generate chart.")
        else:
            await websocket.send("Failed to fetch data from API.")
    except Exception as e:
        await websocket.send(f"Error: {str(e)}")

# Start WebSocket server
start_server = websockets.serve(handle_client, "localhost", 8765)

print("WebSocket server started on ws://localhost:8765")

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
