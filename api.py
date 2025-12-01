from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select, func

from db_models import UserScoreBase, UserScore, get_session


app = FastAPI()

# SqlAlchemy and SQLModel use sessions to manage queries to the database. This line
# creates a Dependancy object that we can use with FastAPI's dependency injection to
# provide a DB session during the requests. 
SessionDep = Annotated[Session, Depends(get_session)]

@app.get("/", response_model=list[UserScoreBase])
def show_all(session: SessionDep) -> list[UserScore]:
    """
    Displays all the users with scores in the database.
    NOTE: It would be good to add pagination to this endpoint.
    """
    user_scores = session.exec(select(UserScore)).all()
    return user_scores


@app.post("/user_scores/", response_model=UserScoreBase)
def create_or_update_user_score(
        user_score: UserScoreBase, session: SessionDep
    ) -> UserScoreBase:
    """
    Add a new user's score to the db or update an existing score
    NOTE: A good feature to add here would be a flag that indicates if we should replace or
    ignore scores for exising users
    """
    # TODO: replace scores for existing users
    db_user_score = UserScore.model_validate(user_score)
    session.add(db_user_score)
    session.commit()
    session.refresh(db_user_score)
    return db_user_score


@app.get("/user_scores/", response_model=UserScoreBase)
def get_score_for_user(first_name: str, second_name: str, session: SessionDep) -> UserScore:
    """
    Return the info for the user corresponding to first_name and second_name.
    """
    sql_expr_obj = select(UserScore).where(
        func.lower(UserScore.first_name) == first_name.lower(),
        func.lower(UserScore.second_name) == second_name.lower()
    ) 
    user_scores = session.exec(sql_expr_obj).all()
    if len(user_scores) < 1:
        raise HTTPException(
            status_code=404,
            detail=f"No score found for first_name: {first_name}, second_name: {second_name}"
        )
    if len(user_scores) > 1:
        # NOTE: Opting to raise a 500 here since we shouldn't have multiple rows with
        # these details if we're updating scores instead of creating new ones.
        raise HTTPException(status_code=500, detail="Server Error")
    return user_scores[0]


@app.get("/top_scorers/", response_model=list[UserScoreBase])
def get_highest_scoring_users(session: SessionDep):
    """
    Return the info for users with the highest scores.
    """
    # Write a subquery to get the max score and use that in the where clause
    sql_subquery = select(func.max(UserScore.score)).scalar_subquery()
    sql_expr_obj = select(UserScore).where(UserScore.score == sql_subquery)
    user_scores = session.exec(sql_expr_obj).all()
    return user_scores
