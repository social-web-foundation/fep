# AttributionRequest

URI
: `https://w3id.org/fep/f12e/AttributionRequest`

Label
: Attribution Request

Comment
: An activity by which the publisher of an object asks an actor for consent to be listed in the `attributions` of that object. Its `object` is the `Relationship` the actor is asked to consent to.

Subclass of
: [Activity](https://www.w3.org/ns/activitystreams#Activity)

See also
: [AttributionAuthorization](https://w3id.org/fep/f12e/AttributionAuthorization)

Is defined by
: [FEP-f12e](https://w3id.org/fep/f12e)


## Examples

Example of an AttributionRequest

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "AttributionRequest",
  "id": "https://example.com/actors/publisher/activities/1",
  "actor": "https://example.com/actors/publisher",
  "to": "https://example.org/actors/1",
  "object": {
    "type": "Relationship",
    "subject": "https://example.com/article/1",
    "relationship": "https://schema.org/author",
    "object": "https://example.org/actors/1"
  }
}
    ```

Example of an Accept of an AttributionRequest

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "Accept",
  "id": "https://example.org/actors/1/activities/5",
  "actor": "https://example.org/actors/1",
  "to": "https://example.com/actors/publisher",
  "object": {
    "type": "AttributionRequest",
    "id": "https://example.com/actors/publisher/activities/1",
    "actor": "https://example.com/actors/publisher",
    "to": "https://example.org/actors/1",
    "object": {
      "type": "Relationship",
      "subject": "https://example.com/article/1",
      "relationship": "https://schema.org/author",
      "object": "https://example.org/actors/1"
    }
  },
  "result": "https://example.org/actors/1/attributions/1"
}
    ```

Example of a Delete that revokes an AttributionAuthorization

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "Delete",
  "id": "https://example.org/actors/1/activities/9",
  "actor": "https://example.org/actors/1",
  "to": "https://example.com/actors/publisher",
  "object": {
    "type": "Tombstone",
    "id": "https://example.org/actors/1/attributions/1",
    "formerType": "AttributionAuthorization",
    "attributedTo": "https://example.org/actors/1",
    "object": {
      "type": "Relationship",
      "subject": "https://example.com/article/1",
      "relationship": "https://schema.org/author",
      "object": "https://example.org/actors/1"
    }
  }
}
    ```
