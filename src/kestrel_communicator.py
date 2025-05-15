import requests
import logging

"""Used to get data in the viewer format from Kestrel"""
# https://kestrel.1678doozer.net/docs#
log = logging.getLogger(__name__)


def kestrel_request(endpoint, json=True):
    """Send a GET request to the given endpoint"""
    kestrel_key = open("data/api_keys/kestrel_key.txt").read()
    full_url = f"https://kestrel.1678doozer.net/{endpoint}"
    response = requests.get(full_url, headers={"Kestrel-API-Key": kestrel_key})
    if response.status_code >= 300 or response.status_code < 200:
        log.error(f"API request to {full_url} failed with status code: {response.status_code}")
        return None
    else:
        if json:
            return response.json()
        else:
            return response
