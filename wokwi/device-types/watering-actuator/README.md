# Система полива

Тип устройства: `watering-actuator`

## Описание
Управляет насосом полива растений.

## Пины
| Компонент   | Пин |
|-------------|-----|
| Water Pump  | 4   |

## MQTT топики

### Подписка
- `devices/{id}/commands/watering` — команда управления

### Публикуемые
- `devices/{id}/status/watering` — статус насоса

## Пример команды
```json
{"command": "on"}
```
```json
{"command": "off"}
```

## Пример статуса
```json
{"status": "on"}
```

## Сборка
```bash
pio run -e watering-actuator
```

## Wokwi
Откройте `diagram.json` в Wokwi для симуляции.
