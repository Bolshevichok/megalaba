# Система проветривания

Тип устройства: `ventilation-actuator`

## Описание
Управляет вентилятором для циркуляции воздуха.

## Пины
| Компонент | Пин |
|-----------|-----|
| Fan       | 18  |

## MQTT топики

### Подписка
- `devices/{id}/commands/ventilation` — команда управления

### Публикуемые
- `devices/{id}/status/ventilation` — статус вентилятора

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
pio run -e ventilation-actuator
```

## Wokwi
Откройте `diagram.json` в Wokwi для симуляции.
