# Emerging Tech Hub Recordings Manager

This application manages and displays recordings from the Emerging Tech Hub meetings using Google Sheets as a data source and Google Cloud Storage for image hosting.

## Setup

1. **Service Account Setup**
   - Create a service account in Google Cloud Console
   - Download the service account key and save it as `service-account.json` in the project root
   - Enable the following APIs:
     - Google Sheets API
     - Google Drive API
     - Google Cloud Storage API

2. **Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   - Set `GOOGLE_CLOUD_PROJECT=emergingtechhubrecordings`

## Google Sheets Structure

The application expects a Google Sheet with the following columns:
- Date (MM/DD/YYYY format)
- Topic
- Presenter
- Location
- Zoom link
- Image (Cloud Storage URL)

### Managing Images

#### Option 1: Upload a Single Image
Use the `upload_image.py` script to upload an image to Cloud Storage:
```bash
python upload_image.py path/to/your/image.jpg
```
The script will output the public URL that you can then paste into the Google Sheet.

#### Option 2: Batch Upload from Drive
If you have multiple images in Google Drive, use the `migrate_images.py` script:
```bash
python migrate_images.py
```
This will:
1. Read all image URLs from the Google Sheet
2. Download images from Drive
3. Upload them to Cloud Storage
4. Print the mapping of old Drive URLs to new Cloud Storage URLs

### Best Practices for Images
1. Use descriptive filenames (e.g., "ai-workshop-jan2024.jpg")
2. Keep image sizes reasonable (< 1MB)
3. Use JPEG or PNG formats
4. Always use Cloud Storage URLs in the sheet (https://storage.googleapis.com/emergingtechhubrecordings-images/...)

## Running the Application

Local Development:
```bash
python app.py
```
The app will be available at http://localhost:8080

## Deployment

The application is configured for Google Cloud Run deployment:
```bash
gcloud run deploy emergingtechhub-recordings --source .
```

## Features

- Displays upcoming and past events
- Automatically converts timestamps to Central Time
- Responsive design for mobile and desktop viewing
- Images are served directly from Google Cloud Storage
- Automatic sorting of events by date

## Troubleshooting

1. **Image Not Displaying**
   - Verify the image URL in the sheet is a Cloud Storage URL
   - Check if the image is publicly accessible
   - Use `upload_image.py` to re-upload if needed

2. **Permission Errors**
   - Ensure the service account has the following roles:
     - `roles/sheets.reader`
     - `roles/storage.objectViewer`
     - `roles/storage.objectCreator`

3. **Date Display Issues**
   - Ensure dates in the sheet are in MM/DD/YYYY format
   - Check if the timezone in the application matches your needs
