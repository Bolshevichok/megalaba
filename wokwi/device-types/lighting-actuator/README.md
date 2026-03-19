# Система освещения

Тип устройства: `lighting-actuator`

## Описание
Управляет дополнительным освещением теплицы.

## Пины
| Компонент | Пин |
|-----------|-----|
| LED       | 2   |

## MQTT топики

### Подписка
- `devices/{id}/commands/lighting` — команда управления

### Публикуемые
- `devices/{id}/status/lighting` — статус освещения

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
pio run -e lighting-actuator
```

## Wokwi
Откройте `diagram.json` в Wokwi для симуляции.
