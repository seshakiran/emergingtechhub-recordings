import os
import io
import tempfile
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.cloud import storage
import requests

# Initialize Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'service-account.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Initialize Cloud Storage client
storage_client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
bucket_name = 'emergingtechhubrecordings-images'
bucket = storage_client.bucket(bucket_name)

def extract_file_id(drive_url):
    """Extract file ID from Google Drive URL."""
    if '/file/d/' in drive_url:
        file_id = drive_url.split('/file/d/')[1].split('/')[0]
    elif 'id=' in drive_url:
        file_id = drive_url.split('id=')[1].split('&')[0]
    else:
        return None
    return file_id

def download_and_upload_image(drive_url):
    """Download image from Drive and upload to Cloud Storage."""
    file_id = extract_file_id(drive_url)
    if not file_id:
        print(f"Could not extract file ID from URL: {drive_url}")
        return None

    try:
        # Get file metadata
        file_metadata = drive_service.files().get(fileId=file_id).execute()
        file_name = file_metadata.get('name', 'image.jpg')
        
        # Download file
        request = drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%")

        # Upload to Cloud Storage
        blob = bucket.blob(file_name)
        file.seek(0)
        blob.upload_from_file(file, content_type='image/jpeg')
        
        # Make the blob public
        blob.make_public()
        
        return blob.public_url
    except Exception as e:
        print(f"Error processing {drive_url}: {str(e)}")
        return None

def get_image_urls_from_sheet():
    """Get all image URLs from the Google Sheet."""
    SPREADSHEET_ID = '1ZFobhUAmJdvsHbYL4i0WZy4Q_CSFgRbiselEbE6gC2M'
    RANGE_NAME = 'Sheet1!A1:Z'
    
    try:
        # Get sheet data
        service = build('sheets', 'v4', credentials=credentials)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get('values', [])
        
        if not values:
            print('No data found in sheet')
            return []
            
        # Find the image column index
        headers = [h.strip().lower() for h in values[0]]
        image_col = None
        for i, header in enumerate(headers):
            if header == 'image':
                image_col = i
                break
                
        if image_col is None:
            print('No image column found')
            return []
            
        # Get all image URLs
        drive_urls = []
        for row in values[1:]:
            if len(row) > image_col and row[image_col].strip():
                url = row[image_col].strip()
                if 'drive.google.com' in url:
                    drive_urls.append(url)
                    
        return drive_urls
    except Exception as e:
        print(f'Error getting sheet data: {str(e)}')
        return []

def main():
    drive_urls = get_image_urls_from_sheet()
    print(f'Found {len(drive_urls)} images to migrate')
    
    url_mapping = {}
    for drive_url in drive_urls:
        print(f"\nProcessing: {drive_url}")
        cloud_url = download_and_upload_image(drive_url)
        if cloud_url:
            url_mapping[drive_url] = cloud_url
            print(f"Successfully uploaded to: {cloud_url}")
        else:
            print(f"Failed to process: {drive_url}")
    
    print("\nURL Mapping:")
    for drive_url, cloud_url in url_mapping.items():
        print(f"Drive URL: {drive_url}")
        print(f"Cloud URL: {cloud_url}\n")

if __name__ == '__main__':
    main()
