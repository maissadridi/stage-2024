import re  # Import regular expressions for text processing

def process_request(request_text):
    # Initialize empty structured output
    structured_output = {
        'start_time': None,
        'end_time': None,
        'version': None,
        'country_code': None,
        'sum': None,
        'group_by': None,
        'order_by': None,
        'filters': None,
        'filter_values': None,
        'order': None
    }
    
    # Example pattern matching to extract information from the request text
    # This is a simplistic example, you would need more sophisticated methods
    # depending on the variability and complexity of your input requests.
    
    # Extracting start_time and end_time using regular expressions
    match = re.search(r'\bstart time: (\d+)\b', request_text, re.IGNORECASE)
    if match:
        structured_output['start_time'] = int(match.group(1))
    
    match = re.search(r'\bend time: (\d+)\b', request_text, re.IGNORECASE)
    if match:
        structured_output['end_time'] = int(match.group(1))
    
    # Extracting version number
    match = re.search(r'\bversion: (\d+)\b', request_text, re.IGNORECASE)
    if match:
        structured_output['version'] = match.group(1)
    
    # Extracting country code
    match = re.search(r'\bcountry code: (\d{4})\b', request_text, re.IGNORECASE)
    if match:
        structured_output['country_code'] = match.group(1)
    
    # Extracting sum formula
    match = re.search(r'\bsum: (.+)\b', request_text, re.IGNORECASE)
    if match:
        structured_output['sum'] = match.group(1)
    
    # Extracting group by and order by
    match = re.search(r'\bgroup by: (\w+)\b', request_text, re.IGNORECASE)
    if match:
        structured_output['group_by'] = match.group(1)
    
    match = re.search(r'\border by: (\w+)\b', request_text, re.IGNORECASE)
    if match:
        structured_output['order_by'] = match.group(1)
    
    # Extracting filters and filter values
    match = re.search(r'\bfilters: \[(.+)\]\b', request_text, re.IGNORECASE)
    if match:
        structured_output['filters'] = match.group(1)
    
    match = re.search(r'\bfilter values: \[(.+)\]\b', request_text, re.IGNORECASE)
    if match:
        structured_output['filter_values'] = match.group(1)
    
    # Extracting order
    match = re.search(r'\border: (ascending|descending)\b', request_text, re.IGNORECASE)
    if match:
        structured_output['order'] = match.group(1)
    
    return structured_output

# Example usage
request_text = "Study the relationship between fields. Start time: 1262300400. End time: 1735599600. Version: 4. Country code: 0000. Sum: bytesFromClient+bytesFromServer+lostBytesClient. Group by: ts. Order by: ts. Filters: [""appName""]. Filter values: [""Facebook"",""Instagram""]. Order: ascending."
output = process_request(request_text)
print(output)
