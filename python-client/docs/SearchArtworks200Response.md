# SearchArtworks200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**available** | **int** |  | [optional] 
**number** | **int** |  | [optional] 
**offset** | **int** |  | [optional] 
**artworks** | [**List[SearchArtworks200ResponseArtworksInner]**](SearchArtworks200ResponseArtworksInner.md) |  | [optional] 

## Example

```python
from artsearch.models.search_artworks200_response import SearchArtworks200Response

# TODO update the JSON string below
json = "{}"
# create an instance of SearchArtworks200Response from a JSON string
search_artworks200_response_instance = SearchArtworks200Response.from_json(json)
# print the JSON string representation of the object
print(SearchArtworks200Response.to_json())

# convert the object into a dict
search_artworks200_response_dict = search_artworks200_response_instance.to_dict()
# create an instance of SearchArtworks200Response from a dict
search_artworks200_response_from_dict = SearchArtworks200Response.from_dict(search_artworks200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


