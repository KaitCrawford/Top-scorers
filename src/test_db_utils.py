import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from .db_utils import UserScore, create_or_update_user_score


# Test fixture to manage the db session
# Using in-mem DB for tests
@pytest.fixture(name="session")
def db_session_fixture():
    engine = create_engine(  
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_or_update_with_new_user(session: Session):
    user_score = UserScore(first_name="first", second_name="user", score=25)

    create_or_update_user_score(user_score, session)

    # Assert added to DB
    [db_score] = session.exec(select(UserScore)).all()
    assert db_score.first_name == "first"
    assert db_score.second_name == "user"
    assert db_score.score == 25


def test_create_or_update_with_existing_user(session: Session):
    score_1 = UserScore(first_name="first", second_name="user", score=25)
    session.add(score_1)
    session.commit()
    user_score = UserScore(first_name="first", second_name="user", score=13)

    create_or_update_user_score(user_score, session)

    # Assert added to DB
    [db_score] = session.exec(select(UserScore)).all()
    assert db_score.first_name == "first"
    assert db_score.second_name == "user"
    assert db_score.score == 13


def test_create_or_update_with_existing_user_insensitive(session: Session):
    score_1 = UserScore(first_name="first", second_name="user", score=25)
    session.add(score_1)
    session.commit()
    user_score = UserScore(first_name="FiRsT", second_name="User", score=13)

    create_or_update_user_score(user_score, session)

    # Assert added to DB
    [db_score] = session.exec(select(UserScore)).all()
    assert db_score.first_name == "first"
    assert db_score.second_name == "user"
    assert db_score.score == 13
