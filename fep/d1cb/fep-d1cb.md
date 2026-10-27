---
slug: "d1cb"
authors: Matthias Pfefferle <@pfefferle@notiz.blog>
status: DRAFT
dateReceived: 2026-10-27
discussionsTo: https://socialhub.activitypub.rocks/t/fep-d1cb-same-origin-actor-re-identification/8884
relatedFeps: FEP-7628
---
# FEP-d1cb: Same-origin actor re-identification

## Summary

This document describes how an [ActivityPub] actor can change its `id` to a new value on the same origin, and how receivers carry the state they have attached to the previous `id` over to the new one. The previous `id` becomes an alias that resolves to the actor. Receivers replace the `id` they have stored and keep their follows. They do not un-follow and follow again.

The `id` of an actor is its identity. This document does not give an actor two identities. It describes how the local state of a receiver, such as follows and blocks, survives a change of that identity.

## Motivation

(This section is non-normative.)

Some servers derive actor identifiers from a username or a permalink, for example `https://example.com/@alice`. When the username changes, the identifier changes with it. The old identifier stops resolving and remote servers keep the old one. To prevent this, a server may want to switch to an identifier that does not contain the username, for example `https://example.com/?author=5`, without losing the followers of existing actors.

The authority over both identifiers does not change, and the WebFinger address of the actor stays the same. This is different from a migration, where the actor moves to another server or another persona.

[FEP-7628] defines the `Move` activity for migrations. A receiver of a `Move` un-follows the old actor and follows the new one, or notifies the user. For a changed `id` on the same origin, this sends a `Follow` to an actor that has not changed. If that actor approves followers manually, the `Follow` arrives as a request and can be missed. Receivers that track the migration state of an actor also mark the actor as moved to itself. [FEP-e965] describes the actor object after a migration between personas. [FEP-1580] allows source and target to be on the same server, but only for migrating objects after an actor move, and requires [FEP-8b32] proofs. [FEP-a427] describes a domain move and its mapping rules can not express a change from `/@alice` to `?author=5`.

Implementations currently handle a changed `id` under an unchanged username in different ways. Some replace the stored `id` in place when a WebFinger lookup confirms it. Some create a second actor and leave the followers on the first one. Some stop processing activities from the actor.

## Requirements

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC-2119].

## Definitions

- **Re-identification**: the change of an actor's `id` to a new value with the same origin, as defined in [RFC-6454]. The actor's inbox and followers collection do not change.
- **Alias**: a URL that was the actor's `id` before a re-identification. An alias resolves to the actor and is listed in the actor's `alsoKnownAs` property. An alias is not an identifier of the actor. The actor has one `id`.

If the previous `id` and the new `id` do not have the same origin, this document does not apply. The restriction limits the scope of this document. A change across origins is a change of authority and is covered by migration proposals such as [FEP-7628] and [FEP-a427].

## Publisher

After a re-identification, the publisher MUST:

1. Serve the actor at the alias. A request for the alias MUST NOT return `404 Not Found` or `410 Gone`. The response MAY be the actor document or a redirect to the `id`. The document MUST have the actor's `id` as its `id`.
2. List the alias in the `alsoKnownAs` property of the actor.
3. Return the `id` from WebFinger for the unchanged address.
4. Use a new `id` for the actor's public key. The key material MAY stay the same. The previous key `id` MUST stay dereferenceable, so that signatures and proofs made before the change can still be verified.
5. Use the `id` in the `actor` and `attributedTo` properties of new activities and objects, and sign them with the key of the `id`.

The publisher SHOULD send an `Update` activity with the actor document embedded as `object` to the followers of the actor. The publisher SHOULD NOT send a `Move` activity. A re-identification is not a migration.

The publisher SHOULD serve the actor at the alias indefinitely. Receivers that did not process the `Update` notice the change only when they dereference the alias or the new key `id`.

The `url` property of the actor MAY keep pointing at the alias. Only the `id` changes.

If the alias is also used for other representations, for example an HTML profile page, the publisher SHOULD return the actor document instead of a redirect. A redirect that is cached without regard to the `Accept` header affects all clients.

Example: the actor `https://example.com/@alice` changes its `id` to `https://example.com/?author=5`. `https://example.com/@alice` is now an alias. A request for it with an ActivityPub media type returns:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "id": "https://example.com/?author=5",
  "type": "Person",
  "preferredUsername": "alice",
  "url": "https://example.com/@alice",
  "inbox": "https://example.com/?author=5&inbox",
  "followers": "https://example.com/?author=5&followers",
  "alsoKnownAs": [
    "https://example.com/@alice"
  ],
  "publicKey": {
    "id": "https://example.com/?author=5#main-key",
    "owner": "https://example.com/?author=5",
    "publicKeyPem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n"
  }
}
```

As HTTP exchange, when the publisher serves the document at the alias:

```http
GET /@alice HTTP/1.1
Host: example.com
Accept: application/activity+json

HTTP/1.1 200 OK
Content-Type: application/activity+json

{"id": "https://example.com/?author=5", "alsoKnownAs": ["https://example.com/@alice"], ...}
```

When the publisher redirects instead:

```http
GET /@alice HTTP/1.1
Host: example.com
Accept: application/activity+json

HTTP/1.1 308 Permanent Redirect
Location: https://example.com/?author=5

GET /?author=5 HTTP/1.1
Host: example.com
Accept: application/activity+json

HTTP/1.1 200 OK
Content-Type: application/activity+json

{"id": "https://example.com/?author=5", "alsoKnownAs": ["https://example.com/@alice"], ...}
```

The WebFinger response for `acct:alice@example.com` links to `https://example.com/?author=5`.

The `Update` sent to the followers:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "id": "https://example.com/?author=5&activity=update-1",
  "type": "Update",
  "actor": "https://example.com/?author=5",
  "object": {
    "id": "https://example.com/?author=5",
    "type": "Person",
    "preferredUsername": "alice",
    "url": "https://example.com/@alice",
    "inbox": "https://example.com/?author=5&inbox",
    "followers": "https://example.com/?author=5&followers",
    "alsoKnownAs": [
      "https://example.com/@alice"
    ],
    "publicKey": {
      "id": "https://example.com/?author=5#main-key",
      "owner": "https://example.com/?author=5",
      "publicKeyPem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n"
    }
  },
  "to": "https://www.w3.org/ns/activitystreams#Public",
  "cc": "https://example.com/?author=5&followers"
}
```

## Receiver

A receiver detects a re-identification in one of two ways:

1. It dereferences a URL it has stored as an actor's `id` and gets an actor document with a different `id`.
2. It gets an actor document with an `id` it does not know, for example when it verifies the signature of an activity or processes an `Update`, and the `alsoKnownAs` property of the document contains a URL it has stored as an actor's `id`.

In both cases the receiver MUST verify that:

1. the `id` of the document has the same origin as the stored URL;
2. the `alsoKnownAs` property of the document contains the stored URL;
3. dereferencing the stored URL returns an actor document with the same `id`, directly or after a redirect.

The third check is not needed in the first case, where the receiver has just dereferenced the stored URL.

When all checks pass, the receiver MUST:

1. Replace the stored URL with the `id` of the document.
2. Keep its relationships with the actor: follows in both directions, pending follow requests, blocks, mutes, list memberships and similar state.
3. Keep objects attributed to the alias associated with the actor.

Step 2 is simple for a receiver that keys its relationships by an internal identifier of the actor record, because only the record changes. A receiver that keys them by the actor's `id` has to move them to the new `id` as part of step 1.

The receiver does not have to modify stored activities and objects that reference the alias. The alias keeps resolving to the actor and is listed in `alsoKnownAs`, so a stored `Follow` with the alias as `object` is still a follow of the actor. A receiver MAY keep the alias in stored data and resolve it when the data is used. A receiver MAY also update stored references to the `id`, but this invalidates signatures and proofs on the stored data.

The receiver MUST NOT:

1. send `Undo(Follow)` to the alias or the `id`;
2. send a `Follow` to the `id`;
3. create a second actor for the `id`;
4. treat the change as a migration.

If the receiver already has separate actors for the alias and the `id`, it SHOULD merge them into one actor and keep the relationships of both.

## Security considerations

A document served from an origin is authoritative for identifiers on that origin. This is the same authority a receiver grants when it dereferences an `id`. This document does not require integrity proofs to verify a re-identification.

The `alsoKnownAs` property alone is not enough. An actor on a shared server could list the `id` of another actor on the same server. The third check in the receiver section, that the alias resolves to the claimed `id`, prevents this. Only the publisher of the alias can make it resolve to a different `id`.

A document from a different origin that lists the stored URL in `alsoKnownAs` MUST NOT be treated as a re-identification.

Publishers that use [FEP-8b32] integrity proofs SHOULD continue to use them after the change. Proofs made before the change reference the previous key `id`, which is why the previous key `id` has to stay dereferenceable.

## Limitations

This document only covers actor identifiers. Object identifiers on the same origin can change for the same reasons, for example when the permalink structure of a site changes. That case is not covered.

The `Update` is sent from an `id` the receiver does not know yet. Receivers that drop activities from unknown actors do not process it. They notice the change when they next dereference the alias or the key of the actor.

## Implementations

- [ActivityPub plugin for WordPress][WordPress] (planned)

## References

- Christine Lemmer-Webber, Jessica Tallon, Erin Shepherd, Amy Guy, Evan Prodromou, [ActivityPub], 2018
- James M Snell, Evan Prodromou, [Activity Vocabulary][ActivityVocabulary], 2017
- S. Bradner, [Key words for use in RFCs to Indicate Requirement Levels][RFC-2119], 1997
- A. Barth, [The Web Origin Concept][RFC-6454], 2011
- P. Jones, G. Salgueiro, M. Jones, J. Smarr, [WebFinger][RFC-7033], 2013
- silverpill, [FEP-7628: Move actor][FEP-7628], 2023
- silverpill, [FEP-8b32: Object Integrity Proofs][FEP-8b32], 2022
- bumblefudge, bengo, [FEP-e965: Move Activity for Migrations and Announce Activity for Tombstone Events][FEP-e965], 2024
- Jonny Saunders, [FEP-1580: Move Actor Objects with a `migration` Collection][FEP-1580], 2025
- Dmitry Skavish, [FEP-a427: Server Domain Migration][FEP-a427], 2026

[ActivityPub]: https://www.w3.org/TR/activitypub/
[ActivityVocabulary]: https://www.w3.org/TR/activitystreams-vocabulary/
[RFC-2119]: https://tools.ietf.org/html/rfc2119.html
[RFC-6454]: https://www.rfc-editor.org/rfc/rfc6454
[RFC-7033]: https://www.rfc-editor.org/rfc/rfc7033
[FEP-7628]: https://codeberg.org/fediverse/fep/src/branch/main/fep/7628/fep-7628.md
[FEP-8b32]: https://codeberg.org/fediverse/fep/src/branch/main/fep/8b32/fep-8b32.md
[FEP-e965]: https://codeberg.org/fediverse/fep/src/branch/main/fep/e965/fep-e965.md
[FEP-1580]: https://codeberg.org/fediverse/fep/src/branch/main/fep/1580/fep-1580.md
[FEP-a427]: https://codeberg.org/fediverse/fep/src/branch/main/fep/a427/fep-a427.md
[WordPress]: https://github.com/Automattic/wordpress-activitypub

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
