---
slug: "4f18"
authors: Evan Prodromou <evanp@socialwebfoundation.org>
status: DRAFT
dateReceived: 2026-10-03
discussionsTo: https://codeberg.org/evanp/fep/issues
---
# FEP-4f18: ActivityPub Network Time

## Summary

Logical clocks capture the causal ordering of events in a system. This proposal introduces a logical clock system for the ActivityPub network.

## Introduction

Leslie Lamport introduced the idea of logical clocks in [Time, Clocks, and the Ordering of Events in a Distributed System]. A logical clock can capture the causal ordering of events in a distributed system. Lamport calls it the "happened-before" relationship.

This FEP defines a scalar logical clock system for the ActivityPub network. The time is represented by a 64-bit integer value shared between servers on the network. Unlike Lamport's distributed systems, the unit of change in the ActivityPub network is the activity. Activities are assigned the logical clock time from when they were performed; other objects have the clock time of the last activity that changed their state.

## Terms

The JSON-LD context for ActivityPub network time is available at <https://w3id.org/fep/4f18>. Its contents are as follows:

```json
{
  "@context": {
    "xsd":  "http://www.w3.org/2001/XMLSchema#",
    "networkTime": {
      "@id": "https://w3id.org/fep/4f18#networkTime",
      "@type": "xsd:unsignedLong"
    }
  }
}
```

### networkTime

`networkTime` is a 64-bit unsigned integer representing the logical clock time of an object.

## Specification

- A [Federated Server](https://www.w3.org/TR/activitypub/#specification-profiles) SHOULD maintain a persistent logical clock value as a 64-bit unsigned integer.
- A Federated Server SHOULD initialize its logical clock value to 0.
- When it generates a new activity, the Federated Server SHOULD increment its logical clock value by 1, then set the `networkTime` property of the activity to the new logical clock value.
- When it modifies the state of any non-activity object, including actors, content objects, and collections, the Federated Server SHOULD set the `networkTime` property of the object to the maximum of its current `networkTime` property and the `networkTime` property of the activity that caused the modification. Modifications of the state include addition of properties, changes to the values of properties, and removal of properties, but not changes to the values of other objects referred to by properties the object.
- When it [retrieves any ActivityPub object](https://www.w3.org/TR/activitypub/#retrieving-objects) from a remote server, if the object has a `networkTime` property, the Federated Server SHOULD set its logical clock to the maximum of its current value and the value of the object's `networkTime` property.
- When an activity with a `networkTime` property from a remote server is [delivered](https://www.w3.org/TR/activitypub/#delivery), the Federated Server SHOULD set its logical clock to the maximum of its current value and the value of the activity's `networkTime` property.

## Examples

The following examples show how a Federated Server can maintain a logical clock value and assign `networkTime` properties to activities and other objects.

### Local Create activity

The Federated Server has a logical clock value of 32102. An actor creates a new `Note` object. The Federated Server increments its logical clock value 32103, and generates a `Create` activity with a `networkTime` property set to the new value:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/create/15585",
  "type": "Create",
  "actor": "https://social.example/person/5489",
  "object": "https://social.example/note/5595",
  "to": "as:Public",
  "networkTime": 32103
}
```

The `Note` object has the same `networkTime` value as the `Create` activity:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/note/5595",
  "type": "Note",
  "attributedTo": "https://social.example/person/5489",
  "content": "Hello, World!",
  "to": "as:Public",
  "networkTime": 32103
}
```

The `Create` activity is added to the actor's `outbox` collection, which increments the collection's `totalItems` property. So, the `networkTime` property of collection is set to the same value as the `Create` activity:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://w3id.org/fep/5711",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/collection/17344",
  "type": "OrderedCollection",
  "attributedTo": "https://social.example/person/5489",
  "outboxOf": "https://social.example/person/5489",
  "totalItems": 9670,
  "first": "https://social.example/page/28891",
  "to": "as:Public",
  "networkTime": 32103
}
```

The `Create` activity is added to the `orderedItems` property of the first page of the outbox collection, so the page's `networkTime` is set to the same value as the `Create` activity:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/page/28891",
  "type": "OrderedCollectionPage",
  "attributedTo": "https://social.example/person/5489",
  "partOf": "https://social.example/collection/17344",
  "orderedItems": [
    "https://social.example/create/15585",
    "https://social.example/create/18031",
    "https://social.example/follow/25127"
  ],
  "to": "as:Public",
  "networkTime": 32103
}
```

The actor refers to the `outbox` collection, but otherwise its properties are not changed. So, its `networkTime` property is not changed:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/person/5489",
  "type": "Person",
  "inbox": "https://social.example/collection/15864",
  "outbox": "https://social.example/collection/17344",
  "to": "as:Public",
  "networkTime": 28676
}
```

### Local Like activity

The Federated Server has a logical clock value of 282539. An actor likes a `Note` object. The Federated Server increments its logical clock value 282540, and generates a `Like` activity with a `networkTime` property set to the new value:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/like/343575",
  "type": "Like",
  "actor": "https://social.example/person/5489",
  "object": "https://social.example/note/29098",
  "to": "as:Public",
  "networkTime": 282540
}
```

The `Like` activity does not modify the `Note`, so the note's `networkTime` property is not changed:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/note/29098",
  "type": "Note",
  "attributedTo": "https://social.example/person/24611",
  "content": "Now is the time for all good people to come to the aid of their party",
  "likes": {
    "id": "https://social.example/collection/29517",
    "totalItems": 1,
    "type": "Collection"
  },
  "to": "as:Public",
  "networkTime": 8263
}
```

Note that the `totalItems` property, which is changed, is not a property of the `Note` object, but of the `Collection` object.

The `Like` activity does modify the `Note`'s `likes` collection, so the collection's `networkTime` property is set to the `Like` activity's network time:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://w3id.org/fep/5711",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/collection/29517",
  "type": "Collection",
  "totalItems": 1,
  "items": [
     "https://social.example/like/343575"
  ],
  "attributedTo": "https://social.example/person/24611",
  "likesOf": "https://social.example/note/29098",
  "to": "as:Public",
  "networkTime": 282540
}
```

The `Like` activity modifies the actor's `liked` collection, so the Federated Server sets its `networkTime` to the network time of the `Like` activity:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://w3id.org/fep/5711",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/collection/19142",
  "type": "Collection",
  "totalItems": 1,
  "items": [
     "https://social.example/note/29098"
  ],
  "attributedTo": "https://social.example/person/5489",
  "likedOf": "https://social.example/person/5489",
  "to": "as:Public",
  "networkTime": 282540
}
```

The actor's outbox collection and outbox collection page are modified as in [Local Create activity](#local-create-activity).

### Remote Create activity

The Federated Server has a logical clock value of 397739. A `Create` activity is received at an actor's inbox.

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://remote.example/create/65999",
  "type": "Create",
  "actor": "https://remote.example/person/11725",
  "object": {
    "id": "https://remote.example/note/52346",
    "type": "Note",
    "attributedTo": "https://remote.example/person/11725",
    "inReplyTo": "https://social.example/note/31872",
    "to": ["as:Public", "https://social.example/person/73385"],
    "networkTime": 429505
  },
  "to": ["as:Public", "https://social.example/person/73385"],
  "networkTime": 429505
}
```

The activity's `networkTime` value is higher than the Federated Server's logical clock value, so the Federated Server sets it logical clock value to 429505.

The received activity is added to the receiving actor's `inbox` collection, which changes the `totalItems` property, so the collection's `networkTime` is updated to the activity's `networkTime`.

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://w3id.org/fep/5711",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/collection/29733",
  "type": "OrderedCollection",
  "attributedTo": "https://social.example/person/73385",
  "inboxOf": "https://social.example/person/73385",
  "totalItems": 893,
  "first": "https://social.example/page/53167",
  "networkTime": 429505
}
```

The first inbox page is also modified, so its `networkTime` is also updated:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/page/53167",
  "type": "OrderedCollectionPage",
  "attributedTo": "https://social.example/person/73385",
  "partOf": "https://social.example/collection/29733",
  "orderedItems": [
    "https://remote.example/create/65999"
  ],
  "networkTime": 429505
}
```

The `object` of the received activity is a `Note` in reply to a local `Note`. The local note is not modified, but its `replies` collection is, so the Federated Server updates its `networkTime` property:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://w3id.org/fep/5711",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/collection/5904",
  "type": "OrderedCollection",
  "attributedTo": "https://social.example/person/73385",
  "repliesOf": "https://social.example/note/31872",
  "totalItems": 2,
  "orderedItems": [
    "https://remote.example/note/52346",
    "https://social.example/note/31380"
  ],
  "to": "as:Public",
  "networkTime": 429505
}
```

### Remote Accept activity

The Federated Server has a logical clock value of 561624. It receives an `Accept` activity at its `sharedInbox` endpoint.

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://remote.example/accept/65999",
  "type": "Accept",
  "actor": "https://remote.example/person/11725",
  "object": "https://social.example/follow/54973",
  "to": "https://social.example/person/73385",
  "networkTime": 519645
}
```

The activity's `networkTime` value is lower than the Federated Server's logical clock value, so the Federated Server leaves its logical clock value unchanged.

The activity changes the local actor's `following` collection. The activity's `networkTime` is greater than the collection's `networkTime`, so the Federated Server updates the collection's `networkTime`.

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://w3id.org/fep/5711",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/collection/94506",
  "type": "OrderedCollection",
  "attributedTo": "https://social.example/person/73385",
  "followingOf": "https://social.example/person/73385",
  "totalItems": 75,
  "first": "https://social.example/page/66877",
  "to": "as:Public",
  "networkTime": 519645
}
```

The first page of the `following` collection is also updated:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://social.example/page/66877",
  "type": "OrderedCollectionPage",
  "attributedTo": "https://social.example/person/73385",
  "partOf": "https://social.example/collection/94506",
  "orderedItems": [
    "https://remote.example/person/11725"
  ],
  "to": "as:Public",
  "networkTime": 519645
}
```

The receiving actor's inbox collection and inbox collection page are modified as in [remote Create activity](#remote-create-activity). Their `networkTime` properties are each set to the maximum of their existing value and the `Accept` activity's `networkTime` value of 519645, even though the Federated Server's logical clock value is higher.

### Fetching a remote ActivityPub object

The Federated Server has a logical clock value of 624844. It fetches a `Note` object from a remote server:

```json
{
  "@context": [
    "https://w3id.org/fep/4f18",
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://remote.example/note/69038",
  "type": "Note",
  "to": "as:Public",
  "attributedTo": "https://remote.example/person/11725",
  "content": "Hello, World!",
  "networkTime": 742281
}
```

The note's `networkTime` value is higher than the Federated Server's logical clock value, so the Federated Server updates its logical clock value to the network time of the note.

## Security Considerations

Remote servers can include network time values that exhaust or overflow the shared logical clock space. For example, a remote server could send an activity with `networkTime` set to 2^64-1, such that the Federated Server will overflow the logical clock on its next activity.

One mitigation is to disallow changes to the logical clock value with too high a delta from the current value. This can be a fixed maximum, or could be adaptive, depending on the historical change of the logical clock value.

Another mitigation is to establish a trust metric with remote servers, and only set the logical clock value when network time is received from a trusted server.

## Appendix A: Scale

A 64-bit integer should be sufficient for this logical clock. [Fedidb.com] shows an average of 0.98 statuses (that is, notes and other content) per user per month on the ActivityPub network for the six months ending in September 2026. New content is not the only type of activity distributed on the network; we here assume an outer bound of about 10x multiplier to account for likes, follows, shares, edits, deletes, and other activities performed by an actor.

We can scale this behaviour to account for global growth of the Fediverse. A global population of 10 billion people, at about 10 activities per month, would create 100 billion activities per month. A 64-bit integer can account for this rate of activity distribution for 15 million years.

JSON, as defined in [RFC 8259], uses floating-point numbers with the [IEEE 754] standard. This limits numbers that can be represented in JSON to 2^53. At the rate of 100 billion activities per month, that allows 7505 years of logical clock values.

## References

- Christine Lemmer-Webber, Jessica Tallon, Erin Shepherd, Amy Guy, Evan Prodromou, [ActivityPub], 2018
- Leslie Lamport, [Time, Clocks, and the Ordering of Events in a Distributed System], 1978
- Dan Supernault, [Fedidb.com], 2026.
- Tim Bray, [RFC 8259], 2017.
- IEEE, "IEEE Standard for Floating-Point Arithmetic", [IEEE 754], 2019.

[ActivityPub]: https://www.w3.org/TR/activitypub/
[Time, Clocks, and the Ordering of Events in a Distributed System]: https://lamport.azurewebsites.net/pubs/time-clocks.pdf
[RFC 8259]: https://www.rfc-editor.org/info/rfc8259/
[IEEE 754]: https://standards.ieee.org/ieee/754/6210/

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
