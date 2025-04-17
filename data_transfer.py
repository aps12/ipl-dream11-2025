from sqlalchemy import create_engine, MetaData, Table, Column, Integer
from sqlalchemy.schema import CreateTable
import sqlalchemy.types as sqltypes
import pandas as pd

# Connect to PostgreSQL and SQLite
pg_engine = create_engine("postgresql://ipl_pg_db_user:ouTA3DieDxXwVMxg0VIfoRWMlwhZf8Gk@dpg-cvh737jv2p9s7382os50-a.oregon-postgres.render.com/ipl_pg_db")
sqlite_engine = create_engine("sqlite:///instance/ipl_db.sqlite")

# Reflect metadata from PostgreSQL
pg_meta = MetaData()
pg_meta.reflect(bind=pg_engine)  # Load schema (tables, constraints, etc.) from PostgreSQL

# Create a fresh SQLite database schema
sqlite_meta = MetaData()

# Establish a connection for schema creation
with sqlite_engine.connect() as connection:
    sqlite_meta.reflect(bind=connection)  # Load existing SQLite metadata
    for table_name in pg_meta.tables:
        if table_name in sqlite_meta.tables:
            print(f"Table {table_name} already exists in SQLite. Skipping creation.")
            continue

        pg_table = pg_meta.tables[table_name]
        sqlite_columns = []

        for col in pg_table.columns:
            # Handle autoincrement columns properly for SQLite
            if col.autoincrement and isinstance(col.type, Integer):
                sqlite_columns.append(Column(col.name, Integer, primary_key=True, autoincrement=True))
            else:
                # Copy column properties without using col.copy() (manually replicate)
                sqlite_columns.append(
                    Column(
                        col.name,
                        col.type if not isinstance(col.type, sqltypes.NullType) else sqltypes.Text,
                        primary_key=col.primary_key,
                        nullable=col.nullable,
                        default=col.default,
                    )
                )

        # Create the SQLite table schema
        sqlite_table = Table(table_name, sqlite_meta, *sqlite_columns)
        connection.execute(CreateTable(sqlite_table))  # Execute table creation in SQLite
        print(f"Created table {table_name} in SQLite.")

# Copy data from PostgreSQL to SQLite
for table_name in pg_meta.tables:
    print(f"Transferring data for table: {table_name}")
    # Fetch data from PostgreSQL using pandas
    df = pd.read_sql_table(table_name, pg_engine)

    # Convert datetime values to date values before inserting into SQLite (if required)
    if table_name == "match":  # Use specific table name for date column adjustment
        if "match_date" in df.columns:  # Replace 'match_date' with your column's name
            df["match_date"] = pd.to_datetime(df["match_date"]).dt.date

    # Insert data into newly created SQLite tables
    df.to_sql(table_name, sqlite_engine, if_exists="append", index=False)
    print(f"Copied data for table: {table_name}")