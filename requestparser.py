import urllib.parse
import time
from datetime import datetime
import requests

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
    
    # Define parts and identify components
    parts = request.split(' ')
    
    # Parse sum fields
    if 'sum' in parts:
        index_sum = parts.index('sum') + 1
        while index_sum < len(parts) and parts[index_sum] != 'group' and parts[index_sum] != 'filter' and parts[index_sum] != 'start' and parts[index_sum] != 'order':
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

    # Construct final URL
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    final_url = f"{base_url}?{query_string}"
    
    print(params)
    # Construct curl command
    curl_command = f"curl -X 'GET' '{final_url}' -H 'accept: application/json' -H 'x-api-key: {api_key}'"
    
    return curl_command, final_url

# Example request
request = 'sum bytesFromClient+bytesFromServer+lostBytesClient group by ts filter by appName = Facebook,Instagram start time 01/01/2010 end time 31/12/2024 order by ts ascending'
api_key = 'a'

# Parse request into curl command
curl_command, final_url = parse_request_to_curl_command(request, api_key)
print("Generated curl command:", curl_command)

# Execute the GET request using requests library
response = requests.get(final_url, headers={'accept': 'application/json', 'x-api-key': api_key})

# Display the response data
print("Response status code:", response.status_code)
print("Response JSON data:", response.json())
