from google.cloud import storage
import sys
import os

def upload_image(local_file_path):
    """Upload a local image file to Cloud Storage."""
    try:
        # Initialize the client
        storage_client = storage.Client.from_service_account_json('service-account.json')
        bucket_name = 'emergingtechhubrecordings-images'
        bucket = storage_client.bucket(bucket_name)
        
        # Get the filename from the path
        filename = os.path.basename(local_file_path)
        
        # Create a blob and upload the file
        blob = bucket.blob(filename)
        blob.upload_from_filename(local_file_path)
        
        # Make the blob public
        blob.make_public()
        
        print(f'File {filename} uploaded successfully!')
        print(f'Public URL: {blob.public_url}')
        return blob.public_url
        
    except Exception as e:
        print(f'Error uploading file: {str(e)}')
        return None

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python upload_image.py <path_to_image>')
        sys.exit(1)
        
    local_file_path = sys.argv[1]
    if not os.path.exists(local_file_path):
        print(f'Error: File {local_file_path} does not exist')
        sys.exit(1)
        
    upload_image(local_file_path)
