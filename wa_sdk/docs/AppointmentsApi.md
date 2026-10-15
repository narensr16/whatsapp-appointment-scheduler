# wa_sdk.AppointmentsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**cancel_appointment_appointments_appointment_id_delete**](AppointmentsApi.md#cancel_appointment_appointments_appointment_id_delete) | **DELETE** /appointments/{appointment_id} | Cancel an appointment
[**create_appointment_appointments_post**](AppointmentsApi.md#create_appointment_appointments_post) | **POST** /appointments/ | Create a new doctor appointment
[**get_appointment_appointments_appointment_id_get**](AppointmentsApi.md#get_appointment_appointments_appointment_id_get) | **GET** /appointments/{appointment_id} | Get appointment by ID
[**list_appointments_appointments_get**](AppointmentsApi.md#list_appointments_appointments_get) | **GET** /appointments/ | List appointments


# **cancel_appointment_appointments_appointment_id_delete**
> object cancel_appointment_appointments_appointment_id_delete(appointment_id)

Cancel an appointment

Mark an appointment as cancelled.

### Example


```python
import wa_sdk
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
    api_instance = wa_sdk.AppointmentsApi(api_client)
    appointment_id = 56 # int | 

    try:
        # Cancel an appointment
        api_response = api_instance.cancel_appointment_appointments_appointment_id_delete(appointment_id)
        print("The response of AppointmentsApi->cancel_appointment_appointments_appointment_id_delete:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AppointmentsApi->cancel_appointment_appointments_appointment_id_delete: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **appointment_id** | **int**|  | 

### Return type

**object**

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

# **create_appointment_appointments_post**
> AppointmentResponse create_appointment_appointments_post(appointment_create)

Create a new doctor appointment

Validates doctor availability, working hours, and bookable slot, then creates a confirmed appointment.

### Example


```python
import wa_sdk
from wa_sdk.models.appointment_create import AppointmentCreate
from wa_sdk.models.appointment_response import AppointmentResponse
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
    api_instance = wa_sdk.AppointmentsApi(api_client)
    appointment_create = wa_sdk.AppointmentCreate() # AppointmentCreate | 

    try:
        # Create a new doctor appointment
        api_response = api_instance.create_appointment_appointments_post(appointment_create)
        print("The response of AppointmentsApi->create_appointment_appointments_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AppointmentsApi->create_appointment_appointments_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **appointment_create** | [**AppointmentCreate**](AppointmentCreate.md)|  | 

### Return type

[**AppointmentResponse**](AppointmentResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Appointment successfully booked. |  -  |
**400** | Invalid input, past slot, or invalid slot timing. |  -  |
**404** | Doctor not found. |  -  |
**409** | Slot conflict - appointment slot already booked. |  -  |
**500** | Internal server error. |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_appointment_appointments_appointment_id_get**
> AppointmentResponse get_appointment_appointments_appointment_id_get(appointment_id)

Get appointment by ID

Retrieve details of a single appointment by its ID.

### Example


```python
import wa_sdk
from wa_sdk.models.appointment_response import AppointmentResponse
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
    api_instance = wa_sdk.AppointmentsApi(api_client)
    appointment_id = 56 # int | 

    try:
        # Get appointment by ID
        api_response = api_instance.get_appointment_appointments_appointment_id_get(appointment_id)
        print("The response of AppointmentsApi->get_appointment_appointments_appointment_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AppointmentsApi->get_appointment_appointments_appointment_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **appointment_id** | **int**|  | 

### Return type

[**AppointmentResponse**](AppointmentResponse.md)

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

# **list_appointments_appointments_get**
> List[AppointmentResponse] list_appointments_appointments_get(doctor_id=doctor_id, user_phone=user_phone, appointment_date=appointment_date, skip=skip, limit=limit)

List appointments

Retrieve appointments filtered by doctor, patient phone number, or date.

### Example


```python
import wa_sdk
from wa_sdk.models.appointment_response import AppointmentResponse
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
    api_instance = wa_sdk.AppointmentsApi(api_client)
    doctor_id = 56 # int | Filter by doctor ID (optional)
    user_phone = 'user_phone_example' # str | Filter by patient phone number (optional)
    appointment_date = '2013-10-20' # date | Filter by appointment date (YYYY-MM-DD) (optional)
    skip = 0 # int |  (optional) (default to 0)
    limit = 100 # int |  (optional) (default to 100)

    try:
        # List appointments
        api_response = api_instance.list_appointments_appointments_get(doctor_id=doctor_id, user_phone=user_phone, appointment_date=appointment_date, skip=skip, limit=limit)
        print("The response of AppointmentsApi->list_appointments_appointments_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AppointmentsApi->list_appointments_appointments_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **doctor_id** | **int**| Filter by doctor ID | [optional] 
 **user_phone** | **str**| Filter by patient phone number | [optional] 
 **appointment_date** | **date**| Filter by appointment date (YYYY-MM-DD) | [optional] 
 **skip** | **int**|  | [optional] [default to 0]
 **limit** | **int**|  | [optional] [default to 100]

### Return type

[**List[AppointmentResponse]**](AppointmentResponse.md)

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

