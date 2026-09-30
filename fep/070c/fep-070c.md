---
slug: "070c"
authors: [Daniel Supernault <@dansup@mastodon.social>]
status: DRAFT
discussionsTo: https://socialhub.activitypub.rocks/t/fep-070c/8914
dateReceived: 2026-09-30
trackingIssue: https://codeberg.org/fediverse/fep/issues/934
---

# FEP-070c: Block synchronization across servers

## Summary

In ActivityPub, a user-level block is created on the blocker's server and, in
some implementations, communicated to the blocked actor's server with a `Block`
activity and later revoked with an `Undo Block` activity. Many implementations
do not federate blocks at all, and those that do assume every delivery is
received and processed correctly.

Dropped deliveries, software bugs, server crashes and database rollbacks can
leave the two servers with different views of which blocks are in effect. This
causes two kinds of failure:

- A **stale block**: the blocked actor's server still applies a block that has
  been revoked, so the formerly blocked actor silently loses access to content
  and interactions.
- A **missing block**: the blocked actor's server never learned about a block,
  so it keeps presenting the blocker's content to the blocked actor and keeps
  accepting and forwarding the blocked actor's interactions with it. This is
  especially damaging where content is delivered through `sharedInbox` and the
  receiving server decides what its local users can see.

This proposal describes an optional mechanism for detecting and repairing such
discrepancies, modeled on [FEP-8fcf]. It discloses a block only to the server
that hosts the blocked actor, and only after that server has authenticated
itself with a signed request.

## Requirements

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this specification are to
be interpreted as described in [RFC-2119].

Implementations and deployments MUST NOT implement the mechanisms described in
this proposal unless:

- all actors managed by an instance share the same URI scheme and authority for
  their `id`, `inbox` and `sharedInbox` URIs;
- every actor using that scheme and authority is managed by the same instance;
- the instance is able to verify HTTP signatures on incoming `GET` requests
  ("authorized fetch") and to sign its own outgoing requests, using
  [HTTP-Signatures] or [RFC-9421].

These requirements are the same as those of [FEP-8fcf], plus signed fetch. They
ensure that the set of blocks relevant to a peer can be derived from actor
`id`s alone, and that the requesting peer can be identified reliably.

Implementing this proposal is optional and does not affect compatibility with
implementations that do not support it.

## Terminology

- **Authority**: the combination of URI scheme, host and port of a URI, as
  defined in [RFC-3986]. Two URIs share an authority when all three are equal.
- **Block pair**: an ordered pair `(blocker, blocked)` of actor `id`s, meaning
  the actor `blocker` has blocked the actor `blocked`.
- **Disclosure set**: the set of block pairs, made by actors on an instance,
  that the instance has decided to reveal to the servers hosting the blocked
  actors. How an instance populates its disclosure set is a local policy
  decision; see [Privacy considerations](#privacy-considerations).
- **Relevant block set**: for a given sending instance and receiving instance,
  the subset of the sending instance's disclosure set in which the `blocker`
  shares the sending instance's authority and the `blocked` actor shares the
  receiving instance's authority.
- **Application actor**: the actor representing the instance itself, as
  described in [FEP-2677]. Often called the instance actor.

## Disclosure set consistency

An instance implementing this proposal MUST use the same disclosure set when
computing digests and when serving the synchronization endpoint. A block pair
that is not part of the disclosure set MUST NOT contribute to any digest and
MUST NOT be returned by the synchronization endpoint.

This prevents a peer from testing guesses about undisclosed blocks against the
digest.

## Block set digest

The block set digest summarizes a relevant block set so that two instances can
check cheaply whether they agree.

For each block pair, compute the SHA-256 hash of the UTF-8 encoding of the
blocker `id`, a single space character (U+0020), and the blocked `id`. The
digest is the XOR of all of these hashes, encoded as 64 lowercase hexadecimal
characters:

```
pairHash(blocker, blocked) = SHA256(blocker + " " + blocked)
digest = pairHash(pair1) XOR pairHash(pair2) XOR ... XOR pairHash(pairN)
```

Actor `id`s are used exactly as they appear in the actor documents, with no
normalization. The digest of an empty set is 64 zero characters.

### Example

Suppose `https://a.example` has the following disclosure set:

- `https://a.example/users/alice` blocks `https://b.example/users/bob`
- `https://a.example/users/carol` blocks `https://b.example/users/bob`
- `https://a.example/users/alice` blocks `https://c.example/users/dave`

The relevant block set for `https://b.example` contains the first two pairs:

```
SHA256("https://a.example/users/alice https://b.example/users/bob")
  = 5a0f09e214e8951a292c01ce220e3b768e738ab28917c73a3ced82e8fd8c77c2

SHA256("https://a.example/users/carol https://b.example/users/bob")
  = 086808bc95e0f2fa3db8e55ae0c5d80e70e87aecc74a7d6beab2ba2319280a17

digest
  = 5267015e810867e01494e494c2cbe378fe9bf05e4e5dba51d65f38cbe4a47dd5
```

## The `Block-Synchronization` HTTP header

The `Block-Synchronization` header lets the sending instance tell the receiving
instance what its relevant block set currently looks like, and where to fetch
it.

The header value is a list of parameters and values, formatted according to
the `signature` syntax defined in [HTTP-Signatures], Section 4.1, as in
[FEP-8fcf].

```
Block-Synchronization: url="https://a.example/federation/block-sync", digest="5267015e810867e01494e494c2cbe378fe9bf05e4e5dba51d65f38cbe4a47dd5"
```

### Parameters

- `url`: the URL of the synchronization endpoint. It MUST share the sending
  instance's authority.
- `digest`: the block set digest of the relevant block set for the receiving
  instance.

A separate header is used rather than `Collection-Synchronization` because
[FEP-8fcf] requires that header's `collectionId` to be a followers collection.

## The synchronization endpoint

The synchronization endpoint returns the relevant block set for the instance
that makes the request. The same URL serves every peer; the response depends
on who the requester has proven to be.

### Authentication

Requests to the synchronization endpoint MUST be signed using [HTTP-Signatures]
or [RFC-9421]. The serving instance MUST:

1. verify the signature;
2. resolve the signing key and confirm that its owner is an actor whose `id`
   shares the authority of the key's `id`;
3. take the authority of the owner actor's `id` as the requesting authority.

Requests SHOULD be signed by the requesting instance's application actor. The
serving instance MUST NOT accept a requesting authority from any other source,
such as a query parameter or request header.

If the request is unsigned or the signature cannot be verified, the serving
instance MUST respond with `401 Unauthorized`. If the serving instance does not
disclose blocks to the requesting authority, it MUST respond with
`403 Forbidden` rather than an empty collection, because an empty collection
would instruct the requester to remove all of its recorded blocks.

### Response

A successful response is an `OrderedCollection` whose items are objects of
type `Block`, each with an `actor` and an `object` property containing the
blocker and blocked actor `id`s. An `id` for each `Block` MAY be included but
is not used by this proposal.

The collection MUST contain exactly the relevant block set for the requesting
authority: every block pair in the serving instance's disclosure set whose
`actor` shares the serving instance's authority and whose `object` shares the
requesting authority, and nothing else.

The collection MUST include a `blockSynchronizationDigest` property whose value
is the block set digest of the collection's items, computed from the same state
the items are read from. This lets the receiving instance check that the items
it fetched form a consistent set, including when there was no header to compare
against (see [Applying the result](#applying-the-result)). When the collection
is paginated, the property is only required on the top-level collection object.

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
      "blockSynchronizationDigest": "https://w3id.org/fep/070c#blockSynchronizationDigest"
    }
  ],
  "type": "OrderedCollection",
  "totalItems": 2,
  "blockSynchronizationDigest": "5267015e810867e01494e494c2cbe378fe9bf05e4e5dba51d65f38cbe4a47dd5",
  "orderedItems": [
    {
      "type": "Block",
      "actor": "https://a.example/users/alice",
      "object": "https://b.example/users/bob"
    },
    {
      "type": "Block",
      "actor": "https://a.example/users/carol",
      "object": "https://b.example/users/bob"
    }
  ]
}
```

### Pagination

A relevant block set only covers the actors of one peer, so it is usually
small. Serving instances SHOULD return it as a single document, and SHOULD only
paginate when the set is too large to serve at once.

When a collection is paginated, serving instances SHOULD order items by `actor`
and then `object`, and SHOULD link pages with a cursor derived from the last
item of the previous page rather than a numeric offset. With offset-based pages,
removing an item from an earlier page shifts later items so that one of them
can be skipped entirely. With cursor-based pages, a block pair that exists for
the whole duration of a fetch is always returned; only pairs added or removed
during the fetch may or may not appear.

### Caching

Responses MUST NOT be stored by shared caches. Serving instances SHOULD send
`Cache-Control: private, no-store`. They SHOULD send an `ETag` for the
requesting authority's current relevant block set and honor `If-None-Match`,
so that periodic reconciliation is cheap when nothing has changed.

### Discovery

Receiving instances learn the endpoint URL from the `Block-Synchronization`
header and MAY remember it per peer.

An instance MAY additionally advertise the endpoint on its application actor
using the `blockSynchronization` property, so that peers can reconcile even
when they have not received a delivery carrying the header:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
      "blockSynchronization": {
        "@id": "https://w3id.org/fep/070c#blockSynchronization",
        "@type": "@id"
      }
    }
  ],
  "id": "https://a.example/actor",
  "type": "Application",
  "blockSynchronization": "https://a.example/federation/block-sync"
}
```

The advertised URL MUST share the application actor's authority.

## Synchronization procedure

### On the sending end

When delivering an activity to an `inbox` or `sharedInbox`, an instance MAY
attach a `Block-Synchronization` header computed for the instance that owns
that inbox, determined by the inbox URI's authority. Because the digest
describes the whole instance pair, the header MAY be attached to a delivery
signed by any local actor, including the application actor.

The header MUST be covered by the request's HTTP signature: listed in the
`headers` parameter under [HTTP-Signatures], or included as a covered component
under [RFC-9421].

An instance MUST NOT attach the header to deliveries to an instance it does not
disclose blocks to.

### On the receiving end

Upon receiving a delivery with a `Block-Synchronization` header, the receiving
instance MUST check that:

- the header is covered by a valid HTTP signature;
- the `url` parameter shares the authority of the signing actor's `id`.

If either check fails, the receiving instance MUST ignore the header.

The receiving instance SHOULD then compute the digest of the block pairs it has
recorded in which the blocker shares the sender's authority and the blocked
actor is local. If this digest differs from the `digest` parameter, it SHOULD
fetch the `url`, signing the request as described in
[Authentication](#authentication).

Receiving instances SHOULD rate limit fetches per peer and SHOULD collapse
repeated mismatches from the same peer into a single pending fetch.

### Periodic reconciliation

A receiving instance MAY periodically fetch the synchronization endpoint of
peers it federates with, using a URL learned from the header or from the
peer's application actor, even without a digest mismatch. This covers peers
that rarely deliver to the receiving instance, which is common after a block
has been made. A daily interval per active peer, combined with `If-None-Match`,
is RECOMMENDED as a starting point.

### Applying the result

Adding a block that should not exist is an inconvenience. Removing a block that
should exist exposes a user to the actor they blocked. The rules below are
therefore asymmetric.

After fetching the collection, the receiving instance MUST discard any item
whose `actor` does not share the serving instance's authority or whose `object`
does not share its own authority, and MUST compute the block set digest of the
items it fetched, across all pages.

For each block pair in the collection but not recorded locally, the receiving
instance SHOULD apply the block as if it had received the corresponding `Block`
activity. It MAY do so even when the fetch was incomplete or inconsistent.

For each block pair recorded locally but not in the collection, the receiving
instance SHOULD remove the block as if it had received the corresponding
`Undo Block` activity, but only if all of the following hold:

- every page of the collection was fetched;
- no item was discarded or failed to parse;
- the computed digest equals the collection's `blockSynchronizationDigest`.

If the digests differ, the set changed while it was being fetched or the
response is inconsistent. The receiving instance MUST NOT remove any block
based on that fetch. It MAY retry the fetch once, and otherwise waits for the
next mismatch or reconciliation.

Receiving instances SHOULD NOT remove a block pair they recorded within the
last few minutes (10 minutes is RECOMMENDED), even when all of the conditions
above hold. This covers a `Block` activity that arrived after the serving
instance generated its response.

The digest from a `Block-Synchronization` header only decides whether to fetch.
Removals are always checked against the digest in the fetched collection, so
header-triggered synchronization and periodic reconciliation follow the same
rules.

Blocks are unilateral, so the receiving instance does not deliver anything in
response.

If the fetch fails or returns a non-2xx status, the receiving instance MUST NOT
change its recorded blocks for that peer.

## Relationship to `Block` activities

This proposal is independent of how blocks are otherwise communicated. An
instance MAY implement it without ever sending `Block` activities, relying on
synchronization alone.

Instances that also want blocks to take effect on servers that do not
implement this proposal SHOULD additionally send `Block` and `Undo Block`
activities. When both are used, the set of blocks federated as activities
SHOULD match the disclosure set, and synchronization serves as a repair
mechanism for lost or misapplied deliveries.

## Relationship to FEP-8fcf

Blocking an actor typically also removes that actor from the blocker's
followers collection. That side of the relationship is already reconciled by
[FEP-8fcf], so the two proposals complement each other.

## Privacy considerations

Blocks are sensitive. This proposal is designed so that implementing it
reveals no more than federating `Block` activities to the blocked actor's
server would:

- A block pair is disclosed only to the instance hosting the blocked actor, and
  only after that instance has authenticated with a signed request. Because the
  response is scoped by the verified signer's authority, no instance can
  retrieve blocks that involve another instance's actors.
- Disclosure set consistency ensures the digest cannot be used to confirm
  guesses about undisclosed blocks.
- The header is only sent to the instance it concerns, over the same
  connection as the delivery.

However, disclosing a block to the blocked actor's server means that server's
operators can see it, and a hostile operator could reveal it to the blocked
actor.

Implementations SHOULD therefore:

- exclude peers that are suspended or limited, or that the instance does not
  otherwise federate with;
- consider offering users a local-only block that is kept out of the disclosure
  set;
- avoid logging header values and endpoint responses.

Receiving implementations SHOULD NOT notify the blocked actor as a result of
synchronization. This proposal does not change how implementations present
blocks to users.

## Security considerations

The XOR of SHA-256 hashes is an order-independent set summary, not a
collision-resistant set hash: a party that controls the set's contents could
construct a different set with the same digest. This proposal uses the digest
in two ways, neither of which depends on collision resistance:

- The header digest only decides whether to fetch.
- The collection digest detects a set that changed during a fetch or a response
  that is otherwise inconsistent. It protects against accidents, not against a
  malicious serving instance, which is authoritative for its own actors' blocks
  and can list whatever it wants.

Receiving instances never infer block state from a digest alone.

The `url` authority check prevents a sender from making the receiving instance
issue signed requests to third-party servers.

Each digest mismatch can trigger an outbound signed fetch, so rate limiting on
both ends is important to prevent amplification.

## Implementation notes

The digest can be maintained incrementally. When a block pair is added to or
removed from the disclosure set, the instance XORs its `pairHash` into the
cached digest for the blocked actor's authority. Storing the digest as 32 bytes
per peer authority, for example in a key-value store, avoids recomputing it on
every delivery.

When an actor is deleted, the instance hosting the blocker SHOULD remove block
pairs involving it from its disclosure set when it processes the `Delete`.
Receiving instances MAY keep block pairs they cannot currently apply, such as
pairs whose blocker has not been fetched yet, so that their digest stays in
agreement with the serving instance.

Because the serving instance usually already maintains the digest for the
header, it can reuse it both for the collection's
`blockSynchronizationDigest` and as the `ETag` of the response.

Receiving instances that want an immediate second attempt after a digest
mismatch during a paginated fetch should wait briefly before retrying, so that
a burst of changes on the serving instance has time to settle.

## Implementations

- Pixelfed
- Loops (planned)

## References

- [ActivityPub] C. Webber, J. Tallon, [ActivityPub](https://www.w3.org/TR/activitypub/), 2018
- [ActivityStreams] J. Snell, E. Prodromou, [Activity Vocabulary](https://www.w3.org/TR/activitystreams-vocabulary/), 2017
- [RFC-2119] S. Bradner, [Key words for use in RFCs to Indicate Requirement Levels](https://tools.ietf.org/html/rfc2119.html), 1997
- [RFC-3986] T. Berners-Lee, R. Fielding, L. Masinter, [Uniform Resource Identifier (URI): Generic Syntax](https://tools.ietf.org/html/rfc3986), 2005
- [HTTP-Signatures] M. Cavage, M. Sporny, [Signing HTTP Messages](https://tools.ietf.org/html/draft-cavage-http-signatures-12), 2019
- [RFC-9421] A. Backman, J. Richer, M. Sporny, [HTTP Message Signatures](https://www.rfc-editor.org/rfc/rfc9421), 2024
- [FEP-8fcf] Claire, [Followers collection synchronization across servers](https://codeberg.org/fediverse/fep/src/branch/main/fep/8fcf/fep-8fcf.md), 2020
- [FEP-2677] Ryan Barrett, [Identifying the Application Actor](https://codeberg.org/fediverse/fep/src/branch/main/fep/2677/fep-2677.md), 2024

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
