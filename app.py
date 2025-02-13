from flask import Flask, render_template
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import re
import os
import json

app = Flask(__name__)

def get_image_url(url):
    """Get the appropriate image URL based on source."""
    if not url or not isinstance(url, str):
        return ''
    
    # If it's already a Cloud Storage URL, return as is
    if 'storage.googleapis.com' in url:
        return url
        
    # If it's a Drive URL, convert it
    if '/file/d/' in url:
        file_id = url.split('/file/d/')[1].split('/')[0]
        return f'https://drive.google.com/uc?id={file_id}'
    elif 'id=' in url:
        file_id = url.split('id=')[1].split('&')[0]
        return f'https://drive.google.com/uc?id={file_id}'
        
    return url

def get_google_sheets_service():
    """Get an authorized Google Sheets API service instance using service account."""
    try:
        import os
        print(f'Current directory: {os.getcwd()}')
        print(f'Files in directory: {os.listdir()}')
        
        # Create credentials using the service account info
        credentials = service_account.Credentials.from_service_account_file(
            'service-account.json',
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
        )
        print('Successfully loaded credentials')
        print(f'Using service account: {credentials.service_account_email}')

        # Build and return the service
        service = build('sheets', 'v4', credentials=credentials)
        print('Successfully built service')
        return service
    except Exception as e:
        import traceback
        print(f'Error getting sheets service: {str(e)}')
        print(f'Traceback: {traceback.format_exc()}')
        return None

@app.route('/')
def index():
    try:
        service = get_google_sheets_service()
        if service is None:
            return "Error: Could not initialize Google Sheets service. Please check the logs."
        
        # Replace with your Google Sheet ID and range
        SPREADSHEET_ID = '1ZFobhUAmJdvsHbYL4i0WZy4Q_CSFgRbiselEbE6gC2M'
        RANGE_NAME = 'Sheet1!A1:Z'  # Get all columns
        
        # Call the Sheets API
        sheet = service.spreadsheets()
        
        # Get the values
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        
        # Get values directly from the sheet
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        
        print('Raw values from sheet:', values)

        if not values:
            return 'No data found in the spreadsheet.'

        # Create a mapping of image URLs
        image_urls = {}
        for row_index, row in enumerate(values):
            for col_index, cell in enumerate(row):
                # Check if the cell contains a Google Drive URL
                if isinstance(cell, str) and 'drive.google.com' in cell:
                    # Convert sharing URL to direct image URL
                    if '/file/d/' in cell:
                        # Extract file ID from URL
                        file_id = cell.split('/file/d/')[1].split('/')[0]
                        image_urls[(row_index, col_index)] = f'https://drive.google.com/uc?id={file_id}'
                    elif 'id=' in cell:
                        # Extract file ID from URL
                        file_id = cell.split('id=')[1].split('&')[0]
                        image_urls[(row_index, col_index)] = f'https://drive.google.com/uc?id={file_id}'

        # Get headers from the first row
        headers = [h.strip() for h in values[0]]  # Strip whitespace from headers
        print('Headers:', headers)
        
        # Process the rest of the rows
        records = []
        for row_idx, row in enumerate(values[1:], 1):  # Skip the header row, start index at 1
            record = {}
            print('\nProcessing row:', row)
            
            # Pad the row with empty strings if it's shorter than headers
            row_data = row + [''] * (len(headers) - len(row))
            
            for i, value in enumerate(row_data):
                if i < len(headers):
                    header = headers[i]
                    header_key = header.strip()
                    
                    # Process value
                    value = value.strip() if value else ''
                    if header_key.lower() == 'image':
                        print(f'Processing image field. Value: {value}')
                        value = get_image_url(value)
                        print(f'Using image URL: {value}')
                        
                    print(f'Column {header_key}: {value}')
                    record[header_key] = value
            
            # Parse the date and add is_future flag
            if 'Date' in record:
                try:
                    # Parse date in MM/DD/YYYY format
                    date_obj = datetime.strptime(record['Date'], '%m/%d/%Y')
                    # Set time to end of day (23:59:59)
                    date_obj = date_obj.replace(hour=23, minute=59, second=59)
                    # Convert to Central Time
                    central = ZoneInfo('America/Chicago')
                    now = datetime.now(central)
                    date_obj = date_obj.replace(tzinfo=central)
                    record['is_future'] = date_obj > now
                except ValueError:
                    record['is_future'] = False
            
            print('Created record:', record)
            # Convert date string to datetime object for sorting
            try:
                record['date_obj'] = datetime.strptime(record['Date'], '%m/%d/%Y')
            except ValueError:
                record['date_obj'] = datetime.min
            records.append(record)

        # Sort records by date in descending order
        records.sort(key=lambda x: x['date_obj'], reverse=True)

        # Separate future and past events
        future_events = [r for r in records if r.get('is_future', False)]
        past_events = [r for r in records if not r.get('is_future', False)]

        # Define the field order for display
        field_order = [
            'Date',
            'Topic',
            'Presenter',
            'Location',
            'Zoom link',
            'Image'
        ]
        
        # Render the template with the data
        return render_template('index.html', 
                             future_events=future_events, 
                             past_events=past_events, 
                             field_order=field_order)

    except HttpError as error:
        print(f'An error occurred: {error}')
        return f'An error occurred: {error}'
    except Exception as e:
        print(f'An error occurred: {str(e)}')
        return f'An error occurred: {str(e)}'

if __name__ == '__main__':
    # For local development, use port 8080
    app.run(host='127.0.0.1', port=8080)
