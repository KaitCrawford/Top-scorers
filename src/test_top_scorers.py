import sys
from unittest import mock

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from .db_utils import UserScore
from .top_scorers import find_highest, handle


@pytest.fixture(name="engine")
def db_session_fixture():
    engine = create_engine(  
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="tmp_file_details")
def tmp_input_file_fixture(tmp_path):
    input = """
First name,Second name,Score
Mark,Jobs,38
Sarah,Pieterson,39
Themba,Mahlala,86
"""
    d = tmp_path / "sub"
    d.mkdir()
    path = d / "input_txt.csv"
    path.write_text(input, encoding="utf-8")
    return {"path": path, "content": input}



def test_find_highest_finds_single_highest(engine):
    input = """
First name,Second name,Score
Mark,Jobs,38
Sarah,Pieterson,39
Themba,Mahlala,86
"""
    with mock.patch("src.top_scorers.engine", new=engine) as engine:
        output = find_highest(input)
    
    assert output[0] == ["Themba Mahlala"]
    assert output[1] == 86


def test_find_highest_finds_multiple_highest(engine):
    input = """
First name,Second name,Score
Mark,Jobs,38
Sarah,Pieterson,86
Themba,Mahlala,86
"""
    with mock.patch("src.top_scorers.engine", new=engine) as engine:
        output = find_highest(input)
    
    assert output[0] == ["Sarah Pieterson","Themba Mahlala"]
    assert output[1] == 86


def test_find_highest_header_row_optional(engine):
    input = """
Mark,Jobs,38
Sarah,Pieterson,39
Themba,Mahlala,86
"""
    with mock.patch("src.top_scorers.engine", new=engine) as engine:
        output = find_highest(input)
    
    assert output[0] == ["Themba Mahlala"]
    assert output[1] == 86


def test_find_highest_ignores_blank_rows(engine):
    input = """
First name,Second name,Score

Mark,Jobs,38


Sarah,Pieterson,39
Themba,Mahlala,86
"""
    with mock.patch("src.top_scorers.engine", new=engine) as engine:
        output = find_highest(input)
    
    assert output[0] == ["Themba Mahlala"]
    assert output[1] == 86


def test_find_highest_adds_all_rows_to_db(engine):
    input = """
First name,Second name,Score
Sarah,Pieterson,39
Themba,Mahlala,86
"""
    with mock.patch("src.top_scorers.engine", new=engine) as engine:
        find_highest(input)

    with Session(engine) as session:
        results = session.exec(select(UserScore)).all()

    assert 2 == len(results)
    assert "Sarah" == results[0].first_name
    assert "Themba" == results[1].first_name


@mock.patch('src.top_scorers.find_highest')
def test_script_errors_without_input(mock_method, capsys):
    sys.argv = ["top_scorers.py"]

    with pytest.raises(SystemExit) as e:
        handle()

    mock_method.assert_not_called()
    
    assert e.type == SystemExit
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == "Invalid Arguments: Please provide an input file\n"


@mock.patch('src.top_scorers.find_highest')
def test_script_reads_input_from_arg(mock_method, tmp_file_details, capsys):
    sys.argv = ["top_scorers.py", tmp_file_details["path"]]

    mock_method.return_value = (["Sarah Pieterson"], 35)

    handle()

    mock_method.assert_called_once_with(tmp_file_details["content"])
    
    captured = capsys.readouterr()
    assert captured.out == "Sarah Pieterson\nScore: 35\n"


@mock.patch('src.top_scorers.find_highest')
def test_script_orders_multiple_alphabetically(mock_method, tmp_file_details, capsys):
    sys.argv = ["top_scorers.py", tmp_file_details["path"]]

    mock_method.return_value = (["Sarah Pieterson", "Andre Williams"], 35)

    handle()

    mock_method.assert_called_once_with(tmp_file_details["content"])
    
    captured = capsys.readouterr()
    assert captured.out == "Andre Williams Sarah Pieterson\nScore: 35\n"


@mock.patch('src.top_scorers.find_highest')
def test_script_writes_to_given_output_file(
        mock_method, tmp_file_details, capsys, tmp_path
    ):
    d = tmp_path / "sub"
    out_path = d / "output.txt"

    sys.argv = ["top_scorers.py", tmp_file_details["path"], out_path]

    mock_method.return_value = (["Sarah Pieterson"], 35)

    handle()

    mock_method.assert_called_once_with(tmp_file_details["content"])
    
    captured = capsys.readouterr()
    assert captured.out == ""
    
    assert out_path.read_text(encoding="utf-8") == "Sarah Pieterson\nScore: 35"
