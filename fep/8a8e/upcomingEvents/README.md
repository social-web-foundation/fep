# upcomingEvents

URI
: `https://w3id.org/fep/8a8e/upcomingEvents`

Label
: Collection of upcoming Events

Comment
: An ActivityStreams Collection of Event objects that have a startTime property in the future.

Is defined by
: [FEP-8a8e](https://w3id.org/fep/8a8e)


## Examples

Example usage of upcomingEvents

```json
    {
      "@context": "https://w3id.org/fep/8a8e",
      "@type": "as:Actor",
      "upcomingEvents": {
        "@type": "Collection",
        "items": [
          { "@type": "Event", "startTime": "2025-06-01T12:00:00Z" },
          { "@type": "Event", "startTime": "2025-07-15T15:30:00Z" }
        ]
      }
    }
    ```
