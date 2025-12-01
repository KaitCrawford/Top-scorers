from sqlmodel import Field, Session, SQLModel, create_engine


class UserScoreBase(SQLModel):
    """
    This is a model to represent the data for user scores. It is not a table in the database
    """
    first_name: str = Field(index=True)
    second_name: str = Field(index=True)
    score: int = Field(index=True)

class UserScore(UserScoreBase, table=True):
    """
    This is a model to represent the data stored in the database. It is a table in the db
    """
    id: int | None = Field(default=None, primary_key=True)


# Setup the db connection
db_filename = "database.db"
sqlite_url = f"sqlite:///{db_filename}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args, echo=True)

def create_db_and_tables():
    """
    Function to create database and tables
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Function to return the database session object
    """
    with Session(engine) as session:
        yield session

