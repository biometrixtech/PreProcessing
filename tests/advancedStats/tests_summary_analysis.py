import app.advancedStats.summary_analysis as calc


def test_get_unit_blocks():

    collection = ""
    athlete = ""
    date = ""
    output_path = ""

    calc.query_mongo_ub(collection, athlete, date, output_path)


def test_get_active_blocks():
    collection = ""
    athlete = ""
    date = ""
    output_path = ""

    calc.query_mongo_ab(collection, athlete, date, output_path)