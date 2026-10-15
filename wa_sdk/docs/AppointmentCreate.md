# AppointmentCreate

Validated request schema for creating an appointment: - user_phone - doctor_id - slot

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**user_phone** | **str** |  | 
**doctor_id** | **int** |  | 
**slot** | **datetime** |  | 

## Example

```python
from wa_sdk.models.appointment_create import AppointmentCreate

# TODO update the JSON string below
json = "{}"
# create an instance of AppointmentCreate from a JSON string
appointment_create_instance = AppointmentCreate.from_json(json)
# print the JSON string representation of the object
print(AppointmentCreate.to_json())

# convert the object into a dict
appointment_create_dict = appointment_create_instance.to_dict()
# create an instance of AppointmentCreate from a dict
appointment_create_from_dict = AppointmentCreate.from_dict(appointment_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


