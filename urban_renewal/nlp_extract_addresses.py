from pathlib import Path

import pandas as pd
import numpy as np
import spacy
from tqdm import tqdm
import typer

from urban_renewal.config import INTERIM_DATA_DIR, MODELS_DIR

app = typer.Typer()

@app.command()
def main(
    input_col : str,
    output_col : str,
    input_path : Path = INTERIM_DATA_DIR / 'urban_renewal_locations_v1.csv',
    output_path : Path = INTERIM_DATA_DIR / 'urban_renewal_locations_v2.csv',
    model_path : Path = MODELS_DIR / 'address_ner/model-best'
):
    
    df = pd.read_csv(input_path)
    nlp = spacy.load(model_path)

    if output_col not in df.columns:
        df[output_col] = np.nan

    progress_bar = tqdm(total=len(df), desc="Processing")

    def extract_address_ner(row):
        progress_bar.update(1)
        if pd.isna(row[output_col]):
            doc = nlp(row[input_col])
            return [ent.text for ent in doc.ents if ent.label_ == 'ADDRESS']
        
        return [row[output_col]]


    res = df.apply(extract_address_ner, axis=1)

    df[output_col] = res.str[0]

    df.to_csv(output_path, index=False)

    print(f'\n{df[output_col].isna().sum()} rows unlabeled out of {len(df)}\n')


if __name__ == '__main__':
    app()




