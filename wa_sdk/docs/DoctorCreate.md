# DoctorCreate


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**specialty** | **str** |  | [optional] 
**phone** | **str** |  | [optional] 
**is_active** | **bool** |  | [optional] [default to True]

## Example

```python
from wa_sdk.models.doctor_create import DoctorCreate

# TODO update the JSON string below
json = "{}"
# create an instance of DoctorCreate from a JSON string
doctor_create_instance = DoctorCreate.from_json(json)
# print the JSON string representation of the object
print(DoctorCreate.to_json())

# convert the object into a dict
doctor_create_dict = doctor_create_instance.to_dict()
# create an instance of DoctorCreate from a dict
doctor_create_from_dict = DoctorCreate.from_dict(doctor_create_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


