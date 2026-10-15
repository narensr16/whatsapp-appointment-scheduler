# wa_sdk.DoctorsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_doctor_doctors_post**](DoctorsApi.md#create_doctor_doctors_post) | **POST** /doctors/ | Register a new doctor
[**get_doctor_available_slots_doctors_doctor_id_slots_get**](DoctorsApi.md#get_doctor_available_slots_doctors_doctor_id_slots_get) | **GET** /doctors/{doctor_id}/slots | Get available slots for a doctor on a specific date
[**list_doctors_doctors_get**](DoctorsApi.md#list_doctors_doctors_get) | **GET** /doctors/ | List all active doctors


# **create_doctor_doctors_post**
> DoctorResponse create_doctor_doctors_post(doctor_create)

Register a new doctor

Add a new doctor to the clinic roster.

### Example


```python
import wa_sdk
from wa_sdk.models.doctor_create import DoctorCreate
from wa_sdk.models.doctor_response import DoctorResponse
from wa_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = wa_sdk.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with wa_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = wa_sdk.DoctorsApi(api_client)
    doctor_create = wa_sdk.DoctorCreate() # DoctorCreate | 

    try:
        # Register a new doctor
        api_response = api_instance.create_doctor_doctors_post(doctor_create)
        print("The response of DoctorsApi->create_doctor_doctors_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DoctorsApi->create_doctor_doctors_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **doctor_create** | [**DoctorCreate**](DoctorCreate.md)|  | 

### Return type

[**DoctorResponse**](DoctorResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_doctor_available_slots_doctors_doctor_id_slots_get**
> DoctorSlotsResponse get_doctor_available_slots_doctors_doctor_id_slots_get(doctor_id, target_date=target_date)

Get available slots for a doctor on a specific date

Returns available 30-minute booking slots for a doctor on the requested date.

### Example


```python
import wa_sdk
from wa_sdk.models.doctor_slots_response import DoctorSlotsResponse
from wa_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = wa_sdk.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with wa_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = wa_sdk.DoctorsApi(api_client)
    doctor_id = 56 # int | 
    target_date = '2013-10-20' # date | Date to check (defaults to today) (optional)

    try:
        # Get available slots for a doctor on a specific date
        api_response = api_instance.get_doctor_available_slots_doctors_doctor_id_slots_get(doctor_id, target_date=target_date)
        print("The response of DoctorsApi->get_doctor_available_slots_doctors_doctor_id_slots_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DoctorsApi->get_doctor_available_slots_doctors_doctor_id_slots_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **doctor_id** | **int**|  | 
 **target_date** | **date**| Date to check (defaults to today) | [optional] 

### Return type

[**DoctorSlotsResponse**](DoctorSlotsResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_doctors_doctors_get**
> List[DoctorResponse] list_doctors_doctors_get()

List all active doctors

Fetch all doctors available for appointments.

### Example


```python
import wa_sdk
from wa_sdk.models.doctor_response import DoctorResponse
from wa_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = wa_sdk.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with wa_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = wa_sdk.DoctorsApi(api_client)

    try:
        # List all active doctors
        api_response = api_instance.list_doctors_doctors_get()
        print("The response of DoctorsApi->list_doctors_doctors_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DoctorsApi->list_doctors_doctors_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[DoctorResponse]**](DoctorResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

