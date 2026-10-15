# wa_sdk.RootApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**root_redirect_get**](RootApi.md#root_redirect_get) | **GET** / | Root Redirect


# **root_redirect_get**
> object root_redirect_get()

Root Redirect

Root endpoint welcoming developers and pointing to Swagger documentation.

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
    api_instance = wa_sdk.RootApi(api_client)

    try:
        # Root Redirect
        api_response = api_instance.root_redirect_get()
        print("The response of RootApi->root_redirect_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling RootApi->root_redirect_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

