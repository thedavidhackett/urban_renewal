import math
import time

import pandas as pd
import requests
from tqdm import tqdm

from config import RAW_DATA_DIR

results_page_url = 'https://cdm16818.contentdm.oclc.org/digital/api/search/collection/CPLDURphoto/page/{}/maxRecords/50'
item_page_url = 'https://cdm16818.contentdm.oclc.org/digital/api/collections/CPLDURphoto/items/{}/false' 



def request_and_sleep(url : str) -> requests.Response:
    """
    Attempts url call three times, sleeping for 10, 20, then 30 seconds between
    """
    for i in range(3):
        try:
            response = requests.get(url, timeout=10)
            return response
        except requests.exceptions.RequestException as e:
            print(f'Request {i + 1} Failed Sleeping for {10 + (i *10)} seconds')
            time.sleep(10 + (i * 10))


def main() -> None:
    """
    Runs script to scrape the meta data from 15,515 images of project locations
    from the Chicago Department of Urban Renewal 
    """
    total_iterations = 15515
    num_of_pages = math.ceil(15515 / 50)
    records = []

    with tqdm(total=total_iterations, desc='Progress') as pbar:
        for i in range(num_of_pages):
            results_page_res = request_and_sleep(results_page_url.format(i + 1))
            results_page_data= results_page_res.json()

            for item in results_page_data['items']:
                item_id = item['itemId']
                item_res = request_and_sleep(item_page_url.format(item_id))
                item_res.raise_for_status()
                item_data = item_res.json()

                record = dict()
                record['item_id'] = item_id
                for field in item_data['fields']:
                    record[field['key']] = field['value']

                records.append(record)
                time.sleep(0.5)
                pbar.update(1)
            




    
    pd.DataFrame.from_records(records).to_csv(RAW_DATA_DIR / 'results.csv', index=False)



if __name__ == "__main__":
    main()