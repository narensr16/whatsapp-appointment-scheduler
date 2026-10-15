# wa_sdk.WhatsAppWebhookApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**handle_whatsapp_webhook_whatsapp_post**](WhatsAppWebhookApi.md#handle_whatsapp_webhook_whatsapp_post) | **POST** /whatsapp/ | Handle incoming WhatsApp message webhook
[**verify_meta_webhook_whatsapp_get**](WhatsAppWebhookApi.md#verify_meta_webhook_whatsapp_get) | **GET** /whatsapp/ | Meta WhatsApp Webhook Verification Handshake


# **handle_whatsapp_webhook_whatsapp_post**
> WhatsAppResponse handle_whatsapp_webhook_whatsapp_post(x_hub_signature_256=x_hub_signature_256)

Handle incoming WhatsApp message webhook

Accepts WhatsApp message (either mock or Meta format), parses intent, executes booking, and responds.

### Example


```python
import wa_sdk
from wa_sdk.models.whats_app_response import WhatsAppResponse
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
    api_instance = wa_sdk.WhatsAppWebhookApi(api_client)
    x_hub_signature_256 = 'x_hub_signature_256_example' # str |  (optional)

    try:
        # Handle incoming WhatsApp message webhook
        api_response = api_instance.handle_whatsapp_webhook_whatsapp_post(x_hub_signature_256=x_hub_signature_256)
        print("The response of WhatsAppWebhookApi->handle_whatsapp_webhook_whatsapp_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling WhatsAppWebhookApi->handle_whatsapp_webhook_whatsapp_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **x_hub_signature_256** | **str**|  | [optional] 

### Return type

[**WhatsAppResponse**](WhatsAppResponse.md)

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

# **verify_meta_webhook_whatsapp_get**
> object verify_meta_webhook_whatsapp_get(hub_mode=hub_mode, hub_verify_token=hub_verify_token, hub_challenge=hub_challenge)

Meta WhatsApp Webhook Verification Handshake

Endpoint for Meta Cloud API webhook subscription challenge.

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
    api_instance = wa_sdk.WhatsAppWebhookApi(api_client)
    hub_mode = 'hub_mode_example' # str |  (optional)
    hub_verify_token = 'hub_verify_token_example' # str |  (optional)
    hub_challenge = 'hub_challenge_example' # str |  (optional)

    try:
        # Meta WhatsApp Webhook Verification Handshake
        api_response = api_instance.verify_meta_webhook_whatsapp_get(hub_mode=hub_mode, hub_verify_token=hub_verify_token, hub_challenge=hub_challenge)
        print("The response of WhatsAppWebhookApi->verify_meta_webhook_whatsapp_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling WhatsAppWebhookApi->verify_meta_webhook_whatsapp_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **hub_mode** | **str**|  | [optional] 
 **hub_verify_token** | **str**|  | [optional] 
 **hub_challenge** | **str**|  | [optional] 

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

