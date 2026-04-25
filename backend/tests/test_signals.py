import pytest
from app.services.analysis import calculate_disparity_ratios

def test_calculate_disparity_ratios_logic():
    # Datos de prueba: El grupo 'Black' tiene 60 casos, 'White' tiene 40. 
    # Total = 100. Promedio = 50.
    # Ratio Black = 60/50 = 1.2x (Debería generar señal)
    mock_records = [
        {"race_ethnicity": "Black", "count": 60},
        {"race_ethnicity": "White", "count": 40}
    ]
    
    signals = calculate_disparity_ratios(mock_records)
    
    assert len(signals) > 0
    assert signals[0]["signal_type"] == "disparity_ratio"
    assert signals[0]["metadata"]["ratio"] == 1.2
    assert "Black" in signals[0]["description"]

def test_calculate_disparity_no_data():
    assert calculate_disparity_ratios([]) == []