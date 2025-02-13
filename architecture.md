# System Architecture

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Flask as Flask App
    participant Sheets as Google Sheets
    participant Storage as Cloud Storage
    participant Drive as Google Drive

    %% Initial page load
    User->>Flask: Access application
    activate Flask
    Flask->>Sheets: Request recordings data
    activate Sheets
    Sheets-->>Flask: Return recordings & image URLs
    deactivate Sheets
    
    %% Process each image URL
    loop For each image URL
        alt Cloud Storage URL
            Flask->>Storage: Request image
            activate Storage
            Storage-->>Flask: Return image
            deactivate Storage
        else Google Drive URL
            Flask->>Drive: Request image
            activate Drive
            Drive-->>Flask: Return image
            deactivate Drive
        end
    end
    
    Flask-->>User: Display recordings with images
    deactivate Flask

    %% Image upload process
    User->>Flask: Upload new image
    activate Flask
    Flask->>Storage: Upload to Cloud Storage
    activate Storage
    Storage-->>Flask: Return public URL
    deactivate Storage
    Flask-->>User: Display upload success
    deactivate Flask
    
    %% Update spreadsheet
    User->>Sheets: Update image URL in spreadsheet
    activate Sheets
    Sheets-->>User: Confirm update
    deactivate Sheets

    %% Migration process
    User->>Flask: Run migration script
    activate Flask
    Flask->>Drive: Download images
    activate Drive
    Drive-->>Flask: Return image data
    deactivate Drive
    
    Flask->>Storage: Upload to Cloud Storage
    activate Storage
    Storage-->>Flask: Return new URLs
    deactivate Storage
    
    Flask->>Sheets: Update image URLs
    activate Sheets
    Sheets-->>Flask: Confirm update
    deactivate Sheets
    Flask-->>User: Migration complete
    deactivate Flask
```

## Component Descriptions

1. **User**: End-user accessing the application through a web browser

2. **Flask App**: Python web application that:
   - Serves web pages
   - Handles image uploads
   - Manages data retrieval and display
   - Runs migration scripts

3. **Google Sheets**:
   - Stores recording metadata
   - Contains meeting details and image URLs
   - Acts as a simple database

4. **Cloud Storage**:
   - Stores and serves images
   - Provides public URLs for images
   - Ensures fast and reliable image delivery

5. **Google Drive**:
   - Legacy storage for images
   - Source for image migration
   - Being phased out in favor of Cloud Storage

## Key Processes

### Page Load Process
1. User accesses the application
2. Flask app retrieves data from Google Sheets
3. For each image:
   - If Cloud Storage URL, fetch directly
   - If Drive URL, fetch through Drive API
4. Display complete page to user

### Image Upload Process
1. User uploads new image
2. Flask app processes and uploads to Cloud Storage
3. Cloud Storage returns public URL
4. User updates URL in Google Sheets

### Migration Process
1. User initiates migration
2. Script downloads images from Drive
3. Uploads them to Cloud Storage
4. Updates URLs in the spreadsheet
5. Confirms completion to user
