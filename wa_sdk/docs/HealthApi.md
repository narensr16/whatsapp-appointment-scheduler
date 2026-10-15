# wa_sdk.HealthApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**check_health_health_get**](HealthApi.md#check_health_health_get) | **GET** /health | Health check endpoint


# **check_health_health_get**
> HealthResponse check_health_health_get()

Health check endpoint

Returns application health status, version, and verifies database connectivity.

### Example


```python
import wa_sdk
from wa_sdk.models.health_response import HealthResponse
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
    api_instance = wa_sdk.HealthApi(api_client)

    try:
        # Health check endpoint
        api_response = api_instance.check_health_health_get()
        print("The response of HealthApi->check_health_health_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling HealthApi->check_health_health_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**HealthResponse**](HealthResponse.md)

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

