---
slug: "c3ab"
authors:
  - "Jiwoon Kim <kimjiwoon75@gmail.com>"
status: DRAFT
discussionsTo: https://socialhub.activitypub.rocks/t/fep-c3ab-referencing-existing-objects-in-client-to-server-create/8983
dateReceived: 2026-11-12
trackingIssue: https://codeberg.org/fediverse/fep/issues/985
---
# FEP-c3ab: Referencing Existing Objects in ActivityPub Client-to-Server Create

## Summary

Client-to-server interactions are described for objects that are born with their activity: a client posts a `Note`, the server wraps it in a `Create`, and both are given identifiers.

Where federation is added to a content store that already exists, the order is reversed, and that is the normal case for a content management system. The store assigns an identifier, an author and an audience when the content is written; a module or plugin adds federation later; and so an object can sit there for years before any actor decides to publish it. Publishing older content, publishing selectively, and publishing under one of several actors are then ordinary requests rather than edge cases. The same is true of any server that serves the same content both as a website and to the fediverse, since the website copy exists whether or not an activity was ever recorded for it.

For those servers the client has nothing new to submit. It wants to name an object the server already hosts and ask for it to be published:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Create",
  "actor": "https://example.org/actors/alice",
  "object": "https://example.org/articles/123"
}
```

The syntax is already defined by ActivityStreams — this is the shape of the Minimal Activity example, with both properties given as URIs rather than inlined documents. This proposal specifies how an outbox handles the `object` reference: identifiers, addressing, refusal, and repeated submissions.

A reference names an existing object rather than asking the server to create another one. Where the same actor's submission names the same publication transition, a retry can return the activity already recorded for that transition.

The proposal does not specify how many such activities an object may have, or who may publish one.

## The situation

Section 6.2.1 of ActivityPub describes submitting an object that does not exist yet, and every rule in it is written for an object the server is about to create:

> The server MUST accept a valid ActivityStreams object that isn't a subtype of Activity in the POST request to the outbox.

> The server then MUST attach this object as the object of a Create Activity.

> For non-transient objects, the server MUST attach an id to both the wrapping Create and its wrapped Object.

It does not describe naming an object the server already hosts, and it does not say what a server should do with an identifier the object already has. The same gap is recorded in `w3c/activitypub#438`, which asks what a server should do with an inner object's `id`.

An adjacent case is the `MediaUpload` proposal, where an object is created through a separate endpoint and the server may afterwards wrap it in a `Create`. It shows that an object preceding its activity is not a new idea, though it addresses a different endpoint and leaves the wrapping optional.

## Why this needs writing down

No existing proposal covers it. Of the client-to-server proposals, FEP-6606 addresses collection addressing, FEP-d8c2 an OAuth profile, FEP-ae97 client-side signing and FEP-65ca client configuration; none concerns what an outbox does with a submitted activity's `object`. The nearest by name is FEP-cd47, which collects addressing and deduplication use cases, but its subject is recognising the same actor or content across locations rather than recognising a repeated submission.

The gap has been visible for some time without closing. `MediaUpload` reached for the same shape in 2017 and has not been edited since; `w3c/activitypub#438` has been open since 2024.

The proposal uses the existing ActivityStreams roles of [actor and object in a Minimal Activity][AS2-Minimal]. It preserves the object's [global identifier][AP-Identifiers] and follows the distinction between attribution and addressing in [ActivityPub Section 6.2][AP-Create]. If a server uses a Create record to register publication of an object URI, returning that record on a retry preserves the registration rather than creating a second one. The global identifier requirement does not itself mandate one Create per object.

The explicit departure from an ActivityPub MUST is the response to a recognised retry: [Section 6][AP-C2S] requires `201 Created`, but this proposal recommends `200 OK` when no new activity is recorded. Documenting that exception gives servers and clients an agreed way to distinguish a new activity from a replay.

## Requirements

A server MAY accept a `Create` activity whose `object` is a string URI. When it does:

1. **The request is a request to publish, not to edit.** The server MUST NOT alter the referenced object's content, attribution or addressing in order to satisfy it. Section 6.2 recommends copying a `Create`'s `actor` onto the object's `attributedTo`; on this path that recommendation is satisfied only where the object carries no attribution yet. A server MUST NOT use it to replace or extend attribution the object already carries.

2. **Identifiers.** The server MUST NOT assign a new identifier to the referenced object. The requirement to attach an identifier applies to objects the server creates, not to objects it is asked to name. The new `Create` activity is itself a new object and receives an identifier as usual.

3. **Two permissions, checked separately.** The authenticated request must be permitted to submit to that outbox, and the outbox's actor must be permitted to publish that object. A server MUST refuse when either is absent, and MUST NOT treat the first as implying the second.

4. **Addressing.** The server MUST take the activity's addressing from the addressing the referenced object already carries. Recipients are then computed from that addressing by the ordinary delivery rules; this proposal does not change them.

5. **Addressing in the request is rejected, not ignored.** If the request carries `to`, `cc`, `bto`, `bcc` or `audience`, the server MUST reject the submission. Ignoring those properties and publishing to the object's existing, possibly wider audience would let a client believe it had published narrowly.

6. **Unresolvable references.** If the URI does not resolve to an object the server hosts, the server MUST refuse the submission. It MUST NOT create an object to satisfy the reference.

7. **Repeated submissions are idempotent.** When an authorised submission repeats the same publication transition for the same actor and object, the server SHOULD return the previously recorded activity without recording or delivering another. A server MUST NOT answer one actor's submission with an activity recorded for another. A reference identifies the object; if the server permits more than one publication by the same actor, the reference alone does not distinguish a retry from a new publication.

8. **Responding to a retry.** Where a new activity is recorded the response is `201 Created` with its identifier in the `Location` header, as for any other submission. Where none is recorded, `201 Created` would assert a creation that did not happen; a server SHOULD answer `200 OK` instead, with the existing activity's identifier in `Location`. Section 6 requires `201 Created` for submissions without qualification, so this is a deliberate departure, and it is confined to the case where the server has determined that it created nothing.

The same replay rule applies to a URI-referenced [Delete][AP-Delete]: a retry of the same effective deletion SHOULD return the existing Delete without recording or delivering another. [FEP-4f05][FEP-4f05] describes restoring a soft-deleted object using `Undo(Delete)`, not a new Create. A deletion after restoration can be a new transition and receive `201 Created`; a delayed retry of the earlier deletion must not be mistaken for that new transition. Servers that support both need a way to distinguish them, such as a request identifier or a lifecycle precondition.

## What this does not specify

How many `Create` activities one object may have, and who may publish them, are left to the implementation. A server may record exactly one and treat the actor of that activity as the object's publishing authority; a server may instead accept a `Create` from each of several actors and treat the object as jointly published. Both remain compatible with the requirements above, which concern a single submission in isolation.

Deletion and restoration semantics beyond the replay rule, re-use of an identifier after deletion, and the relationship between a referenced `Create` and later `Update` activities are out of scope.

## Implementation notes

Axismundi records at most one `Create` per object and treats its actor as that object's publishing authority. That constraint is its own, not part of this proposal, and it is what makes every repeat submission by the same actor a retry: there is never a second creation to record. A submission naming an object another actor created is refused as an authority violation rather than answered idempotently, which is the distinction requirement 7 draws.

A request that carries addressing is answered with `400`, and a URI that does not resolve to a local object with `404`, so that a client can tell a malformed submission from one naming something the server does not have.

Only `Create` is implemented. A referenced `Delete` follows the same shape but has not been built.

## Implementations

- Axismundi (WordPress), a set of plugins rather than a single package: https://github.com/Jiwoon-Kim/axismundi — implemented and covered by its test suite, not yet in a released version.

## References

- Christine Lemmer-Webber, Jessica Tallon, Erin Shepherd, Amy Guy, Evan Prodromou, [ActivityPub], 2018
- James M Snell, Evan Prodromou, [Activity Streams 2.0][AS2], 2017
- [C2S Create activity has unspecified behavior wrt assigning an ID to the inner object][issue438], 2024
- SocialCG, [ActivityPub MediaUpload][MediaUpload], 2017
- [FEP-4f05: Soft Deletion][FEP-4f05]

[ActivityPub]: https://www.w3.org/TR/activitypub/
[AP-Identifiers]: https://www.w3.org/TR/activitypub/#obj-id
[AP-C2S]: https://www.w3.org/TR/activitypub/#client-to-server-interactions
[AP-Create]: https://www.w3.org/TR/activitypub/#create-activity-outbox
[AP-Delete]: https://www.w3.org/TR/activitypub/#delete-activity-outbox
[AS2]: https://www.w3.org/TR/activitystreams-core/
[AS2-Minimal]: https://www.w3.org/TR/activitystreams-core/#example-1
[FEP-4f05]: https://codeberg.org/fediverse/fep/src/branch/main/fep/4f05/fep-4f05.md
[issue438]: https://github.com/w3c/activitypub/issues/438
[MediaUpload]: https://www.w3.org/wiki/SocialCG/ActivityPub/MediaUpload

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
