# OrganizerCollection

URI
: `https://w3id.org/fep/8a8e/OrganizerCollection`

Label
: An Event's Organizer Collection

Comment
: Inherits all properties from `<https://www.w3.org/ns/activitystreams#Collection>` with the addition that the `items` may also include `https://schema.org/Person` or `https://schema.org/Organization`.

Subclass of
: [Object](https://www.w3.org/ns/activitystreams#Collection)

See also
: [organizers](https://w3id.org/fep/8a8e/organizers)

Is defined by
: [FEP-8a8e](https://w3id.org/fep/8a8e)


## Examples

Example of an OrganizerCollection with different items

```json
    {
      "@type": "OrganizerCollection",
      "items": [
        { "@type": "https://www.w3.org/ns/activitystreams#Group", "name": "ActivityPub Group Actor", "id": "https://example.org/actors/group1"},
        { "@type": "https://www.w3.org/ns/activitystreams#Link", "href": "https://organizer1.example.org"},
        { "@type": "https://schema.org/Person", "name": "Alice" },
        { "@type": "[sc:](https://schema.org/)Organization", "name": "Event Co." }
      ]
    }
    ```
