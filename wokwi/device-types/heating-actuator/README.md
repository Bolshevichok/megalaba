# Система обогрева

Тип устройства: `heating-actuator`

## Описание
Управляет нагревательным элементом для поддержания температуры.

## Пины
| Компонент | Пин |
|-----------|-----|
| Heater    | 5   |

## MQTT топики

### Подписка
- `devices/{id}/commands/heating` — команда управления

### Публикуемые
- `devices/{id}/status/heating` — статус нагревателя

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
pio run -e heating-actuator
```

## Wokwi
Откройте `diagram.json` в Wokwi для симуляции.
