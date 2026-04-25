from app.services.analysis import calculate_disparity_ratios


def test_calculate_disparity_ratios_logic():
    mock_records = [
        {"race_ethnicity": "Black", "count": 60},
        {"race_ethnicity": "White", "count": 40},
    ]
    signals = calculate_disparity_ratios(mock_records)

    assert len(signals) > 0
    assert signals[0]["signal_type"] == "disparity"
    assert signals[0]["metadata"]["ratio"] == 1.2
    assert "Black" in signals[0]["description"]


def test_calculate_disparity_no_data():
    assert calculate_disparity_ratios([]) == []
