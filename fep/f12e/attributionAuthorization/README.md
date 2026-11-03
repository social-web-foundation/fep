# attributionAuthorization

URI
: `https://w3id.org/fep/f12e/attributionAuthorization`

Label
: has an attribution authorization

Comment
: References an `AttributionAuthorization` that proves the consent of the attributed party to be listed in the `attributions` Collection of an object.

Domain
: [Relationship](https://www.w3.org/ns/activitystreams#Relationship)

Range
: An [AttributionAuthorization](https://w3id.org/fep/f12e/AttributionAuthorization) (`@id`)

Required
: No

Functional
: Yes

Is defined by
: [FEP-f12e](https://w3id.org/fep/f12e)


## Examples

Example of an attributions item referencing its authorization

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "Relationship",
  "subject": "https://example.com/article/1",
  "relationship": "https://schema.org/author",
  "object": "https://example.org/actors/1",
  "attributionAuthorization": "https://example.org/actors/1/attributions/1"
}
    ```
