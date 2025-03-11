---
slug: "1d80"
authors: Alan "JollyRoberts" Roberts <jolly.development@gmail.com>
status: DRAFT
dateReceived: 2025-03-11
discussionsTo: https://forum.example/topics/xxxx
---
# FEP-1d80: Feed Actor - a way to federate a collection of Group actors


## Summary

ActivityPub `Group` actors have been successfully used to implement federated forums/communities. However many users have found that there is a lot of duplication of Groups on different servers. This defines a new `Feed` actor as a way to federate collections of `Group` actors.


## Requirements

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this specification are to be interpreted as described in [RFC-2119].


## Context

Users have found that there can be multiple similarly themed federated communities provided by different instances. 

As an example [technology@lemmy.zip](https://lemmy.zip/c/technology), [technology@lemmy.ml](https://lemmy.ml/c/technology), [technology@lemmy.world](https://lemmy.world/c/technology), [technology@beehaw.org](https://beehaw.org/c/technology), and [tech@programming.dev](https://programming.dev/c/tech) all have similar themes, and all have their own valid ways of running a federated forum. 

Many "Threadiverse" users are following all of these forums and more. Many of those users have asked for the ability to organize communities themselves in a personal way as seen in the example issues linked below:

PieFed Issues
* [Custom Curated Feeds for Content Organization](https://codeberg.org/rimu/pyfedi/issues/117)
* [\[Idea\] Multiple subscription feeds](https://codeberg.org/rimu/pyfedi/issues/403)

Lemmy Issues
* [Support for grouping communities / multi-communities](https://github.com/LemmyNet/lemmy/issues/818)
* [Subscription Groups](https://github.com/LemmyNet/lemmy/issues/3875)

MBin Issue
* [Implement MultiMag Views](https://github.com/MbinOrg/mbin/issues/486)

The below document proposes an activitypub native method of satisfying this request.


## Feed actor

A federated forum is represented by a `Group` actor as specified in [Activity Vocabulary]. The proposed `Feed` actor is a named collection of `Group` actors, administered by a `Person` actor.

As an [ActivityPub Actor](https://www.w3.org/TR/activitypub/#actor-objects) a `Feed` MUST have an `inbox` and an `outbox`. Unlike base actor objects, a `Feed` object MUST also have `following` property (this is a MAY property for the base actor object). A `Feed` actor SHOULD have a `followers` property.


## Following a Feed

Public feeds SHOULD support a standard `Follow`-`Accept` workflow. This ensures compatibility with existing implementations which support `Person` following using the same vocabulary. After receiving a valid `Follow` activity, the feed SHOULD automatically respond with an `Accept/Follow`, and add the sender to its followers collection. Correspondingly actors can unfollow a feed by sending an `Undo/Follow` activity.


## The following collection

Every feed actor MUST have a following collection. This is a list of every `Group` that the actor has collected. The following collection MUST be either an OrderedCollection or a Collection and MAY be filtered on privileges of an authenticated user or as appropriate when no authentication is given. 

Example following collection:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/security/v1"
  ],
  "id": "https://example.com/f/feedname/following",
  "items": [
    "https://example.com/c/communityname",
    "https://server2.name/c/community-two-name"
  ],
  "totalItems": 2,
  "type": "OrderedCollection"
}
```

### Announce/Add

When a `Group` is added to a Feed's `following` collection, implementations MUST represent that as an `Add` activity, where the object is the `Group` being added, and the target is the `following` collection of the feed.

Implementations SHOULD perform some automatic validation, such as checking that the request comes from a feed owner, or for domain and user blocks. Feeds MAY require additional validation, such as accepting or rejecting SFW/NSFW groups. 

In case the incoming activity is deemed valid, the feed MUST wrap it in an `Announce` activity, with the original activity as object. The wrapped activity MUST be preserved exactly as it was received, without changing or removing any properties. This ensures that forwarded activities can be verified with [Object Integrity Proofs]. Announce activities MAY get added to the group outbox. 


Example announce/add:

```json
{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Announce",
    "actor": "https://example.com/f/feedname",
    "id": "https://example.com/activities/announce/d3ade180-f641-4d6b-8ae7-ceab824f2b72",
    "object": {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Add",
        "actor": "https://example.com/f/feedname",
        "id": "https://example.com/activities/feedadd/4242",
        "object": {
            "type": "Group",
            "id": "https://example.com/c/communityname"
        },
        "target": {
            "type": "Collection",
            "id": "https://example.com/f/feedname/following"
        }
    }
}
```

After the feed successfully verifies and wraps the received activity, it sends it to the inboxes of its followers. Followers then use the outer `Announce` activity to verify that the content was really approved by the feed. After this step the `Announce` can be discarded and only the inner activity used to update the feed following collection.


### Announce/Remove

When a `Group` is removed from a Feed's `following` collection, implementations MUST represent that as an `Remove` activity, where the object is the `Group` being added, and the target is the `following` collection of the feed.

Implementations SHOULD perform some automatic validation, such as checking that the request comes from a feed owner, or for domain and user blocks. Feeds MAY require additional validation, such as accepting or rejecting SFW/NSFW groups. 

In case the incoming activity is deemed valid, the feed MUST wrap it in an `Announce` activity, with the original activity as object. The wrapped activity MUST be preserved exactly as it was received, without changing or removing any properties. This ensures that forwarded activities can be verified with [Object Integrity Proofs]. Announce activities MAY get added to the group outbox. 


Example announce/remove:

```json
{
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Announce",
    "actor": "https://example.com/f/feedname",
    "id": "https://example.com/activities/announce/d3ade180-f641-4d6b-8ae7-ceab824f2b72",
    "object": {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Remove",
        "actor": "https://example.com/f/feedname",
        "id": "https://example.com/activities/feedremove/4242",
        "object": {
            "type": "Group",
            "id": "https://example.com/c/communityname"
        },
        "target": {
            "type": "Collection",
            "id": "https://example.com/f/feedname/following"
        }
    }
}
```

After the feed successfully verifies and wraps the received activity, it sends it to the inboxes of its followers. Followers then use the outer `Announce` activity to verify that the content was really approved by the feed. After this step the `Announce` can be discarded and only the inner activity used to update the feed following collection.


## The followers collection

Every feed SHOULD have a followers collection. This is a list of everyone who has sent a Follow activity for the actor, added as a side effect. This is where one would find a list of all the actors that are following the actor. The followers collection MUST be either an OrderedCollection or a Collection and MAY be filtered on privileges of an authenticated user or as appropriate when no authentication is given. 

Implementations MAY choose to show only the number of collection items, rather than all the actors in the collection. 

Example followers collection:

```json
{
    "@context": [
        "https://www.w3.org/ns/activitystreams",
        "https://w3id.org/security/v1"
    ],
    "id": "https://example.com/f/feedname/followers",
    "items": [],
    "totalItems": 2,
    "type": "Collection"
}
```


## Feed ownership

Feeds MUST provide ownership information. This SHOULD be provided as either the `attributedTo` or `moderators` property of the feed actor.

Implementations MAY provide this information as a single actor, an OrderedCollection of actors, or a Collection of actors.

Example moderators ordered collection:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/security/v1"
  ],
  "id": "https://example.com/f/feedname/moderators",
  "orderedItems": [
    "https://example.com/u/username"
  ],
  "totalItems": 1,
  "type": "OrderedCollection"
}
```


# Implementations

This document is written based on the Feeds feature in PieFed. 


## References

- [RFC-2119] S. Bradner, [Key words for use in RFCs to Indicate Requirement Levels](https://tools.ietf.org/html/rfc2119.html)
- [Activity Vocabulary], James M Snell, Evan Prodromou, [Activity Vocabulary](https://www.w3.org/TR/activitystreams-vocabulary/)
- [Object Integrity Proofs] silverpill, [FEP-8b32: Object Integrity Proofs](https://codeberg.org/fediverse/fep/src/branch/main/fep/8b32/fep-8b32.md)


## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
