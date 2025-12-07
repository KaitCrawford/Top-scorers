import hashlib
import os

from sqlmodel import Field, Session, SQLModel, create_engine, func, select


class UserScoreBase(SQLModel):
    """
    This is a model to represent the data for user scores. It is not a table in the
    database
    NOTE: We could add a UniqueConstraint across first_name and second_name to prevent
    duplicate users. For now we just handle that when inserting rows
    """
    first_name: str = Field(index=True)
    second_name: str = Field(index=True)
    score: int = Field(index=True)

class UserScore(UserScoreBase, table=True):
    """
    This is a model to represent the data stored in the database. It is a table in the db
    """
    id: int | None = Field(default=None, primary_key=True)


class AdminUser(SQLModel, table=True):
    """
    This is a model to be used for basic authentication
    """
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    password_hash: bytes = Field()
    salt: bytes = Field()


# Setup the db connection
# NOTE: We should handle connection errors here
# This should probably be in a settings file of some sort
db_filename = "database.db"
sqlite_url = f"sqlite:///{db_filename}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

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

def create_or_update_user_score(new_user_score: UserScoreBase, session: Session):
    """
    Function that adds new users and updates the score of existing users.
    This accepts the UserScoreBase object to add and Session object
    Returns the new/updated object
    """
    # NOTE: We take in the session object here so that the calling code can determine
    # how the session should be managed.

    # Check for users with the same names in the database
    sql_expr_obj = select(UserScore).where(
        func.lower(UserScore.first_name) == new_user_score.first_name.lower(),
        func.lower(UserScore.second_name) == new_user_score.second_name.lower()
    )
    user_scores = session.exec(sql_expr_obj).all()

    if len(user_scores) > 0:
        # The user does exist, so update it
        # NOTE: We're ignoring the situation where there's more than 1 row but it would
        # be better to handle it since they might have been created by something else
        # NOTE: It's more efficient not to update the row if the score is the same
        # (Depends on context, if we were storing modified times it might makes sense
        # to touch the row even if the score is the same)
        user_scores[0].score = new_user_score.score
        new_user_score = user_scores[0]
    session.add(new_user_score)
    session.commit()
    return new_user_score


def create_admin_user():
    # NOTE: This is terrible. Having a username and password in the code is a bad idea
    # but auth is already somewhat out of scope, so I've taken a short-cut
    uname = "admin"
    pw = "admin"
    salt = os.urandom(16)

    hashed_pw = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, 100000)
    admin_user = AdminUser(username=uname, password_hash=hashed_pw, salt=salt)
    with Session(engine) as session:
        session.add(admin_user)
        session.commit()
