---
slug: "8a8e"
authors: André Menrath <andre.menrath@event-federation.eu>
status: DRAFT
dateReceived: 2024-10-27
trackingIssue: https://codeberg.org/fediverse/fep/issues/XX
discussionsTo: https://socialhub.activitypub.rocks/t/events-interoperability-validation-minimum-requirements-common-extensions/3849/
---
# FEP-8a8e: A common approach to using the Event object type

## Summary

ActivityStreams defines the [Object Type `Event`](https://www.w3.org/TR/activitystreams-vocabulary/#dfn-event). In real-world applications, the event object immediately showed the need for extension. Applications featuring `Event` objects have often chose to add additional attributes and clarifications (i.e., interpretations) in order to implement their particular use case. This proposal clarifies and extends the ActivityPub standard to address the needs that have arisen in real-world implementations.

This includes guidelines for the minimal interoperable event, handling of RSVP ("répondez s'il vous plaît", i.e., attendee management, and side effects), attendee capacities, physical location addresses, virtual locations, timezone, and clarification of how to control the visibility of events in federation.

These differences in how the aforementioned features are implemented have led to fragmentation in how events are published, discovered, and managed across platforms.

## History

Fediverse applications, such as Mobilizon, Friendica, Gancio, and Hubzilla, have adopted varying approaches for handling ActivityPub events. Their different aims and the varying use cases have led to fragmentation in how events are published, discovered, and managed across federation.

Friendica and Hubzilla, for instance, follow the example set by ActivityStreams 2.0, using `Invite` for events, which seems to be very suited for smaller, more private gatherings, such as a birthday party. `Invite` seems natural when visibility is intentionally limited. On the other hand, applications like Mobilizon or Gancio have a focus on announcing public events and therefore chose to make use of the `Create` activity. This seems reasonable, since public events should as well be discoverable by anonymous actors, even by people who do not have an account in the Fediverse. This is achieved through federated event calendars, which are assembled by the instance administrators, who can add various federated event sources by following federated ActivityPub actors.

Within Mobilizon, for historical and internal reasons, the federated visibility of events is currently still controlled by whether a `Group` has published the `Event` or not, and whether the `Event` has also been announced at least once, rather than using `to`/`cc` (e.g., like Mastodon's "public silent"). In federation with other applications, this and other discrepancies led to issues, which have proven to be huge blockers. That's why this FEP sets out to define a common ground.

## Requirements

The key words “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this specification are to be interpreted as described in [RFC-2119](https://datatracker.ietf.org/doc/html/rfc2119.html).

**The context of attributes:** Attributes that have no context prefix are to be interpreted as being in the `https://www.w3.org/ns/activitystreams` context.

## Object Type Event
The ActivityStreams specification already defines Objects of type Event by inheriting properties from the Object type so some of the properties useful to describe an event are already specified but some others are missing and a clear specification will help.

An `Object` Type `Event` *MUST* specify at least the following properties:

- [`name`](https://www.w3.org/TR/activitystreams-vocabulary/#dfn-name): A simple, human-readable, plain-text title for the event. HTML markup *MUST NOT* be included. Values for the name *MUST NOT* be an empty string and the name *MAY* be expressed using multiple language-tagged values.

- [`startTime`](https://www.w3.org/TR/activitystreams-vocabulary/#dfn-startTime): The date and time describing the moment the event began or is scheduled to begin in the format as specified in the [Activity Stream 2.0 specification](https://www.w3.org/TR/activitystreams-core/#dates).

- [`endTime`](https://www.w3.org/TR/activitystreams-vocabulary/#dfn-endTime): The date and time when the event ends or is scheduled to end in the format as specified in the [Activity Stream 2.0 specification](https://www.w3.org/TR/activitystreams-core/#dates). If the event is open-ended, it must include an end time at which applications (not humans) can treat the event as having ended.


```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Event",
  "id": "https://example.org/foo",
  "name": "New years party",
  "startTime": "2014-12-31T23:00:00Z",
  "endTime": "2015-01-01T06:00:00Z"
}
```

### Time zone
The `timezone` property is introduced to support time zone information for events, enabling consistent handling of local "wall times".

> It is important to note that the "time-offset" component in `startTime` and `endTime` property does not correlate to time-zones, and while times that include the "time-offset" component work well for timestamps, they cannot be reliably converted to and from local "wall times" without additional information and processing.
> [https://www.w3.org/TR/activitystreams-core/#dates](https://www.w3.org/TR/activitystreams-core/#dates)

For this reason, if the `Event` is primarily conducted in a single specific time-zone, the application *SHOULD* set the named `timezone`.

In case the `timezone` property is specified it *MUST* be a specific IANA time zone identifier included in the [IANA Time Zone Database](https://data.iana.org/time-zones/tz-link.html) (often called tz or zoneinfo, see [https://www.w3.org/TR/timezone/#time-zone-identifiers](https://www.w3.org/TR/timezone/#time-zone-identifiers)).

When receiving an `Event` with a `timezone` property specified, the receiving application *SHOULD* use that information for displaying the times.

<!--
  Evaluated @id / @type for @context:
   https://iana.org/time-zones
   https://www.w3.org/2006/timezone
   https://www.w3.org/2006/time#timezone
   https://www.w3.org/2007/uwa/context/common.owl#tzName
   https://www.w3.org/2007/uwa/context/common.owl#TimeZone
   https://www.w3.org/TR/timezone/
   https://www.w3.org/TR/timezone/#tz-definition
   https://www.w3.org/TR/timezone/#time-zone-identifiers -->

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
      "timezone": "http://www.w3.org/2006/time#timezone"
    }
  ],
  "type": "Event",
  "id": "https://example.org/foo",
  "name": "New years party",
  "startTime": "2014-12-31T23:00:00+01:00",
  "timezone": "Europe/Rome"
}
```

### Events with Open End

If the event is open-ended, or the `endTime` is not intended to be displayed to humans, the `https://event-federation.eu/ns/#displayEndTime` attribute *SHOULD* be used and set to `"false"`.

Receiving an `Event` with an `endTime` set and no `https://event-federation.eu/ns/#displayEndTime` set, it *MUST* be treated as if `https://event-federation.eu/ns/#displayEndTime` is set to `"true"`, requiring the   `endTime` to be displayed.

If an `Event` is received with no `endTime` set, the `Event` *MUST* be treated as if `https://event-federation.eu/ns/#displayEndTime` were set to `"false"` to avoid misleading users. In such cases, the receiving application *MAY* infer an appropriate `endTime` based on its requirements.

### Location

#### Physical

For adding information about the physical address of an `Event` the `Place` object within the events `location` property *SHOULD* be extended via the attribute `address` which is of type `https://schema.org/address`.

This allows the address to be given as a simple text input as well as a structured `https://schema.org/PostalAddress`. Applications *MUST* be able to transmogrify both incoming types to their internal representation.

Example with address of type `https://schema.org/PostalAddress`:

```json
{
  "@context": [
    "https://schema.org",
    "https://www.w3.org/ns/activitystreams"
  ],
  "type": "Event",
  "id": "https://example.org/new-year-party",
  "name": "New years party",
  "startTime": "2014-12-31T23:00:00-08:00",
  "location": {
    "id": "",
    "type": "Place",
    "name": "Foo Bar",
    "address": {
      "type": "PostalAddress",
      "addressCountry": "Austria",
      "addressLocality": "Fediverse Town",
      "addressRegion": "Steiermark",
      "postalCode": "8010",
      "streetAddress": "15 Fediverse Street"
    }
  }
}
```

Example with pure text address:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
      "address": "https://schema.org/address"
    }
  ],
  "type": "Event",
  "id": "https://example.org/new-year-party",
  "name": "New years party",
  "startTime": "2014-12-31T23:00:00-08:00",
  "location": {
    "type": "Place",
    "name": "Foo Bar",
    "address": "15 Fediverse Street, 8010 Fediverse Town, Austria"
  }
}
```

#### Virtual

> **To Do**  
> Or use a custom attribute `https://event-federation.eu/ns#isVirtualLocation`

An online Location *SHOULD* be represented by using a multi-type of `Place` and `https://schema.org/VirtualLocation`. Note that it is important that `Place` *MUST* be the first item in that case. Applications *SHOULD* at least set and be able to make use of `name` and `url`.

```json
{
  "@context": [
    "https://schema.org",
    "https://www.w3.org/ns/activitystreams"
  ],
  "type": "Event",
  "id": "https://example.org/new-year-party",
  "name": "Fediverse Moderation Meeting",
  "startTime": "2014-12-31T23:00:00-08:00",
  "location": {
    "type": ["Place", "VirtualLocation"],
    "name": "Jitsi Meet Meeting Link",
    "url": "https://jit.si/fediverse-moderation-meeting"
  }
}
```

#### Hybrid

Using multiple entries in `location` makes it easy to define multiple virtual and physical locations. When not supporting multiple entries in `location` applications *MUST* use the first item.

```json
{
  "@context": [
    "https://schema.org",
    "https://www.w3.org/ns/activitystreams"
  ],
  "type": "Event",
  "id": "https://example.org/new-year-party",
  "name": "Discussion about the Fediverse",
  "startTime": "2014-12-31T23:00:00-08:00",
  "location": [
    {
      "type": ["Place"],
      "name": "Fediverse University",
      "url": "https://university.example.com",
      "address": "15 Fediverse Street, 1337 Fediverse Town, Fediverse Country"
    },
    {
      "type": ["Place", "VirtualLocation"],
      "name": "Big Blue Button Participation Link",
      "url": "https://bbb.example.com/meeting-room-1"
    },
    {
      "type": ["Place", "VirtualLocation"],
      "name": "Live Stream",
      "url": "https://peertube.example.com/fediverse-discussion"
    }
  ]
}
```


### RSVP (Attendee Management)

#### Not handling RSVP

If the event creator or the event creator's application does not handle joins via ActivityPub it *MUST* always respond to `Join` activities with an `Ignore` response, where the attribute `object` *MUST* either contain the ID of the `Join` activity, or contain a `Join` object with the `target` being set to the event-objects ID, where the former is preferred.

This *SHOULD* be made clear beforehand by setting `https://joinmobilizon.org/ns#joinMode` to `none`.

> **Note**
> `none` is currently not part of `https://joinmobilizon.org/ns#joinMode` yet.

#### Handle Joins, but not via ActivityPub

If an application does not handle joins of an `Event` via ActivityPub, but knows of an external URL which handles the attendee management `https://joinmobilizon.org/ns#joinMode` *SHOULD* be set to `external`. If `joinMode` is set to `external`, also `https://joinmobilizon.org/ns#externalParticipationUrl` *SHOULD* be set.

> **Note**
> The "*SHOULD*" is not in line with Mobilizon's current definition. But as the join mode could also be made clear via the event's description in the content, or just not be clear yet, it should be allowed.

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
      "joinMode": "https://joinmobilizon.org/ns#joinMode"
    }
  ],
  "type": "Event",
  "id": "https://example.org/foo",
  "name": "New years party",
  "startTime": "2014-12-31T23:00:00-08:00",
  "joinMode": "external",
  "externalParticipationUrl": "https://example.org/foo#regisiter"
}
```

Note that `externalParticipationUrl` *MAY* also be a `mailto`-URL, which is a way of handling event participants that is still used quite frequently by many organizers.

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
      "joinMode": "https://joinmobilizon.org/ns#joinMode",
      "externalParticipationUrl": "https://joinmobilizon.org/ns#externalParticipationUrl"
    }
  ],
  "type": "Event",
  "id": "https://example.org/fediverse-workshop",
  "name": "Fediverse Workshop",
  "startTime": "2014-12-31T23:00:00-08:00",
  "joinMode": "external",
  "externalParticipationUrl": "mailto:team@fediverse-workshop.org"
}
```

#### Showing RSVP status via ActivityPub

To specify the maximum number of attendees for an `Event`, applications *SHOULD* use the `https://schema.org/maximumAttendeeCapacity`.

Remaining attendee capacity *SHOULD* be shown indirectly via using the Collection `https://event-federation.eu/ns#attendees`. This is a list of all actors who have successfully joined the event, i.e. when an `Accept` activity is sent as a response to the actor requesting to join, the actor is added as a side effect. The `attendees` collection *MUST* be either an `OrderedCollection` or a `Collection` and *MAY* be filtered by the privileges of an authenticated user, or as appropriate if no authentication is given.

```json
{
  "@context": [
    "https://schema.org",
    "https://www.w3.org/ns/activitystreams",
    {
      "attendees": {
        "@id": "https://event-federation.eu/ns#attendees ",
        "@type": "https://www.w3.org/TR/activitystreams-vocabulary/#dfn-collection"
      }
    }
  ],
  "type": "Event",
  "id": "https://example.org/foo-bar-party",
  "name": "New years party",
  "startTime": "2014-12-31T23:00:00-08:00",
  "maximumAttendeeCapacity": 100,
  "attendees": {
     "type": "Collection",
     "id": "https://example.org/foo-bar-party/attendees",
     "totalItems": 84
  }
}
```

### Event Banner and Poster Images

#### Flyer

If the event has an image in the style of a flyer or a share-pic which is representing the whole event (i.e., is also containing at least the name and start-date in the image) this image *SHOULD* be set using the `image` attribute.

#### Banner

If the `Event` has a particular banner image, this image *SHOULD* be set as the first `attachment` of type `Image` (type `Document` is also valid). To indicate that an image from within the `attachment` attribute of an `Event` should be preferred over the flyer/share-pic image(s) within `image` attribute, for the use of list pages and header images, the attribute `https://event-federation.eu/ns#isThumbnail` *SHOULD* be set.

Federated event calendars usually have thumbnail images with fixed aspect ratios. Therefore, if the image's aspect ratio is not close to 16:9 `https://docs.joinmastodon.org/spec/activitypub/#focalPoint` *SHOULD* be set.

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
      "toot": "http://joinmastodon.org/ns#",
      "focalPoint": {
        "@container": "@list",
        "@id": "toot:focalPoint"
      }
    }
  ],
  "type": "Event",
  "id": "https://example.org/new-year-party",
  "name": "New years party",
  "startTime": "2014-12-31T23:00:00-08:00",
  "image": {
    "type": "Image",
    "mediaType": "image/jpeg",
    "url": "https://example.com/images/new-year-party-flyer.png",
    "focalPoint": [
      -0.55,
      0.43
    ]
  }
}
```

### Discoverability

Fediverse applications that feature `Event` objects *MAY* provide public calendars, search functions or grouped visualization pages (e.g., for tags or categories) that display events from multiple federated sources.
In both cases these *MUST* never include events from federation that do not have `https://www.w3.org/ns/activitystreams#Public` (also `as:Public` or `Public` is valid) set in `to`. However, they *MAY* appear within a local representation of a remote actor, if `Public` set in `cc`.

The discoverability of an incoming event from federation *MUST NOT* be controlled by the type of the actor set in `attributedTo` or by the `Activity` the event was received (e.g., `Announce`, `Create`).

### Organizers

Events *SHOULD* indicate their organizers by using `https://event-federation.eu/ns#organizers`.
The `organizers` collection helps provide clarity about the event's management, supports federated discovery, and improves interoperability across platforms.

The value of the `organizers` field *MUST* be either an `OrderedCollection` or a `Collection`.
The `items` within this collection *MAY* include [actors](https://www.w3.org/TR/activitystreams-core/#actors),  or [links](https://www.w3.org/TR/activitystreams-core/#link).
If the organizer is a non-ActivityPub entity (e.g., a website or organization without an actor), it *SHOULD* use a link.

```json
{
  "@context": [
    "https://schema.org",
    "https://www.w3.org/ns/activitystreams",
    {
      "organizer": {
        "@id": "https://event-federation.eu/ns#organizer",
        "@type": "https://www.w3.org/TR/activitystreams-vocabulary/#dfn-collection"
      }
    }
  ],
  "type": "Event",
  "id": "https://example.org/foo-bar-party",
  "name": "New Year's Party",
  "startTime": "2014-12-31T23:00:00-08:00",
  "organizers": {
    "type": "Collection",
    "id": "https://example.org/foo-bar-party/organizers",
    "totalItems": 3,
    "first": {
      "type": "CollectionPage",
      "partOf": "https://example.org/foo-bar-party/organizers",
      "items": [
        "https://example.social/users/johnmastodon",
        "https://example.org/somewebsite",
        {
          "type": "Organization",
          "id": "https://example.events/actors/eventorganizer",
          "context": "https://example.events/actors/eventorganizer/accept/example.org-foo-bar-party-offer"
        }
      ]
    }
  }
}
```

#### Explicit Non-Disclosure

A `organizer` with `totalItems: 0` or an empty `items` attribute *MUST* explicitly signal that the event's organizers are intentionally not disclosed. This indicates a deliberate choice to withhold organizer information and overrides any assumptions about organizers based on other fields.

#### Fallback to `attributedTo`:

If the `organizers` property is omitted, it *MAY* be inferred that the actors in the `attributedTo` property are the event's organizers. For events with multiple organizers, it is *RECOMMENDED* to provide an organizers collection to avoid ambiguity, and be compatible with applications that do not support arrays in `attributedTo`.

## Credits

This work would not have been possible without the support of [NLnet foundation](https://nlnet.nl/) and [NGI Zero](https://nlnet.nl/NGI0/).

Thanks are also expressed to the people at OFFDEM who laid out [the beginnings of this document](https://event-federation.eu/2024/02/10/fediversity-at-o%e2%82%84ffdem/).

Special grants to Laurin Weger, for being available for many timely discussions.

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.