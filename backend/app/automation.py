import json
import logging
from typing import Any

from sqlalchemy.orm import Session
from app.models import ActuatorCommand, Actuator, CommandType, Greenhouse, Script, Sensor, ActuatorStatus
from app.mqtt.client import mqtt_client

logger = logging.getLogger(__name__)


def _build_canvas_source_map(greenhouse_id: int, db: Session) -> dict[str, int]:
    """Build mapping placed-device-id -> source device id from greenhouse canvas_state."""
    greenhouse = db.query(Greenhouse).filter(Greenhouse.id == greenhouse_id).first()
    if not greenhouse or not greenhouse.canvas_state:
        return {}

    try:
        canvas_items = json.loads(greenhouse.canvas_state)
    except (TypeError, json.JSONDecodeError):
        return {}

    if not isinstance(canvas_items, list):
        return {}

    mapping: dict[str, int] = {}
    for item in canvas_items:
        if not isinstance(item, dict):
            continue
        placed_id = item.get("id")
        source_id = item.get("sourceId")
        if isinstance(placed_id, str) and isinstance(source_id, int):
            mapping[placed_id] = source_id
    return mapping


def _resolve_device_id_from_rule_key(raw_key: Any, canvas_map: dict[str, int]) -> int | None:
    """Resolve rule key into a device id (supports numeric ids and legacy placed ids)."""
    if isinstance(raw_key, int):
        return raw_key

    if isinstance(raw_key, str):
        if raw_key.isdigit():
            return int(raw_key)
        mapped = canvas_map.get(raw_key)
        if mapped is not None:
            return mapped

    return None

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

def check_rule_conditions(conditions: list[dict], db: Session, canvas_map: dict[str, int]) -> bool:
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
        parsed_keys = []
        for key in sensor_keys:
            resolved = _resolve_device_id_from_rule_key(key, canvas_map)
            if resolved is not None:
                parsed_keys.append(resolved)
                
        # fetch latest reading
        cond_matched = False
        operator = cond.get("operator", ">")
        try:
            threshold = float(cond.get("value", 0))
        except ValueError:
            threshold = 0.0
            
        for key_id in parsed_keys:
            # Backward compatibility: key can be either a sensor id or a device id.
            candidate_sensors: list[Sensor] = []

            sensor = db.query(Sensor).filter(Sensor.id == key_id).first()
            if sensor is not None:
                candidate_sensors = [sensor]
            else:
                candidate_sensors = db.query(Sensor).filter(Sensor.device_id == key_id).all()

            if not candidate_sensors:
                continue

            from app.models import SensorReading

            for candidate in candidate_sensors:
                latest_reading = (
                    db.query(SensorReading)
                    .filter(SensorReading.sensor_id == candidate.id)
                    .order_by(SensorReading.recorded_at.desc(), SensorReading.id.desc())
                    .first()
                )
                # If no reading, we consider the condition false for this sensor.
                if latest_reading is not None and latest_reading.value is not None:
                    if evaluate_condition(latest_reading.value, operator, threshold):
                        cond_matched = True
                        break

            if cond_matched:
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
    canvas_map = _build_canvas_source_map(greenhouse_id, db)
    
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
            
        is_true = check_rule_conditions(conditions, db, canvas_map)
        
        # If true, apply target command. If false, apply opposite command.
        command_to_apply = target_command.lower() if is_true else ("off" if target_command.lower() == "on" else "on")
        
        for key in actuator_keys:
            key_id = _resolve_device_id_from_rule_key(key, canvas_map)
            if key_id is None:
                continue

            # Backward compatibility: key can be either an actuator id or a device id.
            actuator = db.query(Actuator).filter(Actuator.id == key_id).first()
            if actuator is None:
                actuator = (
                    db.query(Actuator)
                    .filter(Actuator.device_id == key_id)
                    .order_by(Actuator.id.asc())
                    .first()
                )
            if not actuator:
                continue
            act_id = actuator.id
                
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
