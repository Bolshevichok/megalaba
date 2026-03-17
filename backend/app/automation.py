import json
import logging
from typing import Any

from sqlalchemy.orm import Session
from app.models import ActuatorCommand, Actuator, CommandType, Script, Sensor, ActuatorStatus
from app.mqtt.client import mqtt_client

logger = logging.getLogger(__name__)

def evaluate_condition(sensor_value: float, operator: str, threshold: float) -> bool:
    if operator == ">":
        return sensor_value > threshold
    elif operator == ">=":
        return sensor_value >= threshold
    elif operator == "<":
        return sensor_value < threshold
    elif operator == "<=":
        return sensor_value <= threshold
    elif operator == "=" or operator == "==":
        return sensor_value == threshold
    elif operator == "!=":
        return sensor_value != threshold
    return False

def check_rule_conditions(conditions: list[dict], db: Session) -> bool:
    """Evaluate a list of rule conditions (with AND/OR logic)."""
    if not conditions:
        return False
    
    # Simple evaluation logic matching the frontend logic
    # the frontend has joinWithPrevious = "AND" | "OR"
    # we'll evaluate left-to-right.
    
    final_result = True
    for i, cond in enumerate(conditions):
        # We need to get the sensor current value
        # For simplicity, if multiple sensors are specified, we evaluate if ANY sensor matches the condition?
        # Let's say if ANY of the sensorKeys matches
        
        sensor_keys = cond.get("sensorKeys", [])
        if not sensor_keys:
            continue
            
        # Get latest readings for these sensors.
        # Since sensorKeys might be ID strings, cast to ints. Replace 'placed-' with actual ID for now if needed.
        # Assuming the UI has been adapted to send integers.
        parsed_sensor_ids = []
        for key in sensor_keys:
            try:
                # If frontend sends 'placed-123', handle it gracefully or assume it's just the int ID.
                if isinstance(key, str) and key.isdigit():
                    parsed_sensor_ids.append(int(key))
                elif isinstance(key, int):
                    parsed_sensor_ids.append(key)
            except ValueError:
                pass
                
        # fetch latest reading
        cond_matched = False
        operator = cond.get("operator", ">")
        try:
            threshold = float(cond.get("value", 0))
        except ValueError:
            threshold = 0.0
            
        for db_sensor_id in parsed_sensor_ids:
            sensor = db.query(Sensor).filter(Sensor.id == db_sensor_id).first()
            if not sensor:
                continue
            # get latest reading
            from app.models import SensorReading
            latest_reading = db.query(SensorReading).filter(SensorReading.sensor_id == db_sensor_id).order_by(SensorReading.recorded_at.desc(), SensorReading.id.desc()).first()
            # If no reading, we consider the condition false
            if latest_reading is not None and latest_reading.value is not None:
                if evaluate_condition(latest_reading.value, operator, threshold):
                    cond_matched = True
                    break
        
        if i == 0:
            final_result = cond_matched
        else:
            join = cond.get("joinWithPrevious", "OR").upper()
            if join == "AND":
                final_result = final_result and cond_matched
            else:
                final_result = final_result or cond_matched

    return final_result

def process_automation_rules(greenhouse_id: int, db: Session):
    """
    Triggered when new sensor data arrives.
    Checks all enabled scripts for the greenhouse and applies commands to actuators.
    """
    scripts = db.query(Script).filter(Script.greenhouse_id == greenhouse_id, Script.enabled == True).all()
    
    for script in scripts:
        if not script.script_code:
            continue
            
        try:
            rule = json.loads(script.script_code)
        except json.JSONDecodeError:
            logger.warning(f"Script {script.id} has invalid JSON script_code")
            continue
            
        conditions = rule.get("conditions", [])
        actuator_keys = rule.get("actuatorKeys", [])
        target_command = rule.get("command", "on") # "on" or "off"
        
        if not conditions or not actuator_keys:
            continue
            
        is_true = check_rule_conditions(conditions, db)
        
        # If true, apply target command. If false, apply opposite command.
        command_to_apply = target_command.lower() if is_true else ("off" if target_command.lower() == "on" else "on")
        
        for key in actuator_keys:
            try:
                act_id = int(key)
            except ValueError:
                continue
                
            actuator = db.query(Actuator).filter(Actuator.id == act_id).first()
            if not actuator:
                continue
                
            # Check current status to avoid flood
            current_status = actuator.status.value if actuator.status else "off"
            if current_status != command_to_apply:
                logger.info(f"Rule '{script.name}' triggered: turning {command_to_apply} actuator {actuator.id}")
                # Change actuator state in DB immediately
                actuator.status = ActuatorStatus.on if command_to_apply == "on" else ActuatorStatus.off
                
                # Add command history
                cmd_type = CommandType.on if command_to_apply == "on" else CommandType.off
                cmd_record = ActuatorCommand(
                    actuator_id=act_id,
                    command=cmd_type,
                    status="sent"
                )
                db.add(cmd_record)
                
                if mqtt_client and mqtt_client.connected:
                    # Format: cmd/<device_id>/<actuator_id> payload: on/off
                    actuator_type = actuator.actuator_type
                    act_name = actuator_type.name if actuator_type else str(act_id)
                    topic = f"cmd/{actuator.device_id}/{act_name}"
                    mqtt_client.publish(topic, f'{{"command": "{command_to_apply}"}}')
                
    db.commit()
