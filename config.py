import os
import json

class Config:
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', 'local-dev')
    IS_PRODUCTION = os.getenv('GAE_ENV', '').startswith('standard')

    @staticmethod
    def get_service_account_path():
        # For local development, use service-account.json in the project directory
        if os.path.exists('service-account.json'):
            return 'service-account.json'
        return None
