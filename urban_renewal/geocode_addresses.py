import os
from pathlib import Path
import tempfile
from batchcensusgeocode import get_census_geocode_batch_results
import geopandas as gpd
import pandas as pd
import typer
from urban_renewal.config import INTERIM_DATA_DIR

app = typer.Typer()

@app.command()
def main(
    inputpath : Path = INTERIM_DATA_DIR / 'urban_renewal_locations_v4.csv',
    output_path : Path = INTERIM_DATA_DIR / 'urban_renewal_locations_v5.csv',
    geodataframe_path : Path = INTERIM_DATA_DIR / 'urban_renewal_addresses_v1.geojson',
    unmatched_path : Path = INTERIM_DATA_DIR / 'unmatched_addresses.csv'
):
    df = pd.read_csv(inputpath)

    df['street_address_cleaned'] = df.street_address.str.upper().str.strip()
    df['zip'] = df.street.str.strip().str.split(' ').str[-1].str.replace('IL', '').str[0:5]
    df['state'] = 'IL'
    df['city'] = 'CHICAGO'

    address_cols = ['street_address_cleaned', 'city', 'state', 'zip']
    addresses = df.loc[df.street_address.notna(), address_cols].drop_duplicates()
    addresses['address_id'] = range(1, len(addresses) + 1)


    df_with_address_id = df.merge(addresses, how='left')
    df_with_address_id.address_id = df_with_address_id.address_id.fillna(-1).astype(int)
    df_with_address_id.to_csv(output_path, index=False)

    with tempfile.TemporaryDirectory() as dirname:
        address_path = os.path.join(dirname, 'ungeocoded_addresses.csv')
        results_path = os.path.join(dirname, 'geocoded_addresses.csv')
        addresses[['address_id'] + address_cols].to_csv(
            address_path,
            index=False
        )

        get_census_geocode_batch_results(
            address_path,
            results_path,
            id_col_name='address_id',
            breakties=True
        )

        geocoded = pd.read_csv(results_path)
    
    coords = geocoded.coordinate.str.split(',')
    gdf = gpd.GeoDataFrame(
        geocoded,
        crs='EPSG:4326',
        geometry=gpd.points_from_xy(
            coords.str[0],
            coords.str[1]
        )
    )


    gdf.to_file(geodataframe_path)

    unmatched_address_ids = gdf[gdf.match == 'No_Match'].address_id.astype(int)
    addresses[addresses.address_id.astype(int).isin(unmatched_address_ids)].to_csv(unmatched_path)


if __name__ == '__main__':
    app()


