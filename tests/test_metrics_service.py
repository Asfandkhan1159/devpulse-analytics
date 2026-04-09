from app.services.metrics_services import calculate_frequency_label, calculate_deployment_frequency, calculate_lead_time, calculate_change_failure_rate
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone

def test_calculate_frequency_label():
    assert calculate_frequency_label(0) == "No deployments"
    assert calculate_frequency_label(1.5) == "Multiple Deployments per Day"
    assert calculate_frequency_label(0.2) == "Multiple Deployments per Week"
    assert calculate_frequency_label(0.08) == "Once per Week"
    assert calculate_frequency_label(0.03) == "Once per month"

def test_calculate_deployment_frequency():

    #arrange
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar.return_value = 10  # Mock total deployments
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    #act
    result = calculate_deployment_frequency(project_id=1, cutoff=cutoff, db=mock_db)

    #assert
    assert result["total_deployments"] == 10
    assert result["frequency_label"] == "Multiple Deployments per Week"

def test_calculate_lead_time():
    #arrange
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar.return_value = 5.0  # Mock average lead time in hours
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    #act
    result = calculate_lead_time(project_id=1, db=mock_db, cutoff=cutoff)

    #assert
    # Check that the average lead time is returned correctly
    assert result["average_lead_time_hours"] == 5.0

def test_calculate_change_failure_rate():
    #arrange
    mock_db = MagicMock()
  
    #mock total and  failed deployments
    mock_db.execute.return_value.scalar.side_effect = [20, 10]  # First call returns total deployments, second call returns failed deployments
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    #act
    result = calculate_change_failure_rate(project_id=1, db=mock_db, cutoff=cutoff)
    #assert
    assert result["failure_rate_percentage"] == 50.0  # 10 failed out of 20 total deployments

