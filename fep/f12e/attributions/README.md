# attributions

URI
: `https://w3id.org/fep/f12e/attributions`

Label
: Attributions Collection

Comment
: An ActivityStreams `Collection` of `Relationship` items that list the parties that have attributed importance to an object.

Domain
: [Object](https://www.w3.org/ns/activitystreams#Object)

Range
: [Collection](https://www.w3.org/ns/activitystreams#Collection) (See [Activity Streams 2.0 Core specification](https://www.w3.org/TR/activitystreams-core/#collection) for a complete description)

Required
: No

Functional
: No

Is defined by
: [FEP-f12e](https://w3id.org/fep/f12e)


## Examples

Example usage of attributions (non-normative): an article

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "Article",
  "id": "https://example.com/article/1",
  "name": "Paper on the Fediverse",
  "attributions": {
    "type": "Collection",
    "totalItems": 3,
    "items": [
      {
        "type": "Relationship",
        "relationship": "https://schema.org/author",
        "object": "https://example.org/actors/1",
        "attributionAuthorization": "https://example.org/actors/1/attributions/1"
      },
      {
        "type": "Relationship",
        "relationship": "https://schema.org/contributor",
        "object": "https://example.net/actors/2",
        "attributionAuthorization": "https://example.net/actors/2/attributions/7"
      },
      {
        "type": "Relationship",
        "relationship": "https://schema.org/contributor",
        "object": {
          "type": "Link",
          "name": "Some Person",
          "href": "https://some.persons.personal.website"
        }
      }
    ]
  },
  "content": "FEP-f12e introduced..."
}
    ```

Example usage of attributions (non-normative): an event

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Event",
  "id": "https://example.com/events/1",
  "name": "Fediverse Meetup",
  "attributions": {
    "type": "Collection",
    "totalItems": 2,
    "items": [
      {
        "type": "Relationship",
        "relationship": "https://schema.org/organizer",
        "object": "https://example.org/groups/1",
        "attributionAuthorization": "https://example.org/groups/1/attributions/3"
      },
      {
        "type": "Relationship",
        "relationship": "https://schema.org/organizer",
        "object": "https://example.com/actors/3"
      }
    ]
  }
}
    ```

Example usage of attributions (non-normative): a custom relationship

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Video",
  "id": "https://example.com/videos/1",
  "name": "Interview",
  "attributions": {
    "type": "Collection",
    "totalItems": 1,
    "items": [
      {
        "type": "Relationship",
        "relationship": "https://vocab.example/terms/interviewee",
        "object": "https://example.org/actors/4",
        "attributionAuthorization": "https://example.org/actors/4/attributions/2"
      }
    ]
  }
}
    ```
