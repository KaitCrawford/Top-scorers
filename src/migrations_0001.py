from db_utils import create_admin_user, create_db_and_tables

if __name__ == "__main__":
    # All migrations to be applied before inital startup
    create_db_and_tables()
    create_admin_user()
