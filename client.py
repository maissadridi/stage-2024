import asyncio
import websockets
import json
import base64
import io
import os
import streamlit as st

# Function to connect to the server and fetch the chart
async def connect_to_server(request_data):
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(request_data))
        print(f"Sent request: {request_data['request']}")

        response = await websocket.recv()
        if response.startswith("Error"):
            print(f"Received server response: {response}")
            return response
        else:
            try:
                img_bytes = base64.b64decode(response)
                img_path = os.path.join(os.getcwd(), 'chart.png')
                with open(img_path, 'wb') as f:
                    f.write(img_bytes)
                print(f"Received chart image saved to: {img_path}")
                return img_path
            except Exception as e:
                print(f"Failed to decode image: {str(e)}")
                return None

# Streamlit app code
def main():
    st.title("Chart Generator")

    # Input for user request and API key
    request = st.text_area("Enter your request:", value='sum bytesFromClient+bytesFromServer group by appName order by value chart pie order descending limit 5')
    api_key = st.text_input("Enter your API key:", value='a')

    # Button to submit request
    if st.button("Generate Chart"):
        request_data = {
            'request': request,
            'api_key': api_key
        }

        # Run the async function in the Streamlit app
        response = asyncio.run(connect_to_server(request_data))

        if response is None:
            st.error("Failed to fetch data from server.")
        elif response.startswith("Error"):
            st.error(f"Server returned an error: {response}")
        else:
            st.image(response, caption='Generated Chart', use_column_width=True)

    # Set background style
    st.markdown("""
        <style>
            .stApp {
                background: #FFFFFF; 
               
            }
        </style>
    """, unsafe_allow_html=True)

# Entry point of the Streamlit app
if __name__ == '__main__':
    main()
