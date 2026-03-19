import json
import pytest
from unittest.mock import patch, MagicMock
from app.models import User, Greenhouse, Device, SensorType, Sensor, SensorReading, ActuatorType, Actuator, Script, ActuatorStatus
from app.automation import check_rule_conditions, process_automation_rules

def test_check_rule_conditions(db_session):
    # Setup test data
    user = User(name="Test", email="test@test.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    
    gh = Greenhouse(user_id=user.id, name="Test GH")
    db_session.add(gh)
    db_session.commit()
    
    device = Device(greenhouse_id=gh.id, name="Test Device")
    db_session.add(device)
    db_session.commit()
    
    st = SensorType(name="temperature")
    db_session.add(st)
    db_session.commit()
    
    sensor = Sensor(device_id=device.id, sensor_type_id=st.id, name="Temp 1")
    db_session.add(sensor)
    db_session.commit()
    
    # Add reading 35
    reading = SensorReading(sensor_id=sensor.id, value=35.0)
    db_session.add(reading)
    db_session.commit()
    
    conditions = [
        {
            "id": "cond1",
            "sensorKeys": [str(sensor.id)],
            "operator": ">",
            "value": "30",
            "joinWithPrevious": "OR"
        }
    ]
    
    result = check_rule_conditions(conditions, db_session)
    assert result is True
    
    # Add new reading 25
    reading2 = SensorReading(sensor_id=sensor.id, value=25.0)
    db_session.add(reading2)
    db_session.commit()
    
    result = check_rule_conditions(conditions, db_session)
    assert result is False

@patch("app.automation.mqtt_client")
def test_process_automation_rules(mock_client, db_session):
    user = User(name="Test2", email="test2@test.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    
    gh = Greenhouse(user_id=user.id, name="Test GH")
    db_session.add(gh)
    db_session.commit()
    
    device = Device(greenhouse_id=gh.id, name="Test Device")
    db_session.add(device)
    db_session.commit()
    
    # Sensor
    st = SensorType(name="temperature")
    db_session.add(st)
    db_session.commit()
    sensor = Sensor(device_id=device.id, sensor_type_id=st.id, name="Temp 1")
    db_session.add(sensor)
    db_session.commit()
    
    # Actuator
    at = ActuatorType(name="fan")
    db_session.add(at)
    db_session.commit()
    actuator = Actuator(device_id=device.id, actuator_type_id=at.id, status=ActuatorStatus.off)
    db_session.add(actuator)
    db_session.commit()
    
    # Script
    rule = {
        "conditions": [
            {
                "id": "cond1",
                "sensorKeys": [str(sensor.id)],
                "operator": ">",
                "value": "30",
                "joinWithPrevious": "OR"
            }
        ],
        "actuatorKeys": [str(actuator.id)],
        "command": "on"
    }
    
    script = Script(
        greenhouse_id=gh.id,
        name="Auto Fan",
        script_code=json.dumps(rule),
        enabled=True
    )
    db_session.add(script)
    db_session.commit()
    
    # Mock MQTT client
    mock_client.connected = True
    
    # Scenario 1: Temperature is 35 (> 30). Should turn ON.
    db_session.add(SensorReading(sensor_id=sensor.id, value=35.0))
    db_session.commit()
    
    process_automation_rules(gh.id, db_session)
    
    # Check if actuator turned on
    db_session.refresh(actuator)
    assert actuator.status == ActuatorStatus.on
    mock_client.publish.assert_called_with(f"cmd/{device.id}/{at.name}", '{"command": "on"}')
    
    mock_client.publish.reset_mock()
    
    # Scenario 2: Call again with temp 35. Should not spam/repeat.
    db_session.add(SensorReading(sensor_id=sensor.id, value=35.0))
    db_session.commit()
    process_automation_rules(gh.id, db_session)
    mock_client.publish.assert_not_called()
    
    # Scenario 3: Temperature drops to 25. Rule fails -> automatic rollback (OFF).
    db_session.add(SensorReading(sensor_id=sensor.id, value=25.0))
    db_session.commit()
    
    process_automation_rules(gh.id, db_session)
    
    db_session.refresh(actuator)
    assert actuator.status == ActuatorStatus.off
    mock_client.publish.assert_called_with(f"cmd/{device.id}/{at.name}", '{"command": "off"}')