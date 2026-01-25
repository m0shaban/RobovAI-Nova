# artsearch.ArtApi

All URIs are relative to *https://api.artsearch.io*

Method | HTTP request | Description
------------- | ------------- | -------------
[**random_artwork**](ArtApi.md#random_artwork) | **GET** /artworks/random | Random Artwork
[**retrieve_artwork_by_id**](ArtApi.md#retrieve_artwork_by_id) | **GET** /artworks/{id} | Retrieve Artwork by Id
[**search_artworks**](ArtApi.md#search_artworks) | **GET** /artworks | Search Artworks


# **random_artwork**
> RetrieveArtworkById200Response random_artwork()

Random Artwork

Get one random artwork from our vast collection. The API returns comprehensive details including the title, high-quality image URL, creation date range, and a rich description providing historical and artistic context.

### Example

* Api Key Authentication (apiKey):
* Api Key Authentication (headerApiKey):

```python
import artsearch
from artsearch.models.retrieve_artwork_by_id200_response import RetrieveArtworkById200Response
from artsearch.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.artsearch.io
# See configuration.py for a list of all supported configuration parameters.
configuration = artsearch.Configuration(
    host = "https://api.artsearch.io"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: apiKey
configuration.api_key['apiKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['apiKey'] = 'Bearer'

# Configure API key authorization: headerApiKey
configuration.api_key['headerApiKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['headerApiKey'] = 'Bearer'

# Enter a context with an instance of the API client
with artsearch.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = artsearch.ArtApi(api_client)

    try:
        # Random Artwork
        api_response = api_instance.random_artwork()
        print("The response of ArtApi->random_artwork:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ArtApi->random_artwork: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**RetrieveArtworkById200Response**](RetrieveArtworkById200Response.md)

### Authorization

[apiKey](../README.md#apiKey), [headerApiKey](../README.md#headerApiKey)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**401** | Unauthorized |  -  |
**402** | Payment Required |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**406** | Not Acceptable |  -  |
**429** | Too Many Requests |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **retrieve_artwork_by_id**
> RetrieveArtworkById200Response retrieve_artwork_by_id(id)

Retrieve Artwork by Id

Get one artwork by its id. The API returns the title, image URL, start and end date, and a description of the artwork.

### Example

* Api Key Authentication (apiKey):
* Api Key Authentication (headerApiKey):

```python
import artsearch
from artsearch.models.retrieve_artwork_by_id200_response import RetrieveArtworkById200Response
from artsearch.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.artsearch.io
# See configuration.py for a list of all supported configuration parameters.
configuration = artsearch.Configuration(
    host = "https://api.artsearch.io"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: apiKey
configuration.api_key['apiKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['apiKey'] = 'Bearer'

# Configure API key authorization: headerApiKey
configuration.api_key['headerApiKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['headerApiKey'] = 'Bearer'

# Enter a context with an instance of the API client
with artsearch.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = artsearch.ArtApi(api_client)
    id = 26226350 # int | The id of the artwork.

    try:
        # Retrieve Artwork by Id
        api_response = api_instance.retrieve_artwork_by_id(id)
        print("The response of ArtApi->retrieve_artwork_by_id:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ArtApi->retrieve_artwork_by_id: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| The id of the artwork. | 

### Return type

[**RetrieveArtworkById200Response**](RetrieveArtworkById200Response.md)

### Authorization

[apiKey](../README.md#apiKey), [headerApiKey](../README.md#headerApiKey)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**401** | Unauthorized |  -  |
**402** | Payment Required |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**406** | Not Acceptable |  -  |
**429** | Too Many Requests |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **search_artworks**
> SearchArtworks200Response search_artworks(query=query, earliest_start_date=earliest_start_date, latest_start_date=latest_start_date, earliest_end_date=earliest_end_date, latest_end_date=latest_end_date, min_ratio=min_ratio, max_ratio=max_ratio, type=type, material=material, technique=technique, origin=origin, offset=offset, number=number)

Search Artworks

Search and filter artworks by query, creation time, material, technique, and origin. The natural language search uses semantic AI to understand the context of your query, so you can search for artworks by their style, subject, or even emotions they evoke. The API returns a list of artworks matching the given criteria.

### Example

* Api Key Authentication (apiKey):
* Api Key Authentication (headerApiKey):

```python
import artsearch
from artsearch.models.search_artworks200_response import SearchArtworks200Response
from artsearch.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.artsearch.io
# See configuration.py for a list of all supported configuration parameters.
configuration = artsearch.Configuration(
    host = "https://api.artsearch.io"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: apiKey
configuration.api_key['apiKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['apiKey'] = 'Bearer'

# Configure API key authorization: headerApiKey
configuration.api_key['headerApiKey'] = os.environ["API_KEY"]

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['headerApiKey'] = 'Bearer'

# Enter a context with an instance of the API client
with artsearch.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = artsearch.ArtApi(api_client)
    query = 'landscape paintings' # str | The search query. (optional)
    earliest_start_date = 1750 # int | The artwork must have been created after this date. (optional)
    latest_start_date = 1755 # int | The artwork must have been created before this date. (optional)
    earliest_end_date = 1751 # int | For artworks with a period of creation, the completion date must be after this date. (optional)
    latest_end_date = 1760 # int | For artworks with a period of creation, the completion date must be before this date. (optional)
    min_ratio = 0.8 # float | The minimum aspect ratio (width/height) the artwork image must have. (optional)
    max_ratio = 1.5 # float | The maximum aspect ratio (width/height) the artwork image must have. (optional)
    type = 'painting' # str | The artwork type. Possible values are tapestry, collotype, collage, printmaking, cutting, digital_art, sculpture, metalwork, fragment, token, embroidery, painting, jewellery, print, ornament, photograph, statuette, furniture, needlework, drawing, miniature, tile, stereograph, calligraphy. (optional)
    material = 'ivory' # str | The art material used. Possible values are ferrous_lactate, ink, textile, metal, bronze, canvas, stone, reduced_iron, horn, stoneware, in_shell_walnuts, chalk, velvet, silver, charcoal, gold_leaf, candied_walnuts, porcelain, walnut_halves, jade, cotton, paint, ferrous_fumarate, graphite, cobalt, sandstone, plastic, walnut_pieces, clay, walnuts, cupric_sulfate, ivory, ferric_orthophosphate, earthenware, tin, pen, linen, mahogany, electrolytic_iron, silk, crayon, black_walnuts, brush, beech_wood, terracotta, glass, lead, brass, oil_paint, pencil, leather, gold, marble, watercolor, diamond, iron, ferrous_sulfate, walnut_halves_and_pieces, gouache, wool, ceramic, parchment, cork, limestone, copper_gluconate, paper, pastel, copper, cardboard, plant_material, oak, wood. (optional)
    technique = 'etching' # str | The art technique used. Possible values are engraving, grinding, embroidering, etching, vitrification, gilding, lithography, knitting, cyanotype, silkscreen, woodcut, printing, drypoint, photolithography, weaving, sawing, casting, glassblowing, block_printing, photographing, forging. (optional)
    origin = 'Italy' # str | The country or region of origin for the artwork (optional)
    offset = 0 # int | The number of artworks to skip in range [0,1000] (optional)
    number = 10 # int | The number of artworks to return in range [1,10] (optional)

    try:
        # Search Artworks
        api_response = api_instance.search_artworks(query=query, earliest_start_date=earliest_start_date, latest_start_date=latest_start_date, earliest_end_date=earliest_end_date, latest_end_date=latest_end_date, min_ratio=min_ratio, max_ratio=max_ratio, type=type, material=material, technique=technique, origin=origin, offset=offset, number=number)
        print("The response of ArtApi->search_artworks:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ArtApi->search_artworks: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **query** | **str**| The search query. | [optional] 
 **earliest_start_date** | **int**| The artwork must have been created after this date. | [optional] 
 **latest_start_date** | **int**| The artwork must have been created before this date. | [optional] 
 **earliest_end_date** | **int**| For artworks with a period of creation, the completion date must be after this date. | [optional] 
 **latest_end_date** | **int**| For artworks with a period of creation, the completion date must be before this date. | [optional] 
 **min_ratio** | **float**| The minimum aspect ratio (width/height) the artwork image must have. | [optional] 
 **max_ratio** | **float**| The maximum aspect ratio (width/height) the artwork image must have. | [optional] 
 **type** | **str**| The artwork type. Possible values are tapestry, collotype, collage, printmaking, cutting, digital_art, sculpture, metalwork, fragment, token, embroidery, painting, jewellery, print, ornament, photograph, statuette, furniture, needlework, drawing, miniature, tile, stereograph, calligraphy. | [optional] 
 **material** | **str**| The art material used. Possible values are ferrous_lactate, ink, textile, metal, bronze, canvas, stone, reduced_iron, horn, stoneware, in_shell_walnuts, chalk, velvet, silver, charcoal, gold_leaf, candied_walnuts, porcelain, walnut_halves, jade, cotton, paint, ferrous_fumarate, graphite, cobalt, sandstone, plastic, walnut_pieces, clay, walnuts, cupric_sulfate, ivory, ferric_orthophosphate, earthenware, tin, pen, linen, mahogany, electrolytic_iron, silk, crayon, black_walnuts, brush, beech_wood, terracotta, glass, lead, brass, oil_paint, pencil, leather, gold, marble, watercolor, diamond, iron, ferrous_sulfate, walnut_halves_and_pieces, gouache, wool, ceramic, parchment, cork, limestone, copper_gluconate, paper, pastel, copper, cardboard, plant_material, oak, wood. | [optional] 
 **technique** | **str**| The art technique used. Possible values are engraving, grinding, embroidering, etching, vitrification, gilding, lithography, knitting, cyanotype, silkscreen, woodcut, printing, drypoint, photolithography, weaving, sawing, casting, glassblowing, block_printing, photographing, forging. | [optional] 
 **origin** | **str**| The country or region of origin for the artwork | [optional] 
 **offset** | **int**| The number of artworks to skip in range [0,1000] | [optional] 
 **number** | **int**| The number of artworks to return in range [1,10] | [optional] 

### Return type

[**SearchArtworks200Response**](SearchArtworks200Response.md)

### Authorization

[apiKey](../README.md#apiKey), [headerApiKey](../README.md#headerApiKey)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**401** | Unauthorized |  -  |
**402** | Payment Required |  -  |
**403** | Forbidden |  -  |
**404** | Not Found |  -  |
**406** | Not Acceptable |  -  |
**429** | Too Many Requests |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

