1. clone repo
2. Create ve
3. activate ve
4. pip install -r requirements.txt
5. python migrations_0001.py
6. to run program: python top_scorers.py input_file.csv
7. to run api: fastapi run

- GET "/" shows all scores in the database
- GET "/user_scores/?first_name=<first name>&second_name=<second name>" shows the details in the db for the user with the given first name and second name (case insensitive, 404 if none exists)
- GET "/top_scorers/" shows the details of all users with the highest score
- POST "/user_scores/" with json body of {"first_name": "<str>", "second_name": "<str>", "score": <int>} will create or update the given user score in the database

Notes:
Example authentication implementation is commented out in the api.py file.
The top_scorers.py script only returns the max score of the users in the given input file, rows in the database are not considered.
Adding a score with the same first name and second name as an existing row will update the existing row, not create a new row. This check is case insensitive. This behaviour is consistent regardless of if the score is added using the script or the api endpoint
More notes can be found in comments starting with "NOTE"

