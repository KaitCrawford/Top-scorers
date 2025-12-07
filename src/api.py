import hashlib
import hmac
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, func, select

from .db_utils import (AdminUser, UserScore, UserScoreBase,
                       create_or_update_user_score, get_session)

app = FastAPI()

# SqlAlchemy and SQLModel use sessions to manage queries to the database. This line
# creates a Dependancy object that we can use with FastAPI's dependency injection to
# provide a DB session during the requests. 
SessionDep = Annotated[Session, Depends(get_session)]

# Uncomment the sections below for basic bearer authentication
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
#
# def get_user_from_token(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep):
#     sql_expr_obj = select(AdminUser).where(AdminUser.username == token)
#     admin_user = session.exec(sql_expr_obj).one()
#     return admin_user


@app.get("/", response_model=list[UserScoreBase])
def show_all(session: SessionDep) -> list[UserScore]:
    """
    Displays all the users with scores in the database.
    NOTE: It would be good to add pagination to this endpoint.
    """
    user_scores = session.exec(select(UserScore)).all()
    return user_scores


@app.post("/user_scores/", response_model=UserScoreBase)
def post_user_score(
        user_score: UserScoreBase, session: SessionDep
    ) -> UserScore:
    """
    Add a new user's score to the db or update an existing score
    NOTE: A good feature to add here would be a flag that indicates if we should replace or
    ignore scores for exising users
    """
    # Check the input data is valid for the model (FastAPI validation should prevent us
    # getting here with invalid data)
    new_user_score = UserScore.model_validate(user_score)
    new_user_score = create_or_update_user_score(new_user_score, session)

    session.refresh(new_user_score)
    return new_user_score


@app.get("/user_scores/", response_model=UserScoreBase)
def get_score_for_user(
        first_name: str, second_name: str, session: SessionDep
    ) -> UserScore:
    """
    Return the info for the user corresponding to first_name and second_name. Case insensitive
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
def get_highest_scoring_users(session: SessionDep) -> list[UserScore]:
    """
    Return the info for users with the highest scores.
    """
    # Write a subquery to get the max score and use that in the where clause
    sql_subquery = select(func.max(UserScore.score)).scalar_subquery()
    sql_expr_obj = select(UserScore).where(UserScore.score == sql_subquery)
    user_scores = session.exec(sql_expr_obj).all()
    return user_scores

# ##################
# Authentication
# For authentication uncomment the section at the top of this file and add the line
# below to the params of all paths
# current_user: Annotated[AdminUser, Depends(get_user_from_token)]

@app.post("/token")
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: SessionDep
    ):
    """
    Authenticates the given username and password against the database
    The returned token will be stored in browswer cookies and sent in the header of
    future requests
    """
    # Get user for username
    sql_expr_obj = select(AdminUser).where(AdminUser.username == form_data.username)
    admin_user = session.exec(sql_expr_obj).one()
    if not admin_user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # Check password
    # This uses hashlib's built in key derivation which is recommended for passwords
    password = form_data.password
    if not hmac.compare_digest(
            admin_user.password_hash,
            hashlib.pbkdf2_hmac('sha256', password.encode(), admin_user.salt, 100000)
        ):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # NOTE: Use a more better token here
    return {"access_token": admin_user.username, "token_type": "bearer"}
