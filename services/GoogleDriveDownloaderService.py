import requests


class GoogleDriveDownloaderService:
    DOWNLOAD_URL = "https://docs.google.com/uc?export=download&confirm=1"
    CHUNK_SIZE = 32768

    def download_file(self, id, destination):
        session = requests.Session()

        response = session.get(self.DOWNLOAD_URL, params={'id': id}, stream=True)
        token = self._get_confirm_token(response)

        if token:
            params = {'id': id, 'confirm': token}
            response = session.get(self.DOWNLOAD_URL, params=params, stream=True)

        self._save_response_content(response, destination)

    def _get_confirm_token(self, response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value

        return None

    def _save_response_content(self, response, destination):
        with open(destination, "wb") as f:
            for chunk in response.iter_content(self.CHUNK_SIZE):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
