import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from .api import app, get_session
from .db_utils import UserScore


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


# Test fixture to manage the client and connect to the DB session
@pytest.fixture(name="client")  
def client_fixture(session: Session):  
    def get_session_override():  
        return session

    app.dependency_overrides[get_session] = get_session_override  

    client = TestClient(app)  
    yield client  
    app.dependency_overrides.clear()


def test_root_with_no_scores(session: Session, client: TestClient):
    response = client.get("/")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []


def test_root_lists_scores(session: Session, client: TestClient):
    # Setup existing users
    score_1 = UserScore(first_name="first", second_name="user", score=25)
    score_2 = UserScore(first_name="second", second_name="user", score=10)
    score_3 = UserScore(first_name="third", second_name="user", score=5)
    session.add(score_1)
    session.add(score_2)
    session.add(score_3)
    session.commit()

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == [
        {"first_name": "first", "second_name": "user", "score": 25},
        {"first_name": "second", "second_name": "user", "score": 10},
        {"first_name": "third", "second_name": "user", "score": 5},
    ]


def test_post_score_new_user(session: Session, client: TestClient):
    response = client.post(
        "/user_scores/", json={
            "first_name": "first", "second_name": "user", "score": 13
        }
    )

    # Assert API response
    assert response.status_code == 200
    assert response.json() == {
        "first_name": "first", "second_name": "user", "score": 13
    }

    # Assert added to DB
    [db_score] = session.exec(select(UserScore)).all()
    assert db_score.first_name == "first"
    assert db_score.second_name == "user"
    assert db_score.score == 13


def test_post_score_exising_user(session: Session, client: TestClient):
    score_1 = UserScore(first_name="first", second_name="user", score=25)
    session.add(score_1)
    session.commit()

    response = client.post(
        "/user_scores/", json={
            "first_name": "first", "second_name": "user", "score": 13
        }
    )

    # Assert API response
    assert response.status_code == 200
    assert response.json() == {
        "first_name": "first", "second_name": "user", "score": 13
    }

    # Assert changed in to DB
    [db_score] = session.exec(select(UserScore)).all()
    assert db_score.first_name == "first"
    assert db_score.second_name == "user"
    assert db_score.score == 13


def test_post_score_exising_user_case_insensitive(
        session: Session, client: TestClient
    ):
    score_1 = UserScore(first_name="first", second_name="user", score=25)
    session.add(score_1)
    session.commit()

    response = client.post(
        "/user_scores/", json={
            "first_name": "First", "second_name": "UseR", "score": 13
        }
    )

    # Assert API response
    assert response.status_code == 200
    assert response.json() == {
        "first_name": "first", "second_name": "user", "score": 13
    }

    # Assert changed in to DB
    [db_score] = session.exec(select(UserScore)).all()
    assert db_score.first_name == "first"
    assert db_score.second_name == "user"
    assert db_score.score == 13


def test_post_score_invalid_data(client: TestClient):
    response = client.post(
        "/user_scores/", json={
            "firstname": "first", "second_name": "user", "score": 25
        }
    )

    # Assert API response
    assert response.status_code == 422


def test_post_score_no_data(client: TestClient):
    response = client.post(
        "/user_scores/", json={}
    )

    # Assert API response
    assert response.status_code == 422


def test_get_score_for_given_user(session: Session, client: TestClient):
    # Setup existing users
    score_1 = UserScore(first_name="first", second_name="user", score=25)
    score_2 = UserScore(first_name="second", second_name="user", score=10)
    session.add(score_1)
    session.add(score_2)
    session.commit()

    response = client.get(
        f"/user_scores/?first_name={score_1.first_name}&second_name={score_1.second_name}"
    )
    assert response.status_code == 200
    assert response.json() == {
        "first_name": "first", "second_name": "user", "score": 25
    }


def test_get_score_for_invalid_user(session: Session, client: TestClient):
    # Setup existing users
    score_1 = UserScore(first_name="first", second_name="user", score=25)
    score_2 = UserScore(first_name="second", second_name="user", score=10)
    session.add(score_1)
    session.add(score_2)
    session.commit()

    response = client.get(f"/user_scores/?first_name=third&second_name=user")
    assert response.status_code == 404


def test_get_top_scorers_single(session: Session, client: TestClient):
    # Setup existing users
    score_1 = UserScore(first_name="first", second_name="user", score=25)
    score_2 = UserScore(first_name="second", second_name="user", score=10)
    session.add(score_1)
    session.add(score_2)
    session.commit()

    response = client.get(f"/top_scorers/")
    assert response.status_code == 200
    assert response.json() == [{
        "first_name": "first", "second_name": "user", "score": 25
    }]


def test_get_top_scorers_multiple(session: Session, client: TestClient):
    # Setup existing users
    score_1 = UserScore(first_name="first", second_name="user", score=25)
    score_2 = UserScore(first_name="second", second_name="user", score=10)
    score_3 = UserScore(first_name="third", second_name="user", score=25)
    session.add(score_1)
    session.add(score_2)
    session.add(score_3)
    session.commit()

    response = client.get(f"/top_scorers/")
    assert response.status_code == 200
    assert response.json() == [
        {"first_name": "first", "second_name": "user", "score": 25},
        {"first_name": "third", "second_name": "user", "score": 25}
    ]
