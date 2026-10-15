# DoctorSlotsResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**doctor_id** | **int** |  | 
**doctor_name** | **str** |  | 
**var_date** | **str** |  | 
**available_slots** | **List[str]** |  | 

## Example

```python
from wa_sdk.models.doctor_slots_response import DoctorSlotsResponse

# TODO update the JSON string below
json = "{}"
# create an instance of DoctorSlotsResponse from a JSON string
doctor_slots_response_instance = DoctorSlotsResponse.from_json(json)
# print the JSON string representation of the object
print(DoctorSlotsResponse.to_json())

# convert the object into a dict
doctor_slots_response_dict = doctor_slots_response_instance.to_dict()
# create an instance of DoctorSlotsResponse from a dict
doctor_slots_response_from_dict = DoctorSlotsResponse.from_dict(doctor_slots_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


