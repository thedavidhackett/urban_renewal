import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import typer
from urban_renewal.config import DOCS_DIR, EXTERNAL_DATA_DIR, FIGURES_DIR, INTERIM_DATA_DIR

GLOBAL_CRS = 'EPSG:3435'

def year_bin(y):
    start = (y // 5) * 5
    end = start + 4
    return f"{start}–{end}"

app = typer.Typer()

@app.command()
def main():
    df = pd.read_csv(INTERIM_DATA_DIR / 'urban_renewal_locations_v5.csv')

    gdf = gpd.read_file(INTERIM_DATA_DIR / 'urban_renewal_addresses_v1.geojson').to_crs(GLOBAL_CRS)
    city_boundary = gpd.read_file(EXTERNAL_DATA_DIR / 'City_Boundary_20250624.geojson').to_crs(GLOBAL_CRS)


    df['datetime'] = pd.to_datetime(
        df['date'].str.split(',|;').str[0]
    ).apply(
        lambda x: x if x.year < 2025 else x.replace(year=x.year - 100)
    )


    addresses_dates = df.groupby(
        'address_id'
    ).datetime.agg(
        ['min', 'max']
    ).reset_index().rename(
        columns={
            'min': 'first_date',
            'max': 'last_date'
        }
    )

    gdf_with_dates = gdf[gdf.countyfp == 31].merge(
        addresses_dates[(addresses_dates.address_id > 0)&addresses_dates.first_date.notna()], 
        how='inner', 
        on='address_id'
    )

    gdf_with_dates['year'] = gdf_with_dates.first_date.dt.year

    coords = gdf_with_dates.coordinate.str.split(',')
    gdf_with_dates['lon'] = coords.str[0].astype(float)
    gdf_with_dates['lat'] = coords.str[1].astype(float)

    max_year = int(gdf_with_dates.year.max())
    min_year = int(gdf_with_dates.year.min())
    years = list(range(min_year, max_year + 1))

    frames = []
    for frame_year in years:
        df_cum = gdf_with_dates[
            (gdf_with_dates['year'] <= frame_year)
        ].copy()
        df_cum['Current Year'] = frame_year

        df_cum['weight'] = 1

        frames.append(df_cum)


    df_anim = pd.concat(frames)
    df_anim['year_scaled'] = (df_anim['year'] - min_year) / (max_year - min_year)
    df_anim['Current Year'] = df_anim['Current Year'].astype(str)

    df_anim["Five Year Period"] = df_anim["year"].apply(year_bin)

    all_bins = sorted(
        df_anim["Five Year Period"].unique(),
        key=lambda x: int(x.split("–")[0])
    )

    first_frame_year = df_anim['Current Year'].min()
    present_bins = df_anim[df_anim['Current Year'] == first_frame_year]["Five Year Period"].unique()

    missing_bins = [b for b in all_bins if b not in present_bins]
    dummy_rows = []

    for b in missing_bins:
        dummy_rows.append({
            'lat': 0,  # out of view
            'lon': 0,
            'year': 0,
            'Current Year': first_frame_year,
            'weight': 0.0001,
            'Five Year Period': b
        })

    df_anim = pd.concat([df_anim, pd.DataFrame(dummy_rows)], ignore_index=True)

    df_anim = df_anim.rename(columns={
        'parsed': 'Project Address',
    })

    df_anim['First Photo Taken'] = df_anim.first_date.astype(str)
    df_anim['Last Photo Taken'] = df_anim.last_date.astype(str)

    fig = px.scatter_mapbox(
        df_anim,
        lat='lat',
        lon='lon',
        color='Five Year Period',
        size='weight',
        opacity=.8,
        center={'lat': 41.8781, 'lon': -87.6298},
        zoom=9.5,
        animation_frame='Current Year',
        mapbox_style='carto-positron',
        category_orders={"Five Year Period": all_bins},
        height=800,
        size_max=5,
        color_discrete_sequence=px.colors.qualitative.Safe,
        hover_data={
            'Project Address': True, 
            'First Photo Taken': True, 
            'Last Photo Taken': True,
            'Five Year Period': False,
            'weight': False,
            'Current Year': False,
            'lat': False,
            'lon': False
        }
    )

    fig.write_html(DOCS_DIR / "urban_renewal_projects.html")


    fig, axes = plt.subplots(2,3, figsize=(8,8), layout='tight')
    axes = axes.flatten()

    for year, ax in zip(range(1956, 1978, 4), axes):
        filtered = gdf_with_dates[(gdf_with_dates.year >= year)&(gdf_with_dates.year < (year + 4))]
        filtered.plot(
            ax=ax,
            markersize=10
        )

        city_boundary.boundary.plot(ax=ax, lw=0.5, color='black')

        ax.set_title(f'{year} to {year + 3}')
        ax.set_axis_off()

    fig.suptitle('Chicago Urban Renewal Project Locations by Time Period')

    plt.savefig(FIGURES_DIR / 'urban_renewal_locations_by_time_period.png')


if __name__ == '__main__':
    app()


