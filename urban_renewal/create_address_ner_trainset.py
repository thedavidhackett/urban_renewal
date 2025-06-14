import os
from pathlib import Path
from typing import Union

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import spacy
import typer
import usaddress

from urban_renewal.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, INTERIM_DATA_DIR
from urban_renewal.preprocessing import (
    LabeledExample, 
    clean_streetname, 
    construct_street_name, 
    create_address_label,
    examples_to_spacy
)

app = typer.Typer()

@app.command()
def main(
    n_intersections : int,
    n_blocks : int,
    n_street_range : int,
    random_state : int,
    input_path : Path =  RAW_DATA_DIR / 'urban_renewal_location_photos.csv',
    output_path : Path = INTERIM_DATA_DIR / 'urban_renewal_locations_v1.csv',
    output_folder : Path = PROCESSED_DATA_DIR / 'address_ner' 
):
    nlp = spacy.blank("en")
    locations = pd.read_csv(input_path)
    np.random.seed(random_state)

    street_mask = locations.street.notna()
    locations.loc[street_mask, 'street_address'] = locations[street_mask].street.str.split(',').str[0].apply(clean_streetname)
    locations['title_cleaned'] = locations.title.apply(clean_streetname)

    title_contains_street = locations[street_mask].apply(lambda x : x.street_address in x.title_cleaned, axis=1)

    labeled_examples = locations[street_mask&title_contains_street]
    le_last_index = len(labeled_examples) - 1    

    all_streets = locations[street_mask].street_address.apply(lambda x : usaddress.tag(x)).str[0].apply(construct_street_name)
    street_names = all_streets[all_streets.notna()].unique()
    sn_last_index = len(street_names) -1

    highest_address = 9999

    blocks = list(range(100, highest_address, 100))
    blocks_last_index = len(blocks) - 1

    range_additions = [2, 2, 2, 4, 6, 8, 10, 20]
    ra_last_index = len(range_additions) - 1

    def replace_street(new_street: str) -> str:
        row = labeled_examples.iloc[np.random.randint(0, le_last_index)]
        return row.title_cleaned.replace(row.street_address, new_street)

    def create_labeled_example(new_street : str, example : Union[str, bool] = False) -> LabeledExample:
        if not example:
            example = replace_street(new_street)
        label =  create_address_label(example, new_street)
        return (example, [label]) 

    def create_intersection_example() -> LabeledExample:
        street1 = street_names[np.random.randint(0, sn_last_index)]
        street2 = street_names[np.random.randint(0, sn_last_index)]
        new_street = f'{street1} and {street2}'
        return create_labeled_example(new_street)
        
    def create_block_example() -> LabeledExample:
        block = blocks[np.random.randint(0, blocks_last_index)]
        street = street_names[np.random.randint(0, sn_last_index)]
        new_street = f'{block} block of {street}'
        return create_labeled_example(new_street)

    def create_range_example() -> LabeledExample:
        start = np.random.randint(10, highest_address)
        end = start + range_additions[np.random.randint(0, ra_last_index)]
        street = street_names[np.random.randint(0, sn_last_index)]
        new_street = f'{start}-{str(end)[-2:]} {street}'
        return create_labeled_example(new_street)



    current_examples = locations[street_mask&title_contains_street].drop_duplicates(
        subset=['title']
    ).apply(
        lambda x : create_labeled_example(x.street_address, x.title_cleaned),
        axis=1
    ).tolist() 


    intersection_examples = [create_intersection_example() for _ in range(n_intersections)]
    block_examples = [create_block_example() for _ in range(n_blocks)]
    range_examples = [create_range_example() for _ in range(n_street_range)]


    all_examples = current_examples + intersection_examples + block_examples + range_examples

    train_set, remainder = train_test_split(all_examples, test_size=0.2)
    eval_set, test_set = train_test_split(remainder, test_size=0.5)

    os.makedirs(output_folder, exist_ok=True)

    for dataset, outputfile in zip([train_set, eval_set, test_set], ['train.spacy', 'eval.spacy', 'test.spacy']):
        examples_to_spacy(dataset, output_folder / outputfile, nlp)

    locations.to_csv(output_path, index=False)


if __name__ == '__main__':
    app()

