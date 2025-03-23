# attendees

URI
: `https://w3id.org/fep/8a8e/attendees`

Label
: Attendees of an Event

Comment
: 

Is defined by
: [FEP-8a8e](https://w3id.org/fep/8a8e)

Range
: [Collection](https://w3id.org/fep/8a8e/AttendeesCollection) (ActivityStreams Type)

Required
: No

Functional
: No


## Examples

Example usage of attendees

```json
    {
      "@context": "https://www.w3.org/ns/activitystreams",
      "@type": "Event",
      "attendees": {
        "@type": "https://w3id.org/fep/8a8e/OrganizersCollection",
        "totalItems": 4,
        "items": [
          { "@type": "as:Actor", "name": "ActivityPub Group Actor", "id": "https://example.org/actors/group1"},
          { "@type": "as:Link", "href": "https://organizer1.example.org"},
          { "@type": "sc:Person", "name": "Alice" },
          { "@type": "sc:Organization", "name": "Event Co." }
        ]
      }
    }
    ```
