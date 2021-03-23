import os
import shutil
import sqlite3
import argparse
import pandas as pd
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt

from website import create_app
from website.extensions import db
from website.models import Cluster, Region

from shapely.geometry.multipolygon import MultiPolygon
from tqdm.contrib.concurrent import process_map

CLUSTER_ID = -1


def next_cluster_id():
    global CLUSTER_ID

    CLUSTER_ID += 1

    return CLUSTER_ID


def choose_column(df):
    id_candidates = df.select_dtypes(exclude=['geometry']).columns
    id_candidates = [x for x in id_candidates if df[x].is_unique]
    longest = max([len(x) for x in id_candidates])

    print('--\tColumn Name\tExample')
    for i, col in enumerate(id_candidates):
        print('{})\t{:<{longest}}\t{}'.format(i,
                                              col,
                                              df.iloc[0][col],
                                              longest=longest))

    choice = input('Please choose the ID column to use [0-{}]: '.format(
        len(id_candidates) - 1))

    try:
        choice = id_candidates[int(choice)]
        return choice
    except:
        print('Invalid choice')

    return None


def load_shapefile(args):
    print('Loading Shapefile')
    df = gpd.read_file(args.shapefile)
    df = df.to_crs(epsg=3857)

    # Identify geometry column which must exists and be unique
    col_geom = df.select_dtypes(include=['geometry']).columns
    assert len(col_geom) == 1
    col_geom = col_geom[0]

    # Choose ID column
    print(
        '\nYou need to choose a column as unique identifier of your regions, potential candidates are:'
    )
    col_idx = None
    while col_idx is None:
        col_idx = choose_column(df)

    # Choose label column
    print(
        '\n\n\nYou need to choose a column containg the label / name of each region, potential candidates are:'
    )
    col_label = None
    while col_label is None:
        col_label = choose_column(df)

    print('\n\n\nSummary of selected columns:')
    print('\t[ID] {}'.format(col_idx))
    print('\t[Label] {}'.format(col_label))
    print('\t[Geometry] {}'.format(col_geom))

    #df.set_index(col_idx, inplace=True)
    df.rename(columns={col_idx: 'chosen_id', col_label: 'name'}, inplace=True)
    df.reset_index(inplace=True)
    df.index = df.index + 1

    return df[['chosen_id', 'name', col_geom]]


def generate_region_images(df_row):
    row = df_row.iloc[0]
    (minx, miny, maxx, maxy) = row.geometry.bounds

    cx = row.geometry.centroid.x
    cy = row.geometry.centroid.y

    dx = (maxx - minx)
    dy = (maxy - miny)

    if dx > dy:
        padding = dx // 2 + dx // 8
    else:
        padding = dy // 2 + dy // 8

    fig, ax = plt.subplots()

    ax.set_xlim((cx - padding, cx + padding))
    ax.set_ylim((cy - padding, cy + padding))

    df_row.plot(ax=ax, facecolor="none", edgecolor="red", lw=1)
    ctx.add_basemap(ax,
                    crs=df_row.geometry.crs.to_string(),
                    source=ctx.providers.Esri.NatGeoWorldMap,
                    attribution='')
    plt.axis('off')

    plt.savefig(f'website/static/maps/region_{df_row.index.to_list()[0]}.png',
                dpi=200,
                bbox_inches='tight',
                pad_inches=0)

    plt.close(fig)


def generate_cluster_images(data):
    df, extent = data
    minx, miny, maxx, maxy = extent
    cluster_id = df.iloc[0]['cluster_id']

    cx = int((minx + maxx) / 2)
    cy = int((miny + maxy) / 2)

    dx = (maxx - minx)
    dy = (maxy - miny)

    if dx > dy:
        padding = dx // 2 + dx // 8
    else:
        padding = dy // 2 + dy // 8

    fig, ax = plt.subplots()

    ax.set_xlim((cx - padding, cx + padding))
    ax.set_ylim((cy - padding, cy + padding))


    df = df.dissolve(by='cluster_id')

    df.plot(ax=ax, facecolor="none", edgecolor="red", lw=1)
    ctx.add_basemap(ax, 
            source=ctx.providers.Esri.NatGeoWorldMap,
            crs=df.crs.to_string(), 
            attribution='')  #, zoom=12)
    plt.axis('off')

    plt.savefig(f'website/static/maps/cluster_{cluster_id}.png',
                dpi=300,
                bbox_inches='tight',
                pad_inches=0)

    plt.close(fig)


def run_clustering(df):
    # Extract centroids
    df['X'] = df.centroid.x
    df['Y'] = df.centroid.y

    # Aiming for 10 clusters
    cluster_size = len(df) // 10

    # If small dataset, go for clusters of 5 regions instead
    cluster_size = max(cluster_size, 5)

    # If large dataset, go for clusters of 25 regions instead
    cluster_size = min(cluster_size, 25)

    df['cluster_id'] = -1

    # Extract convex hulls as simplified geometries
    islands = df.convex_hull.unary_union

    # Convert MultiPolygon into list of Polygons
    if type(islands) == MultiPolygon:
        islands = list(islands)
    else:
        islands = [islands]

    # Create a GeoDataFrame and set CRS
    islands = gpd.GeoSeries(islands, crs=df.crs)

    for island in islands:
        mask = df.centroid.within(island)
        if len(df[mask]) <= cluster_size:
            df.loc[mask, 'cluster_id'] = next_cluster_id()
        else:
            # Partition space by vertical and horizontal half splits
            df[mask] = split_in_half(df[mask], cluster_size)

    df.to_file("clusters.shp")
    return df


def split_in_half(df, max_cluster_size):
    range_x = df.X.max() - df.X.min()
    range_y = df.Y.max() - df.Y.min()

    column = 'X' if range_x > range_y else 'Y'

    mask = df[column] < df[column].median()

    g1 = df[mask]
    g2 = df[~mask]

    if len(g1) > max_cluster_size:
        df1 = split_in_half(g1.copy(deep=False), max_cluster_size)
        df2 = split_in_half(g2.copy(deep=False), max_cluster_size)
        return pd.concat([df1, df2])

    df.loc[g1.index, 'cluster_id'] = next_cluster_id()
    df.loc[g2.index, 'cluster_id'] = next_cluster_id()
    return df


def create_database(dataframe):
    app = create_app()

    with app.app_context():

        # TODO Check if database already exists (sqlalchemy-utils) and warn user before deleting
        db.drop_all()
        db.create_all()

        for c_id in dataframe['cluster_id'].unique():
            c = Cluster(id=int(c_id), name=f'Cluster {c_id}')
            db.session.add(c)

        for i, row in dataframe.iterrows():
            r = Region(id=i,
                       shapefile_id=row['chosen_id'],
                       name=row['name'],
                       cluster_id=row['cluster_id'])
            db.session.add(r)
        db.session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        'Create clusters and images for a Shapefile containg the regions of interest'
    )
    # Positional arguements
    parser.add_argument('shapefile',
                        metavar='shapefile',
                        type=str,
                        help='a Shapefile containg regions to be surveyed')

    # Optional arguments
    parser.add_argument('--disable-clustering',
                        action='store_true',
                        default=False)
    parser.add_argument('--max-cluster-size', action='store', default=5)

    args = parser.parse_args()
    print('\n\n\n')

    # Create output directory
    if os.path.exists('website/static/maps'):
        # TODO Add warning / confirmation about emptying folder
        shutil.rmtree('website/static/maps')
    os.mkdir('website/static/maps')

    # Load Shapefile
    df = load_shapefile(args)

    # Check if clustering should be applied
    if len(df) > 25 and not args.disable_clustering:
        df = run_clustering(df)

        # Generate cluster images with full extent
        extent = df.geometry.total_bounds
        clusters = []
        for i in df['cluster_id'].unique():
            c = df[df['cluster_id'] == i]
            clusters.append([c, extent])

        print('Generating images for clusters')
        process_map(generate_cluster_images, clusters)
    else:
        df['cluster_id'] = 0

        if len(df) > 50:
            print(
                'Shapefile contains {} regions, pre-filtering stage is recommended but was disabled!'
                .format(len(df)))

    # Generate images for individual regions
    print('\nGenerating images for individual regions')
    regions = [df.loc[[i]] for i in df.index]
    process_map(generate_region_images, regions)

    # TODO Check all images were properly generated, maybe a simple file count?

    # Create Sqlite3 database
    create_database(df)
