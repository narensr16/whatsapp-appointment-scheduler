# WhatsAppResponse

Standardized response from the WhatsApp webhook endpoint.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** |  | 
**reply** | **str** |  | 
**appointment** | [**AppointmentResponse**](AppointmentResponse.md) |  | [optional] 
**suggested_slots** | **List[str]** |  | [optional] 
**message_id** | **str** |  | [optional] 

## Example

```python
from wa_sdk.models.whats_app_response import WhatsAppResponse

# TODO update the JSON string below
json = "{}"
# create an instance of WhatsAppResponse from a JSON string
whats_app_response_instance = WhatsAppResponse.from_json(json)
# print the JSON string representation of the object
print(WhatsAppResponse.to_json())

# convert the object into a dict
whats_app_response_dict = whats_app_response_instance.to_dict()
# create an instance of WhatsAppResponse from a dict
whats_app_response_from_dict = WhatsAppResponse.from_dict(whats_app_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


