# import requests

# ARCHIVER_URL = "http://archiver:8080"

# def upload_file_to_archiver(file_path):
#     with open(file_path, "rb") as f:
#         files = {'file': f}
#         response = requests.post(f"{ARCHIVER_URL}/upload", files=files)

#     response.raise_for_status()
#     return response.json()

# def restore_data(date_begin, date_end):
#     url = f"{ARCHIVER_URL}/restore"
#     params = {"date_begin": date_begin, "date_end": date_end}
#     response = requests.post(url, params=params)
#     response.raise_for_status()
#     return response.json()

# def get_current_data():
#     response = requests.get(f"{ARCHIVER_URL}/current")
#     response.raise_for_status()
#     return response.json()
