import requests
import time
import os
import json


"""
Code adapted from: https://gist.github.com/danielgross/3ab4104e14faccc12b49200843adab21
"""

__author__ = 'Mike Rustell'
__email__ = 'mike@inframatic.ai'
__github__ = 'CivilEngineerUK'


class MathpixConverter:
    def __init__(self):
        self.app_id = os.getenv('MATHPIX_APP_ID')
        self.app_key = os.getenv('MATHPIX_APP_KEY')

    def send_pdf_to_mathpix(self, file_path, options):
        url = 'https://api.mathpix.com/v3/pdf'
        headers = {
            'app_id': self.app_id,
            'app_key': self.app_key
        }

        with open(file_path, 'rb') as file:
            files = {'file': file}
            data = {
                'options_json': json.dumps(options)
            }
            print(f"Sending {os.path.getsize(file_path) / 1000} kb to Mathpix")
            response = requests.post(url, headers=headers, files=files, data=data)  # Updated data parameter

            if response.status_code != 200:
                print(f"Error: {response.json().get('error', 'Unknown error')}")
                return None

            response_data = response.json()
            print(response_data)
            if 'pdf_id' in response_data:
                pdf_id = response_data['pdf_id']
                print(f"PDF ID: {pdf_id}")
                return pdf_id
            else:
                print("Error: Unable to send PDF to Mathpix")
                return None

    def wait_for_processing(self, pdf_id):
        url = f'https://api.mathpix.com/v3/pdf/{pdf_id}'
        headers = {
            'app_id': self.app_id,
            'app_key': self.app_key
        }

        while True:
            response = requests.get(url, headers=headers)
            response_data = response.json()
            status = response_data.get('status', None)

            if status == 'completed':
                print("Processing complete")
                return True
            elif status == 'error':
                print("Error: Unable to process PDF")
                return False
            else:
                print(f"Status: {status}, waiting for processing to complete")
                time.sleep(5)

    def download_processed_file(self, pdf_id, file_format):
        url = f'https://api.mathpix.com/v3/pdf/{pdf_id}.{file_format}'
        headers = {
            'app_id': self.app_id,
            'app_key': self.app_key
        }

        response = requests.get(url, headers=headers)
        return response

    def mathpix_convert(self, input_pdf_path, output_md_path):
        if not os.path.exists(output_md_path):
            os.makedirs(output_md_path)
        pdf_id = self.send_pdf_to_mathpix(input_pdf_path)
        if pdf_id and self.wait_for_processing(pdf_id):
            return self.download_processed_file(pdf_id, 'md', output_md_path)