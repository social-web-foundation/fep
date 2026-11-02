---
slug: "336f"
authors: Daniel Supernault <danielsupernault@gmail.com>
status: DRAFT
discussionsTo: https://socialhub.activitypub.rocks/t/fep-336f/8963
dateReceived: 2026-11-02
trackingIssue: https://codeberg.org/fediverse/fep/issues/970
---
# FEP-336f: Creator Collaborations

## Summary

This proposal describes how an object can credit one or more coauthors besides its author, with each coauthor's consent, in a way that other servers can verify.

The author remains the only `actor` and `attributedTo` of the object, so software that does not implement this proposal sees an ordinary post. The object gains a `coauthors` property that references one `CoauthorAuthorization` per coauthor. Each authorization is published by the coauthor's server, attributed to the coauthor, and states that the coauthor agreed to be credited on that specific object. Receivers dereference every authorization before showing a credit, and coauthors can withdraw their credit at any time.

This version covers coauthors who have an account on the same server as the author. Coauthorship across servers needs an invitation protocol, which is left for future work.

## Motivation

Short-form video, photo and blogging platforms commonly let creators publish one post together, for example a collaboration between two musicians or a brand and a creator. The post appears on both creators' profiles and reaches both audiences.

On the fediverse, the obvious encoding is a list of actors in `attributedTo`. That does not work well in practice:

- Most implementations assume a single `attributedTo` and either take the first entry or reject the object.
- `attributedTo` implies authority over the object. Under the origin-based security model ([FEP-fe34]), every actor in `attributedTo` would be expected to be able to `Update` or `Delete` the object, which is not what a credit means.
- Nothing in `attributedTo` proves that the listed actors agreed to be credited. Any server could claim that a well-known account coauthored its post.

This proposal keeps authority with a single author, makes the credit a separate, consent-backed statement by the coauthor, and lets receivers verify that statement against the coauthor's own server.

## History

- [Loops] implemented Creator Collaborations in October 2026 for video posts, using the mechanism described here.
- The authorization object follows the stamp pattern of [FEP-044f] (`QuoteAuthorization`) and reuses the `interactingObject` and `interactionTarget` properties from [GoToSocial interaction policies].
- A pre-FEP discussion on representing coauthors for federated CMS software ([Pre-FEP: Reassigning Actor and CoAuthor Representation]) explored listing coauthors on the object but did not address verifiable consent.

## Requirements

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this specification are to be interpreted as described in [RFC 2119] and [RFC 8174] when, and only when, they appear in all capitals, as shown here.

## Terminology

- **Author**: the actor in the object's `attributedTo`, who created and controls the object.
- **Coauthor**: an actor credited on the object who is not its author.
- **Coauthored object**: an object with a non-empty `coauthors` property.
- **Publishing server**: the server that hosts the author and the coauthored object.
- **Receiving server**: any server that processes the coauthored object.

## Overview

1. The author asks a coauthor on the same server to collaborate on an object.
2. The coauthor agrees, either for that object or ahead of time for all objects by that author.
3. The publishing server creates a `CoauthorAuthorization`, attributed to the coauthor, naming the object and the author.
4. The object is published with a `coauthors` property that references the authorization, and is delivered to the author's and the coauthor's audiences.
5. Receiving servers fetch each authorization by its `id` and check it before showing the credit.
6. If the credit ends, the authorization is removed, the author sends an `Update` without it, and the coauthor sends a `Delete` of the authorization.

## Coauthored objects

### The `coauthors` property

A coauthored object has a `coauthors` property whose value is an array. Each element references one `CoauthorAuthorization`, either as an object with at least an `id` or as a bare `id` string. Publishing servers SHOULD use objects containing `type`, `id` and `attributedTo`:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/336f"
  ],
  "id": "https://loops.example/ap/users/100/video/200",
  "type": "Note",
  "attributedTo": "https://loops.example/ap/users/100",
  "content": "<p>New track with @bob</p>",
  "published": "2026-10-27T10:00:00Z",
  "to": ["https://www.w3.org/ns/activitystreams#Public"],
  "cc": [
    "https://loops.example/ap/users/100/followers",
    "https://loops.example/ap/users/101",
    "https://loops.example/ap/users/101/followers"
  ],
  "attachment": [
    {
      "type": "Document",
      "mediaType": "video/mp4",
      "url": "https://cdn.loops.example/videos/200.mp4"
    }
  ],
  "coauthors": [
    {
      "type": "CoauthorAuthorization",
      "id": "https://loops.example/ap/users/101/coauthor_authorizations/300",
      "attributedTo": "https://loops.example/ap/users/101"
    }
  ]
}
```

The embedded `attributedTo` is a hint for display before verification. Receiving servers MUST NOT rely on it (see [Verification](#verification)).

A publishing server:

- MUST only list a coauthor whose consent it has recorded (see [Consent](#consent)).
- MUST NOT list the author as a coauthor.
- MUST NOT list the same coauthor twice.
- MAY list more than one coauthor. Loops lists at most one.

### Addressing and delivery

When the object is visible beyond its mentioned recipients, the publishing server SHOULD:

- address each coauthor's actor, and
- address each coauthor's followers collection, in the same field (`to` or `cc`) that holds the author's followers collection, and
- deliver the activity to the coauthor's followers in addition to the author's.

Delivering to the coauthor's followers is possible because the coauthor is on the publishing server. `Update` and `Delete` activities for the object SHOULD reach the same audience.

The coauthor's actor is addressed without a `Mention` tag unless the content mentions them. Some implementations treat an addressed actor without a `Mention` as a silent mention.

## CoauthorAuthorization

A `CoauthorAuthorization` is a public statement, made in the name of the coauthor, that they agreed to be credited on one object by one author.

| Property | Required | Description |
|---|---|---|
| `id` | MUST | URL of the authorization. MUST be on the same origin as the coauthor's actor. |
| `type` | MUST | `CoauthorAuthorization` |
| `attributedTo` | MUST | The coauthor's actor. |
| `interactingObject` | MUST | The `id` of the coauthored object. |
| `interactionTarget` | MUST | The author's actor, i.e. the object's `attributedTo`. |
| `published` | SHOULD | When the coauthor gave consent. |

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/336f"
  ],
  "type": "CoauthorAuthorization",
  "id": "https://loops.example/ap/users/101/coauthor_authorizations/300",
  "attributedTo": "https://loops.example/ap/users/101",
  "interactingObject": "https://loops.example/ap/users/100/video/200",
  "interactionTarget": "https://loops.example/ap/users/100",
  "published": "2026-10-27T10:00:00Z"
}
```

### Serving the authorization

The publishing server:

- MUST serve the authorization at its `id` as `application/activity+json` (or `application/ld+json; profile="https://www.w3.org/ns/activitystreams"`), while the credit is active and the object is published.
- SHOULD place the authorization under the coauthor's actor path, since the statement is made in the coauthor's name.
- MUST stop serving the authorization once the credit has been withdrawn. It SHOULD respond with `410 Gone` and a `Tombstone` with `formerType: "CoauthorAuthorization"`, and MAY respond with `404 Not Found` when it no longer has a record of the authorization (for example after the object or the coauthor's account was deleted).
- SHOULD respond with `404 Not Found` while the object is not published, for example while it is waiting for the coauthor's consent.
- MAY require signed requests if it uses authorized fetch, in which case receivers fetch the authorization with a signed request as they would any other object.
- SHOULD allow only short caching (Loops uses `Cache-Control: max-age=300`), so withdrawals take effect quickly.

## Consent

A publishing server MUST obtain the coauthor's consent before listing them in `coauthors`. This proposal does not define how consent is collected on the server, but it MUST be an explicit action by the coauthor. Two forms are RECOMMENDED:

- **Per-object approval**: the coauthor reviews the object and accepts or declines.
- **Standing trust**: the coauthor has marked the author as trusted, and invitations from that author are approved automatically. The coauthor SHOULD be notified when this happens and MUST be able to withdraw the credit afterwards.

A publishing server SHOULD let users limit who can invite them (for example nobody, accounts they follow, mutuals, or everyone), and MUST NOT allow invitations between accounts where either one blocks the other.

While consent is pending, a publishing server MUST NOT list the coauthor. It MAY hold the whole object back until the coauthor answers. Loops holds the post, and if the invitation is declined or expires, lets the author publish it without the coauthor or discard it.

## Verification

A receiving server MUST NOT show a coauthor credit based on the object alone. For each entry in `coauthors`, it MUST dereference the authorization from its `id` and accept the credit only if all of the following hold:

1. The fetched document's `type` is `CoauthorAuthorization`.
2. The fetched document's `id` equals the URL that was fetched.
3. `interactingObject` equals the coauthored object's `id`.
4. `interactionTarget` equals the coauthored object's `attributedTo`.
5. `attributedTo` is an actor on the same origin as the authorization's `id`, and resolves to an actor whose `id` equals that value.
6. That actor is not the author.
7. In this version of the proposal, the authorization's origin is the same as the coauthored object's origin.

Requirement 5 is what makes the authorization meaningful: under [FEP-fe34], a document fetched from the coauthor's origin speaks for the coauthor. Requirement 7 reflects that this version only covers coauthors on the author's server. A future cross-server extension would relax it.

Entries that fail verification, cannot be fetched, or are not on an `https` URL MUST be ignored. The object itself MUST still be accepted and shown without the failed credits.

Receiving servers:

- SHOULD fetch authorizations asynchronously, after the object has been stored.
- MAY limit how many entries they verify per object. Loops verifies at most three.
- SHOULD apply their usual fetch timeouts, size limits and SSRF protections.

## Updates

On `Create`, a missing or empty `coauthors` means the object has no coauthors.

On `Update` of a coauthored object:

- If `coauthors` is present, it is authoritative. Receivers MUST re-verify the listed entries as described in [Verification](#verification) and MUST remove stored credits that are no longer listed. An empty array removes all credits.
- If `coauthors` is absent, receivers SHOULD leave stored credits unchanged. This keeps updates from software or code paths that do not know about coauthors from silently removing credits.

Publishing servers SHOULD include `coauthors` in every `Update` of an object that currently has, or previously had, coauthors.

## Withdrawal

A credit can end because the coauthor leaves, the author removes the coauthor, either account blocks the other, or the coauthor's account is deleted. When this happens, the publishing server:

1. MUST stop serving the authorization (see [Serving the authorization](#serving-the-authorization)).
2. MUST send an `Update` of the object with the remaining coauthors, using an empty array if none remain.
3. SHOULD send a `Delete` of the authorization from the coauthor's actor to the object's audience:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/336f"
  ],
  "id": "https://loops.example/ap/users/101/coauthor_authorizations/300#delete",
  "type": "Delete",
  "actor": "https://loops.example/ap/users/101",
  "to": ["https://www.w3.org/ns/activitystreams#Public"],
  "cc": ["https://loops.example/ap/users/100"],
  "object": {
    "id": "https://loops.example/ap/users/101/coauthor_authorizations/300",
    "type": "CoauthorAuthorization",
    "interactingObject": "https://loops.example/ap/users/100/video/200",
    "interactionTarget": "https://loops.example/ap/users/100"
  }
}
```

The `Delete` lets receivers drop the credit even if the `Update` is lost, and ties the withdrawal to the coauthor's own signature. When account deletion triggers the withdrawal, publishing servers SHOULD send it before deleting the coauthor's actor, so that receivers can still verify the signature.

A receiving server that gets a `Delete` whose object has `type` `CoauthorAuthorization`:

- MUST only act on it if the signing `actor` is the coauthor stored for that authorization.
- SHOULD check that `interactingObject`, if present, matches the stored object.
- MUST then remove the credit.

Receivers that re-fetch an authorization and get `404` or `410` MUST also remove the credit.

## Compatibility

- Software that does not implement this proposal ignores `coauthors` and shows the object as a post by its author. The coauthor may still receive the activity because they are addressed.
- Software that supports [FEP-044f] already understands the stamp pattern used here, and can reuse its verification code.
- Coauthorship grants no authority over the object. Receivers MUST NOT accept `Update` or `Delete` of the object from a coauthor.

## Security considerations

- **Spoofed credits**: a server can put any actor in `coauthors`, but cannot produce a valid authorization on another server's origin. The embedded copy in the object is never trusted.
- **Same-origin hosts**: on a server that hosts both accounts, the server itself can mint authorizations for any local account. Receivers already trust a server to speak for its own users. Consent is therefore enforced by the publishing server, and these requirements describe the behavior users should expect from it.
- **Reuse**: an authorization names exactly one object and one author, so it cannot be attached to a different post.
- **Amplification**: an object can cause one fetch per listed coauthor. Receivers should cap entries per object and rate-limit fetches per origin.
- **Stale credits**: credits can outlive a withdrawal on servers that missed both the `Update` and the `Delete`. Receivers MAY re-verify periodically, for example when the object is refreshed.

## Privacy considerations

- An authorization is a public statement that two accounts collaborated on an object. Publishing servers SHOULD NOT serve authorizations for objects limited to the local server, and MAY require signed requests for authorizations on non-public objects.
- Coauthors are added to the object's audience, which exposes the object to their followers. Users SHOULD understand this when they accept an invitation.
- Declined and expired invitations never produce an authorization and are not federated.

## Future work

- **Cross-server coauthors**: an invitation flow between servers, for example a `CoauthorRequest` answered with `Accept` carrying the authorization, similar to `QuoteRequest` in [FEP-044f]. This would remove verification requirement 7 and need the coauthor's server to deliver to the coauthor's followers.
- **Roles**: an optional `name` or role on each credit (featuring, producer, sponsor).
- **Coauthor-initiated removal across servers**: once coauthors can live on other servers, the coauthor's `Delete` becomes the primary withdrawal signal.

## Implementations

- [Loops] (loops-server): publishes and verifies coauthored video `Note` objects, with one coauthor per post, per-object approval, standing trust, and invitation privacy settings.

## JSON-LD context

The context document is published at `https://w3id.org/fep/336f`:

```json
{
  "@context": {
    "fep336f": "https://w3id.org/fep/336f#",
    "gts": "https://gotosocial.org/ns#",
    "CoauthorAuthorization": "fep336f:CoauthorAuthorization",
    "coauthors": {
      "@id": "fep336f:coauthors",
      "@container": "@set"
    },
    "interactingObject": {
      "@id": "gts:interactingObject",
      "@type": "@id"
    },
    "interactionTarget": {
      "@id": "gts:interactionTarget",
      "@type": "@id"
    }
  }
}
```

Publishers MAY instead embed these term definitions directly in the object's `@context`.

## References

- Christine Lemmer-Webber, Jessica Tallon, Erin Shepherd, Amy Guy, Evan Prodromou, [ActivityPub], 2018
- James M Snell, Evan Prodromou, [Activity Streams 2.0], 2017
- S. Bradner, [RFC 2119]: Key words for use in RFCs to Indicate Requirement Levels, 1997
- B. Leiba, [RFC 8174]: Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words, 2017
- silverpill, [FEP-fe34]: Origin-based security model, 2024
- Claire, [FEP-044f]: Consent-respecting quote posts, 2024
- [GoToSocial interaction policies]
- [Pre-FEP: Reassigning Actor and CoAuthor Representation] for federated CMS, SocialHub, 2025
- [Loops] server source code

[ActivityPub]: https://www.w3.org/TR/activitypub/
[Activity Streams 2.0]: https://www.w3.org/TR/activitystreams-core/
[RFC 2119]: https://tools.ietf.org/html/rfc2119
[RFC 8174]: https://tools.ietf.org/html/rfc8174
[FEP-fe34]: https://codeberg.org/fediverse/fep/src/branch/main/fep/fe34/fep-fe34.md
[FEP-044f]: https://codeberg.org/fediverse/fep/src/branch/main/fep/044f/fep-044f.md
[GoToSocial interaction policies]: https://docs.gotosocial.org/en/latest/federation/interaction_policy/
[Pre-FEP: Reassigning Actor and CoAuthor Representation]: https://socialhub.activitypub.rocks/t/pre-fep-reassigning-actor-and-coauthor-representation-for-federated-cms/8172
[Loops]: https://github.com/joinloops/loops-server

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
