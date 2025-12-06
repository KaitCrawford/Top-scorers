import sys

from sqlmodel import Session

from .db_utils import UserScore, create_or_update_user_score, engine


def find_highest(input: str):
    """
    Takes csv formatted input of user names and scores and returns list of all users
    with the highest score. Each line in input is "First Name,Second Name,Score"
    Outputs tupple with highest score and list of names with that store.
    Each unique First Name, Second Name pair is stored in the database
    """
    highest_scorers = []
    highest_score = 0
    users = input.split("\n")

    with Session(engine) as session:
        for line in users:
            # Skip empty lines or the header line
            if line == "":
                continue
            if line.lower().find("first name") >= 0:
                continue

            details = line.split(",")

            # Add row to db
            db_object = UserScore(first_name=details[0], second_name=details[1], score=int(details[2]))
            create_or_update_user_score(db_object, session)

            # Find highest scorers
            user_score = int(details[2])
            if user_score == highest_score:
                # This score is one of the highest, append this user's info
                highest_scorers.append(f"{details[0]} {details[1]}")
                continue
            if user_score > highest_score:
                # This score is higher than previous highest
                # So update all the information with the new highest
                highest_scorers = [f"{details[0]} {details[1]}"]  # Overwrite the list
                highest_score = user_score

    return (highest_scorers, highest_score)


def handle():
    """
    Handles the program opperation. Loads specified file and writes output
    """
    try:
        input_file = sys.argv[1]
        with open(input_file, "r") as f:
            input = f.read()
    except (FileNotFoundError, IndexError):
        print("Invalid Arguments: Please provide an input file")
        sys.exit(1)

    (highest_users, highest_score) = find_highest(input)

    output = ""
    # Sort the users alphabetically
    sorted_users = sorted(highest_users)
    counter = 0
    for name in sorted_users:
        output += f"{name}"
        if counter != len(sorted_users):
            output += " "
            counter += 1

    output += f"\nScore: {highest_score}"

    try:
        output_file = sys.argv[2]
        with open(output_file, "w") as f:
            f.write(output)
    except (PermissionError, IndexError):
        print(output)


if __name__ == "__main__":
    handle()


"""
Assumptions:
- When running this program, only the scores in the input file should be considered
    for the top scores (values in the database are excluded)

Changes to make this reusable/production ready:
- (Done) Don't hard code the default input. Return a helpful error
- Unit tests
- Use python's csv lib (using built-in lib reduces risk of errors)
- Use typer and typing_extensions libs to annotate params with useful help text
    - This would also simplify proper documention and validation of input parameters
- Package as an app to improve usability/sharability and lib dependancy management
- Consider wider context and reusablity
    - eg Decoupling the csv processing from the logic to find the highest scores would
    enable that logic to be used regardless of input format
"""
