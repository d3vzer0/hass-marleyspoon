[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

### Introduction
This integration polls the MarleySpoon API and registers the upcoming 4 orders as individual sensors named as sensor.ms_order_week_0, sensor.ms_order_week_1 etc. Each sensor contains a state which indicates if the order is delivered or not. Additionally the following attributes are also added:

- total_price: str ('41')
- status: str ('at_home')
- cutoff_days: int (5)
- days_until_cutoff: int (0)
- intended_delivery_date: str ('2021-06-28')
- delivery_slot -> dict(str, str)
  - from: str ('08:00')
  - to: str ('22:00')
  - id: int 101
- recipes -> list(dict(str, str))
  - id: int (53193)
    quantity: int (2)
    name: str ('Pestotortelloni')
    subtitle: str ('met romige spinazie en champignons')
    classic: bool (false)
    meal_type: str ('veggie')
    image.small: str ('https://...')

### Requirements
Python dependencies:
- aiohttp

### Configuration


### Screenshots ###
