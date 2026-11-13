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

In this case the object already has an identifier and is publicly retrievable by `GET`. What the hosting server has not done is record or deliver a `Create` for it. A referenced `Create` records that publication and makes it eligible for delivery under the ordinary addressing rules; it does not make the object retrievable for the first time.

For those servers the client has nothing new to submit. It wants to name an object the server already hosts and ask for it to be published:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Create",
  "actor": "https://example.org/actors/alice",
  "object": "https://example.org/articles/123"
}
```

The syntax is already defined by ActivityStreams — this is the shape of the Minimal Activity example, with both properties given as URIs rather than inlined documents. What is missing is what an outbox should do with it.

**There are two separable proposals here, and it is worth saying which is which.**

1. **Referencing an existing object.** When `Create.object` is a URI the server already hosts, what happens to the object's identifier, its existing attribution, and its addressing. This is specific to a submission that names something rather than carrying it.

2. **Responding to a retry.** When a server recognises a submission as one it has already recorded and creates no new activity, what status and `Location` it returns. This is not specific to `Create` at all: the same question arises for any submission a server deduplicates, `Follow` and `Like` among them.

The second is the one this proposal exists for, and it survives a change of activity type — if the publication were expressed as something other than a `Create`, the retry contract would read the same. The first is what makes a referenced submission well defined in the first place, so both are specified here.

Note what decides the status code. The object already existing does not make the first submission a retry: that request records a new activity and gets `201`. A later submission recognised as a retry gets `200` because the *activity* already exists and this request recorded nothing, not because the object does.

The rules here are written for a URI-referenced `Create` or `Delete`, which Activity Streams lists under both Content Management and Relationship Management, so the target may be an article or a relationship without changing anything. The same response pattern can be used for other client-to-server activities — `Follow`, `Like`, `Block` and `Undo` among them — wherever a server recognises a retry and records nothing new. How to recognise a retry for those is not defined here.

The proposal does not specify how many such activities an object may have, or who may publish one. Nor does it cover actor types. [Section 6.2.1][AP-Bare-Object] obliges an outbox to accept any non-`Activity` `Object` submitted directly to it, so a client-to-server implementation already has to answer for a `Person`, a `Group` or a `Collection` as well as an `Article`. Section 6.2.1 says nothing about references, but a URI can name one of those just as easily, and that case does need an answer eventually. This proposal is written from an implementation of the [object types][AS2-Object-Types] only — a list that does not include `Collection`, which is a core type — and the author has not examined the [actor types][AS2-Actor-Types] closely enough to say what a referenced `Create` should mean for one, and would rather implement and measure that than guess at it here.

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

[ActivityPub Section 6][AP-C2S] requires `201 Created` and does not separately address a recognised retry that records no new activity. [HTTP Semantics][HTTP-Created] describes `201` in terms of a request creating a new resource. This proposal recommends `200 OK` for the no-new-activity case, explicitly documenting the exception to Section 6 so clients can distinguish a new activity from a replay.

## Requirements

### Referenced Create

A server MAY accept a `Create` activity whose `object` is a string URI identifying an existing `Object` the server hosts and publishes as content: an `Object` that is neither an [actor type][AS2-Actor-Types], nor a `Collection` or `CollectionPage`, nor a `Link`. A server MAY apply the same rules to other types; this proposal does not say what they should mean there.

[Section 6.2.1][AP-Bare-Object] requires an outbox to accept a valid non-`Activity` `Object` submitted directly to it. `Link` is [disjoint from `Object`][AS2-Base-Types], so that requirement does not reach a standalone `Link`, and nothing here defines the publication of one either. A [`Mention`][AS2-Mention] is a `Link`: the resource its `href` points to is distinct from the link itself, and this proposal does not define what it means to publish the `Mention` itself. AS2 does permit a `Link` as the value of `as:object`, so such a submission is not malformed by type alone; it is simply outside what is specified here. Nor does naming something by URI make the reference a `Link` — the URI string is the reference form this proposal defines, and what matters is the object it resolves to.

When a server accepts a URI-referenced `Create`:

1. **The request is a request to publish, not to edit.** The server MUST NOT alter the referenced object's content or addressing to satisfy it, and MUST NOT replace or extend its existing attribution. If the object has no existing attribution, the server SHOULD initialise `attributedTo` from `Create.actor`, consistent with [ActivityPub Section 6.2][AP-Create].

2. **Identifiers.** The server MUST NOT assign a new identifier to the referenced object. The requirement to attach an identifier applies to objects the server creates, not to objects it is asked to name. The new `Create` activity is itself a new object and receives an identifier as usual.

3. **Two permissions, checked separately.** The authenticated request must be permitted to submit to that outbox, and the outbox's actor must be permitted to publish that object. A server MUST refuse when either is absent, and MUST NOT treat the first as implying the second. The authorisation mechanism is implementation-defined; attribution alone does not establish publication authority under this proposal.

4. **Addressing.** The server MUST take the activity's addressing from the addressing the referenced object already carries. Recipients are then computed from that addressing by the ordinary delivery rules; this proposal does not change them. Some objects carry no addressing at all, and a server MUST NOT invent one. It MUST either refuse the submission, or record the activity without adding addressing. Recording it is still a creation, so the response rules below apply unchanged; an activity with no recipients is simply not delivered.

   The absence of addressing on the referenced object does not by itself grant or restrict access to that object. Conversely, an object being publicly retrievable does not supply recipients for the new activity: a server MUST NOT choose an audience the object never stated. [ActivityPub's rules for public addressing][AP-Public] are unchanged by this proposal, and who may read the recorded activity in the [outbox collection][AP-Outbox] is not decided here.

5. **Addressing in the request is rejected, not ignored.** If the request carries `to`, `cc`, `bto`, `bcc` or `audience`, the server MUST reject the submission. Ignoring those properties and publishing to the object's existing, possibly wider audience would let a client believe it had published narrowly.

6. **Unresolvable references.** If the URI does not resolve to an object the server hosts, the server MUST refuse the submission. It MUST NOT create an object to satisfy the reference.

### Replay of a referenced Create or Delete

The following rules apply to both URI-referenced `Create` and [`Delete`][AP-Delete]. For `Delete`, they are all this proposal defines: whether to accept a referenced `Delete` at all, what authority it requires, how it is addressed, and what becomes of the object are left to [ActivityPub][AP-Delete] and to the server. The rules above are for `Create` only.

7. **Repeated submissions are idempotent.** When an authorised submission repeats the same publication or deletion transition for the same actor and object, the server SHOULD return the previously recorded activity without recording or delivering another. A server MUST NOT answer one actor's submission with an activity recorded for another. If more than one transition of the same type is possible for that actor and object, the reference alone does not distinguish a retry from a new transition.

8. **Responding to a retry.** Where a new activity is recorded the response is `201 Created` with its identifier in the `Location` header. For a recognised retry under rule 7, the server SHOULD answer `200 OK` with the existing activity's identifier in `Location`. This exception to [ActivityPub Section 6][AP-C2S] applies only to that successful replay, not to a refused submission.

[FEP-4f05][FEP-4f05] describes restoring a soft-deleted object using `Undo(Delete)`, not a new Create. A deletion after restoration can be a new transition and receive `201 Created`; a delayed retry of the earlier deletion must not be mistaken for that new transition. Servers that support both need a way to distinguish them, such as a request identifier or a lifecycle precondition.

## Why `Create` and not `Announce`

Announcing an object's existence and recording its first federated publication are different purposes, and neither is always the better one. `Announce` serves the first. This proposal serves the second: the `Create` records that an actor published the object, without replacing the attribution the object already carries. A server can use that record to track publication history, while later `Update` and `Delete` activities still target the object itself.

[FEP-aef6][FEP-aef6] reaches for a third type in a neighbouring shape: a `Notify` whose `object` already exists, sent in answer to a `Request`, so that an object can be retrieved without an always-on HTTP server. Its subject is retrieval rather than publication, so it is cited here as adjacent work rather than as an alternative — though what this proposal says about an object keeping the identifier it already has would read much the same under either activity.

Nothing about this requires the object to be new. An object may be written long beforehand and the `Create` sent later; that is the ordinary case for a content store that predates its federation. The object keeps its existing `published` timestamp, if any, while the activity carries the time of the federated publication.

The same actor may legitimately update the same object many times. Actor and object identifiers alone cannot identify an `Update` retry; how to identify such retries is outside this proposal.

## What this does not specify

How many `Create` activities one object may have, and who may publish them, are left to the implementation. A server may record exactly one and treat the actor of that activity as the object's publishing authority; a server may instead accept a `Create` from each of several actors and treat the object as jointly published. Both remain compatible with the requirements above, which concern a single submission in isolation.

Deletion and restoration semantics beyond the replay rule, re-use of an identifier after deletion, and the relationship between a referenced `Create` and later `Update` activities are out of scope.

## Implementation notes

Axismundi originally supported multiple actors per user so people could switch profiles without signing out. It later drew on account discovery in the [JMAP Session object][JMAP-Session] to describe which actor accounts are available to the authenticated user.

This separation also fits the [ActivityPub C2S object submission model][AP-Bare-Object], which is not limited to content types: `Person` and `Group` are also non-Activity object types. Submitting an actor object is distinct from provisioning an operable account or granting access to its outbox. Neither this proposal nor ActivityPub requires JMAP Session discovery or specifies account provisioning for such submissions.

Axismundi distinguishes the authenticated WordPress user from the selected publishing actor. Its account access policy determines whether the user may act as that actor. For a referenced WordPress post it also checks the user's `edit_post` capability for that post and enforces the post's publication and attribution policy. This uses WordPress's existing access controls, including delegated editing, rather than treating the post's author field or ActivityStreams attribution as an access-control list.

When a post has no stored attribution, Axismundi uses the actor of its first recorded `Create` to initialise attribution in WordPress post metadata after the activity commits. If the post already has a stored publishing actor, its URI must exactly match `Create.actor`; membership in the co-attribution list is not sufficient. Co-attribution and the WordPress post author are preserved.

Axismundi records at most one `Create` per object and uses its actor as the publication authority. This makes an otherwise valid repeat submission from that actor a replay, while a submission by a different actor is refused rather than given the existing activity. These are implementation choices; the proposal does not require Axismundi's account model, storage layout, or one-Create limit.

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
- silverpill, [FEP-aef6: Asynchronous Object Retrieval][FEP-aef6]

[ActivityPub]: https://www.w3.org/TR/activitypub/
[AP-Identifiers]: https://www.w3.org/TR/activitypub/#obj-id
[AP-C2S]: https://www.w3.org/TR/activitypub/#client-to-server-interactions
[HTTP-Created]: https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.2
[AP-Create]: https://www.w3.org/TR/activitypub/#create-activity-outbox
[AP-Bare-Object]: https://www.w3.org/TR/activitypub/#object-without-create
[AS2-Object-Types]: https://www.w3.org/TR/activitystreams-vocabulary/#object-types
[AS2-Mention]: https://www.w3.org/TR/activitystreams-vocabulary/#dfn-mention
[AS2-Base-Types]: https://www.w3.org/TR/activitystreams-vocabulary/#base-types
[AP-Outbox]: https://www.w3.org/TR/activitypub/#outbox
[AP-Public]: https://www.w3.org/TR/activitypub/#public-addressing
[AS2-Actor-Types]: https://www.w3.org/TR/activitystreams-vocabulary/#actor-types
[JMAP-Session]: https://www.rfc-editor.org/rfc/rfc8620.html#section-2
[AP-Delete]: https://www.w3.org/TR/activitypub/#delete-activity-outbox
[AS2]: https://www.w3.org/TR/activitystreams-core/
[AS2-Minimal]: https://www.w3.org/TR/activitystreams-core/#example-1
[FEP-4f05]: https://codeberg.org/fediverse/fep/src/branch/main/fep/4f05/fep-4f05.md
[FEP-aef6]: https://codeberg.org/silverpill/feps/src/branch/main/aef6/fep-aef6.md
[issue438]: https://github.com/w3c/activitypub/issues/438
[MediaUpload]: https://www.w3.org/wiki/SocialCG/ActivityPub/MediaUpload

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
