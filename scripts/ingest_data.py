import os
import sys
import pandas as pd
import geopandas as gpd

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.session import engine
from app.models.base import Base
# Make sure models are loaded for create_all to see them
import app.models.link
import app.models.speed_record

def get_time_period(hour: int) -> str:
    """Map an hour (0-23) to a time period bucket."""
    if 0 <= hour <= 3:
        return 'Overnight'
    elif 4 <= hour <= 6:
        return 'Early Morning'
    elif 7 <= hour <= 9:
        return 'AM Peak'
    elif 10 <= hour <= 12:
        return 'Midday'
    elif 13 <= hour <= 15:
        return 'Early Afternoon'
    elif 16 <= hour <= 18:
        return 'PM Peak'
    else:
        return 'Evening'

def ingest_links(filepath: str):
    """Ingest spatial Link geometries and attributes."""
    import json
    from shapely.geometry import shape
    
    print(f"Reading {filepath} with Pandas...")
    df = pd.read_parquet(filepath)
    
    print("Mapping columns and parsing geometries...")
    links_df = pd.DataFrame()
    
    # Map the primary key
    links_df['id'] = df['link_id'] if 'link_id' in df.columns else df['id']
    
    # Map road_name
    if 'road_name' in df.columns:
        links_df['road_name'] = df['road_name']
        
    # Map length (the terminal showed it as '_length')
    if '_length' in df.columns:
        links_df['length'] = df['_length']
    elif 'length' in df.columns:
        links_df['length'] = df['length']
        
    def extract_linestring(geo_json_str):
        if pd.isna(geo_json_str) or not geo_json_str:
            return None
        try:
            geom = shape(json.loads(geo_json_str))
            # The database column strictly expects a LINESTRING.
            if geom.geom_type == 'MultiLineString':
                # Take the first segment to fulfill the LINESTRING requirement
                # Alternatively, one could use shapely.ops.linemerge(geom) to combine segments into a single LineString if they are contiguous
                geom = list(geom.geoms)[0]
            if geom.geom_type != 'LineString':
                return None
            return geom.wkt
        except Exception as e:
            return None
            
    # Parse the GeoJSON string into Shapely, convert MultiLineString -> LineString -> WKT
    if 'geo_json' in df.columns:
        links_df['geometry'] = df['geo_json'].apply(extract_linestring)
        
    # Drop rows where geometry extraction failed or is None, since geometry is likely required
    initial_len = len(links_df)
    links_df = links_df.dropna(subset=['geometry'])
    print(f"Dropped {initial_len - len(links_df)} rows with invalid or missing geometries.")
        
    print(f"Inserting {len(links_df)} Links into PostgreSQL...")
    links_df.to_sql('links', engine, if_exists='append', index=False)
    print("Links successfully ingested.")

def ingest_speeds(filepath: str):
    """Ingest temporal speed records, mapping time periods dynamically."""
    print(f"Reading {filepath} with Pandas...")
    df = pd.read_parquet(filepath)
    
    print("Cleaning and transforming timestamps...")
    # Map the actual parquet columns to our database schema
    df.rename(columns={'date_time': 'timestamp', 'average_speed': 'speed'}, inplace=True)
    
    # Convert abstract strings to pandas datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Handle Timezones safely: PostGIS / SQLAlchemy prefers timezone-aware UTC datetime.
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
        
    # Vectorized execution for deriving 'day_of_week' as a string ('Monday', 'Tuesday' ...)
    df['day_of_week'] = df['timestamp'].dt.day_name()
    
    # Map the hour integer to the categorical bucket logic
    hours = df['timestamp'].dt.hour
    df['time_period'] = hours.apply(get_time_period)
    
    # Keep only the columns defined in our SQLAlchemy `SpeedRecord` model
    speeds_df = df[['link_id', 'timestamp', 'speed', 'day_of_week', 'time_period']]
    
    print(f"Inserting {len(speeds_df)} SpeedRecords into PostgreSQL. This might take a moment...")
    
    # chunksize=10000 and method='multi' uses a bulk INSERT syntax spanning multiple rows
    speeds_df.to_sql('speed_records', engine, if_exists='append', index=False, chunksize=10000, method='multi')
    print("SpeedRecords successfully ingested.")

def main():
    print("Ensuring database tables match models...")
    Base.metadata.create_all(bind=engine)
    
    links_path = "link_info.parquet.gz"
    speeds_path = "duval_jan1_2024.parquet.gz"
    
    if os.path.exists(links_path):
        ingest_links(links_path)
    else:
        print(f"ERROR: {links_path} not found in root directory!")
        
    if os.path.exists(speeds_path):
        ingest_speeds(speeds_path)
    else:
        print(f"ERROR: {speeds_path} not found in root directory!")

if __name__ == "__main__":
    main()
