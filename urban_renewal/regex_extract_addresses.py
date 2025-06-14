from pathlib import Path
import re
import pandas as pd
import typer
from urban_renewal.config import INTERIM_DATA_DIR

app = typer.Typer()

@app.command()
def main(
    input_col : str,
    output_col : str,
    input_path : Path = INTERIM_DATA_DIR / 'urban_renewal_locations_v2.csv',
    output_path : Path = INTERIM_DATA_DIR / 'urban_renewal_locations_v3.csv',
):
    
    def extract_by_pattern(df, pattern):
        for idx, row in df[df[output_col].isna()].iterrows():
            res = re.search(pattern, row[input_col], flags=re.IGNORECASE)
            if res:
                df.loc[idx, output_col] = res[0]

        return df

    def extract_all_patterns(df, patterns):
        for pattern in patterns:
            df = extract_by_pattern(df, pattern)

        return df

    df = pd.read_csv(INTERIM_DATA_DIR / input_path)

    street_suffixes = 'Ave|Avenue|Street|St|Rd|Blvd|Ln|Dr|Way|Ct|Pl|Terrace|Pkwy|Circle'

    patterns = [
        fr'\b(N|S|E|W)\s+[A-Z0-9][a-z0-9\s]*?(?:\s+({street_suffixes}))?\s+and\s+(N|S|E|W)\s+[A-Z0-9][a-z0-9\s]*?(?:\s+({street_suffixes}))?\b',
        fr'\b\d+\s+to\s+\d+\s+(N|S|E|W)\s+[A-Z0-9][a-z0-9\s]*?(?:\s+({street_suffixes}))\b',
        fr'\b\d+\s+(N|S|E|W)\s+[A-Z0-9][a-z0-9\s]*?(?:\s+({street_suffixes}))\b'
    ]
    

    final_df = extract_all_patterns(df, patterns)
    
    final_df.to_csv(INTERIM_DATA_DIR / output_path, index=False)

    print(f'\n{final_df[output_col].isna().sum()} rows unlabeled out of {len(final_df)}\n')


if __name__ == '__main__':
    app()



