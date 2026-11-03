# AttributionAuthorization

URI
: `https://w3id.org/fep/f12e/AttributionAuthorization`

Label
: Attribution Authorization

Comment
: A revocable approval stamp issued by an actor. Its `object` is the `Relationship` the actor consents to.

Subclass of
: [Object](https://www.w3.org/ns/activitystreams#Object)

See also
: [attributionAuthorization](https://w3id.org/fep/f12e/attributionAuthorization) | [AttributionRequest](https://w3id.org/fep/f12e/AttributionRequest)

Is defined by
: [FEP-f12e](https://w3id.org/fep/f12e)


## Examples

Example of an AttributionAuthorization

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "AttributionAuthorization",
  "id": "https://example.org/actors/1/attributions/1",
  "attributedTo": "https://example.org/actors/1",
  "object": {
    "type": "Relationship",
    "subject": "https://example.com/article/1",
    "relationship": "https://schema.org/author",
    "object": "https://example.org/actors/1"
  }
}
    ```
