from db_utils import create_db_and_tables


if __name__ == "__main__":
    # All migrations to be applied before inital startup
    create_db_and_tables()
