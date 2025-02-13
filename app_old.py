from flask import Flask, render_template, redirect, request, session, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config
from datetime import datetime
import base64
import re
import os

app = Flask(__name__)
app.secret_key = Config.get_flask_secret_key()

def get_oauth_credentials():
    """Get OAuth 2.0 credentials configuration."""
    return Config.get_oauth_config()

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

def get_google_sheets_service():
    if 'credentials' not in session:
        return None

    # Load credentials from the session.
    credentials = Credentials(**session['credentials'])

    try:
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

@app.route('/')
def index():
    try:
        service = get_google_sheets_service()
        if service is None:
            return redirect('/authorize')
        
        # Replace with your Google Sheet ID and range
        SPREADSHEET_ID = '1ZFobhUAmJdvsHbYL4i0WZy4Q_CSFgRbiselEbE6gC2M'
        RANGE_NAME = 'Sheet1!A1:Z'  # Get all columns
        
        try:
            # First get the values to get headers
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME
            ).execute()
            values = result.get('values', [])
            
            if not values:
                return 'No data found.'
            
            # Get headers from first row
            headers = values[0]
            
            # Define the desired field order (Image will be handled separately in template)
            field_order = ['Topic', 'Presenter', 'Date', 'Location', 'Zoom Link']
            
            # Now get the spreadsheet with grid data to access images
            spreadsheet = service.spreadsheets().get(
                spreadsheetId=SPREADSHEET_ID,
                ranges=[RANGE_NAME],
                includeGridData=True,
                fields='sheets.data.rowData.values.effectiveFormat.backgroundColorStyle,sheets.data.rowData.values.effectiveValue,sheets.data.rowData.values.userEnteredValue'
            ).execute()
            
            # Find the image column index
            image_col_index = headers.index('Image') if 'Image' in headers else -1
            
            # Process each row into a dictionary using headers as keys
            cards = []
            grid_data = spreadsheet['sheets'][0]['data'][0]['rowData']
            
            # Skip the header row
            for idx, row_data in enumerate(grid_data[1:]):
                if 'values' not in row_data:
                    continue
                
                card = {}
                row = values[idx + 1]  # Get the corresponding row from values
                row_values = row_data.get('values', [])
                
                for i, value in enumerate(row):
                    if i < len(headers):
                        header = headers[i]
                        field = header.lower().replace(' ', '_')
                        
                        # Special handling for image column
                        if i == image_col_index and i < len(row_values):
                            try:
                                cell = row_values[i]
                                # Try to get image from cell format
                                background = cell.get('effectiveFormat', {}).get('backgroundColorStyle', {})
                                if background and 'rgbImageBlob' in background:
                                    card[field] = f"data:image/png;base64,{background['rgbImageBlob']}"
                                elif 'userEnteredValue' in cell:
                                    entered_value = cell['userEnteredValue']
                                    if 'stringValue' in entered_value:
                                        value = entered_value['stringValue']
                                        if value.startswith('data:image'):
                                            card[field] = value
                                        elif re.match(r'^[A-Za-z0-9+/=]+$', value.strip()):
                                            card[field] = f'data:image/jpeg;base64,{value}'
                                        else:
                                            card[field] = value
                            except (IndexError, KeyError, AttributeError) as e:
                                print(f"Error processing image: {e}")
                                card[field] = value
                        else:
                            card[field] = value
                        
                        # Convert date string to datetime object for sorting
                        if field == 'date' and value:
                            try:
                                # Try different date formats
                                date_formats = ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y']
                                for date_format in date_formats:
                                    try:
                                        card['date_obj'] = datetime.strptime(value, date_format)
                                        break
                                    except ValueError:
                                        continue
                                if 'date_obj' not in card:
                                    card['date_obj'] = datetime.min
                            except Exception as e:
                                print(f"Error processing date: {e}")
                                card['date_obj'] = datetime.min
                
                if card:  # Only add non-empty cards
                    cards.append(card)
            
            # Sort cards by date in descending order
            cards.sort(key=lambda x: x.get('date_obj', datetime.min), reverse=True)
            
            return render_template('index.html', cards=cards, field_order=field_order)
            
        except HttpError as error:
            return f'An error occurred: {error}'
            
    except Exception as e:
        return f'Authorization error: {str(e)}'

@app.route('/authorize')
def authorize():
    try:
        client_config = get_oauth_credentials()
        if not client_config:
            return 'Error: No OAuth client configuration found. Please check credentials.json'
        
        # Ensure we're using the correct redirect URI
        redirect_uri = 'https://emergingtechhubrecordings.uc.r.appspot.com/oauth2callback'
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to show
        )
        
        session['state'] = state
        return redirect(authorization_url)
    except Exception as e:
        error_msg = str(e)
        print(f'Authorization error: {error_msg}')
        if 'access_denied' in error_msg:
            return 'Access denied. Please make sure your email is added as a test user in the Google Cloud Console.'
        return f'Error setting up authorization: {error_msg}'

@app.route('/oauth2callback')
def oauth2callback():
    try:
        # Get the authorization response from the request URL
        # Ensure we're using HTTPS for the authorization response
        authorization_response = request.url.replace('http:', 'https:')
        if 'http://emergingtechhubrecordings' in authorization_response:
            authorization_response = authorization_response.replace('http://emergingtechhubrecordings', 'https://emergingtechhubrecordings')
        
        client_config = get_oauth_credentials()
        if not client_config:
            return 'Error: No OAuth client configuration found. Please check credentials.json'
        
        # Create flow with the same redirect URI as the authorization request
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri='https://emergingtechhubrecordings.uc.r.appspot.com/oauth2callback'
        )
        
        # Fetch the token
        try:
            flow.fetch_token(authorization_response=authorization_response)
        except Exception as token_error:
            print(f'Token fetch error: {str(token_error)}')
            # If there's a scope mismatch, try to handle it
            if 'Scope has changed' in str(token_error):
                return redirect('/authorize')
            raise token_error
        
        # Store the credentials in the session
        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        return redirect('/')
    except Exception as e:
        print(f'Callback error: {str(e)}')
        return redirect('/authorize')

if __name__ == '__main__':
    # For local development, use port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)
