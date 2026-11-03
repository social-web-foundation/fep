---
slug: f12e
authors: André Menrath <andre.menrath@posteo.de>
status: DRAFT
dateReceived: 2026-10-29
discussionsTo: https://socialhub.activitypub.rocks/t/fep-f12e-consent-respecting-attributions/8956
---

# FEP-f12e: Consent-respecting attributions

## Summary

This document defines how to show, in a consent-respecting way, who has attributed importance to an ActivityPub object, for example as author, contributor or organizer.

It defines an `attributions` property containing a `Collection` of `Relationship` items. Each item states that a party (usually an `Actor`) has attributed importance to the object that carries the property.
It also defines a flow by which the consent of the actors listed in that collection can be requested, proven, and revoked.

> [!NOTE]
> The property `attributedTo` is left unchanged because in current Fediverse applications it is typically used to define the single `Actor` that published that object.

## Motivation

An event may have several organizers, an article several authors, a video several creators.
Credited parties may have different origins, or may not be a Fediverse `Actor` at all.
In practice `attributedTo` is used as "the Actor that published this".
It is not a good place for attribution or credit that is shared or has roles.
Applications that handle multiple ActivityPub object `type`s should not need type-specific properties to find out who has attributed importance to an `Object`.

## Requirements

The key words "MUST", "MUST NOT", "SHOULD", "SHOULD NOT" and "MAY" in this document are to be interpreted as described in [RFC-2119].

The publisher of an object is the `Actor` that published it, usually the `Actor` who sent a `Create` activity with that object and is in its `attributedTo`.

An item in an `attributions` collection is *local* if the origin of its `object` is the same as the origin of the object that contains the collection, and *remote* otherwise. This is independent of which server is processing the object.

## When to use

Most objects need nothing beyond `attributedTo`.
If the only party that attributed importance to an `Object` is the single `Actor` in `attributedTo`, the `attributions` property SHOULD NOT be used.

The `attributions` property SHOULD be used when the object has important attributions and at least one of the following applies:

- More than one party attributed importance to it.
- A party is not an ActivityPub `Actor`.
- The `attributedTo` merely reflects the `Actor` that published the `Object`, without being credited beyond a technical protocol level. This also includes cases where the attributions are not disclosed.

> [!WARNING]
> `attributions` is designed for a "handful" of parties. Very long lists (for example the end credits of a film) may require a different way of being handled.

## Attributions grant no rights

Applications MUST NOT treat being listed in `attributions` as granting any right to update or delete the object.

## Updating attributions

- When the `attributions` of an object change, the publisher MUST send an `Update` of that object.
- The publisher MAY remove any item from `attributions` at any time, without the consent of the listed party.
- An `Update` MUST be addressed to every `Actor` that is listed in the `attributions` after the change, and to every `Actor` that was removed by it, so that removed actors learn about it and listed actors can re-verify.

## Items and kinds of attributions

Items of the `attributions` collection are ActivityStreams `Relationship` objects:

- `subject`: the object that carries the attribution (for example an article).
- `relationship`: The IRI of a property that names the kind of attribution, for example `https://schema.org/author`.
- `object`: the attributed party. This is an `Actor` or, for something that is not an `Actor`, a `Link`.

An item reads "`subject` has `relationship` `object`", for example "Article 1 has the author Actor 1". If given `relationship` MUST be a property defined in this direction (work to party), as schema.org's `author`, `contributor` and `organizer` are.

The `subject` MAY be omitted if the collection is embedded via the `attributions` property, in which case the containing object is the `subject`, or if the `context` of a standalone collection states it. Consumers MUST fill in an omitted `subject` before comparing items (see [Verification](#verification)).

The vocabulary of `relationship` is open-ended, and consumers are not required to understand particular values. A consumer that does not understand a value SHOULD treat the item as a general credit without a role label.

## Disclosure

- If the `attributions` property is present on an object, a consuming application MUST NOT derive attributed items from its `attributedTo`.
- Attributions that should not be visible to a recipient MUST NOT be listed in the collection that is served to that recipient. The `attributions` of an object MAY therefore differ between recipients.

## Establishing consent for being listed in `attributions` in federation

> [!WARNING]
> A malicious actor or application might put `Actor`s into an `attributions` collection without their consent, and so falsely imply that they have attributed importance to an object.

For items of the `attributions` collection:

- Remote items whose `object` is an `Actor` MUST be backed by consent, as described below.
- Local items MAY be trusted via an origin-based security model, where the origin of the object's publisher and the origin of the listed actor are the same. See [FEP-fe34].
- Items whose `object` is not an `Actor` (for example a `Link`) cannot give consent. They are claims made by the publisher only. A consumer MAY ignore them, or display them as unverified.

> [!NOTE]
> This section is inspired by [FEP-044f]. Especially note non-normative sections "Server behavior considerations" and "Security considerations" of FEP-044f, which apply to this FEP accordingly.

### Consent flow

The flow below shows how consent is established, how proof can be given to third parties, and how it can be revoked.
Remote actors MUST NOT be added to an `attributions` collection until their consent has been obtained as follows:

1. **Request**: The publisher sends an `AttributionRequest` addressed (`to`) to the candidate actor. Its `object` is the `Relationship` the candidate is asked to consent to, with `subject`, `relationship` and `object` (the candidate) all stated.
2. **Response**: The candidate replies with an `Accept` or `Reject`. Its `object` is the full `AttributionRequest`. An `Accept` MUST have a `result` property that links to (not embeds) to that dereferenceable `AttributionAuthorization`.
3. **Listing**: On receiving an `Accept`, the publisher MUST add a `Relationship` item with an `attributionAuthorization` property referencing the authorization to the `attributions` collection, and MUST send an `Update` of the object. On receiving a `Reject`, the publisher MUST NOT add the actor.
4. **Revocation**: The actor revokes consent by deleting the `AttributionAuthorization` with a `Delete` activity addressed to the publisher. The `object` of that `Delete` MUST be a `Tombstone` that embeds the `formerType` and the original properties of the authorization, because the publisher can no longer dereference the deleted object to learn what was revoked. On receiving it, the publisher MUST remove the item from `attributions` and MUST send an `Update` of the object.
   The actor MAY also send an `Undo` of the `Accept` (with the complete `Accept` as its `object`) as an additional signal to the publisher. The `Delete` is authoritative.

The `object` of every activity in this flow MUST be embedded in full, not given as an `id` only. For example, an `Undo` MUST contain the complete `Accept`, which contains the complete `AttributionRequest`.

### Verification

A consumer that wants to verify an item of an `attributions` collection whose `object` is a remote `Actor`:

1. MUST dereference the `attributionAuthorization` of the item. If it cannot be retrieved, or returns `410 Gone` or a `Tombstone`, the consent MUST be treated as not given or withdrawn.
2. MUST check that the `id` of the authorization is on the same origin as its `attributedTo`, and that `attributedTo` equals the `object` of the item.
3. MUST, after filling in an omitted `subject` from the containing object, check that the `subject`, `relationship` and `object` of the item equal those of the `Relationship` embedded as the `object` of the authorization.

Consent covers exactly the one `Relationship` that is embedded in the authorization.

A consumer SHOULD re-verify an already verified attribution, when the object is accessed for the first time in a given period of time.

## Terms

<section id="attributions" resource="https://w3id.org/fep/f12e/attributions" typeof="owl:ObjectProperty">
  <h3>attributions</h3>
  <dl>
    <dt>URI</dt>
    <dd><code>https://w3id.org/fep/f12e/attributions</code></dd>
    <dt>Label</dt>
    <dd property="rdfs:label" lang="en">Attributions Collection</dd>
    <dt>Comment</dt>
    <dd property="rdfs:comment" lang="en">An ActivityStreams <code>Collection</code> of <code>Relationship</code> items that list the parties that have attributed importance to an object.</dd>
    <dt>Domain</dt>
    <dd><a property="rdfs:domain" href="https://www.w3.org/ns/activitystreams#Object">Object</a></dd>
    <dt>Range</dt>
    <dd property="rdfs:range" resource="https://www.w3.org/ns/activitystreams#Collection"><a href="https://www.w3.org/ns/activitystreams#Collection">Collection</a> (See <a href="https://www.w3.org/TR/activitystreams-core/#collection">Activity Streams 2.0 Core specification</a> for a complete description)</dd>
    <dt>Required</dt>
    <dd>No</dd>
    <dt>Functional</dt>
    <dd>No</dd>
    <dt>Is defined by</dt>
    <dd><a property="rdfs:isDefinedBy" href="https://w3id.org/fep/f12e">FEP-f12e</a></dd>
  </dl>
  <pre title="Example usage of attributions (non-normative): an article" lang="json">
    <code>
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "Article",
  "id": "https://example.com/article/1",
  "name": "Paper on the Fediverse",
  "attributions": {
    "type": "Collection",
    "totalItems": 3,
    "items": [
      {
        "type": "Relationship",
        "relationship": "https://schema.org/author",
        "object": "https://example.org/actors/1",
        "attributionAuthorization": "https://example.org/actors/1/attributions/1"
      },
      {
        "type": "Relationship",
        "relationship": "https://schema.org/contributor",
        "object": "https://example.net/actors/2",
        "attributionAuthorization": "https://example.net/actors/2/attributions/7"
      },
      {
        "type": "Relationship",
        "relationship": "https://schema.org/contributor",
        "object": {
          "type": "Link",
          "name": "Some Person",
          "href": "https://some.persons.personal.website"
        }
      }
    ]
  },
  "content": "FEP-f12e introduced..."
}
    </code>
  </pre>
  <pre title="Example usage of attributions (non-normative): an event" lang="json">
    <code>
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Event",
  "id": "https://example.com/events/1",
  "name": "Fediverse Meetup",
  "attributions": {
    "type": "Collection",
    "totalItems": 2,
    "items": [
      {
        "type": "Relationship",
        "relationship": "https://schema.org/organizer",
        "object": "https://example.org/groups/1",
        "attributionAuthorization": "https://example.org/groups/1/attributions/3"
      },
      {
        "type": "Relationship",
        "relationship": "https://schema.org/organizer",
        "object": "https://example.com/actors/3"
      }
    ]
  }
}
    </code>
  </pre>
  <pre title="Example usage of attributions (non-normative): a custom relationship" lang="json">
    <code>
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "type": "Video",
  "id": "https://example.com/videos/1",
  "name": "Interview",
  "attributions": {
    "type": "Collection",
    "totalItems": 1,
    "items": [
      {
        "type": "Relationship",
        "relationship": "https://vocab.example/terms/interviewee",
        "object": "https://example.org/actors/4",
        "attributionAuthorization": "https://example.org/actors/4/attributions/2"
      }
    ]
  }
}
    </code>
  </pre>
</section>

<section id="attributionAuthorization" resource="https://w3id.org/fep/f12e/attributionAuthorization" typeof="owl:ObjectProperty">
  <h3>attributionAuthorization</h3>
  <dl>
    <dt>URI</dt>
    <dd><code>https://w3id.org/fep/f12e/attributionAuthorization</code></dd>
    <dt>Label</dt>
    <dd property="rdfs:label" lang="en">has an attribution authorization</dd>
    <dt>Comment</dt>
    <dd property="rdfs:comment" lang="en">References an <code>AttributionAuthorization</code> that proves the consent of the attributed party to be listed in the <code>attributions</code> Collection of an object.</dd>
    <dt>Domain</dt>
    <dd><a property="rdfs:domain" href="https://www.w3.org/ns/activitystreams#Relationship">Relationship</a></dd>
    <dt>Range</dt>
    <dd property="rdfs:range" resource="https://w3id.org/fep/f12e/AttributionAuthorization">An <a href="https://w3id.org/fep/f12e/AttributionAuthorization">AttributionAuthorization</a> (<code>@id</code>)</dd>
    <dt>Required</dt>
    <dd property="owl:minCardinality" content="0" datatype="xsd:nonNegativeInteger">No</dd>
    <dt>Functional</dt>
    <dd property="owl:maxCardinality" content="1" datatype="xsd:nonNegativeInteger">Yes</dd>
    <dt>Is defined by</dt>
    <dd><a property="rdfs:isDefinedBy" href="https://w3id.org/fep/f12e">FEP-f12e</a></dd>
  </dl>
  <pre title="Example of an attributions item referencing its authorization" lang="json">
    <code>
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "Relationship",
  "subject": "https://example.com/article/1",
  "relationship": "https://schema.org/author",
  "object": "https://example.org/actors/1",
  "attributionAuthorization": "https://example.org/actors/1/attributions/1"
}
    </code>
  </pre>
</section>

<section id="AttributionAuthorization" resource="https://w3id.org/fep/f12e/AttributionAuthorization" typeof="rdfs:Class">
  <h3>AttributionAuthorization</h3>
  <dl>
    <dt>URI</dt>
    <dd><code>https://w3id.org/fep/f12e/AttributionAuthorization</code></dd>
    <dt>Label</dt>
    <dd property="rdfs:label" lang="en">Attribution Authorization</dd>
    <dt>Comment</dt>
    <dd property="rdfs:comment" lang="en">A revocable approval stamp issued by an actor. Its <code>object</code> is the <code>Relationship</code> the actor consents to.</dd>
    <dt>Subclass of</dt>
    <dd><a property="rdfs:subClassOf" href="https://www.w3.org/ns/activitystreams#Object">Object</a></dd>
    <dt>See also</dt>
    <dd><a property="rdfs:seeAlso" href="https://w3id.org/fep/f12e/attributionAuthorization">attributionAuthorization</a> | <a property="rdfs:seeAlso" href="https://w3id.org/fep/f12e/AttributionRequest">AttributionRequest</a></dd>
    <dt>Is defined by</dt>
    <dd><a property="rdfs:isDefinedBy" href="https://w3id.org/fep/f12e">FEP-f12e</a></dd>
  </dl>
  <pre title="Example of an AttributionAuthorization" lang="json">
    <code>
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "AttributionAuthorization",
  "id": "https://example.org/actors/1/attributions/1",
  "attributedTo": "https://example.org/actors/1",
  "object": {
    "type": "Relationship",
    "subject": "https://example.com/article/1",
    "relationship": "https://schema.org/author",
    "object": "https://example.org/actors/1"
  }
}
    </code>
  </pre>
</section>

<section id="AttributionRequest" resource="https://w3id.org/fep/f12e/AttributionRequest" typeof="rdfs:Class">
  <h3>AttributionRequest</h3>
  <dl>
    <dt>URI</dt>
    <dd><code>https://w3id.org/fep/f12e/AttributionRequest</code></dd>
    <dt>Label</dt>
    <dd property="rdfs:label" lang="en">Attribution Request</dd>
    <dt>Comment</dt>
    <dd property="rdfs:comment" lang="en">An activity by which the publisher of an object asks an actor for consent to be listed in the <code>attributions</code> of that object. Its <code>object</code> is the <code>Relationship</code> the actor is asked to consent to.</dd>
    <dt>Subclass of</dt>
    <dd><a property="rdfs:subClassOf" href="https://www.w3.org/ns/activitystreams#Activity">Activity</a></dd>
    <dt>See also</dt>
    <dd><a property="rdfs:seeAlso" href="https://w3id.org/fep/f12e/AttributionAuthorization">AttributionAuthorization</a></dd>
    <dt>Is defined by</dt>
    <dd><a property="rdfs:isDefinedBy" href="https://w3id.org/fep/f12e">FEP-f12e</a></dd>
  </dl>
  <pre title="Example of an AttributionRequest" lang="json">
    <code>
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "AttributionRequest",
  "id": "https://example.com/actors/publisher/activities/1",
  "actor": "https://example.com/actors/publisher",
  "to": "https://example.org/actors/1",
  "object": {
    "type": "Relationship",
    "subject": "https://example.com/article/1",
    "relationship": "https://schema.org/author",
    "object": "https://example.org/actors/1"
  }
}
    </code>
  </pre>
  <pre title="Example of an Accept of an AttributionRequest" lang="json">
    <code>
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "Accept",
  "id": "https://example.org/actors/1/activities/5",
  "actor": "https://example.org/actors/1",
  "to": "https://example.com/actors/publisher",
  "object": {
    "type": "AttributionRequest",
    "id": "https://example.com/actors/publisher/activities/1",
    "actor": "https://example.com/actors/publisher",
    "to": "https://example.org/actors/1",
    "object": {
      "type": "Relationship",
      "subject": "https://example.com/article/1",
      "relationship": "https://schema.org/author",
      "object": "https://example.org/actors/1"
    }
  },
  "result": "https://example.org/actors/1/attributions/1"
}
    </code>
  </pre>
  <pre title="Example of a Delete that revokes an AttributionAuthorization" lang="json">
    <code>
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f12e"
  ],
  "type": "Delete",
  "id": "https://example.org/actors/1/activities/9",
  "actor": "https://example.org/actors/1",
  "to": "https://example.com/actors/publisher",
  "object": {
    "type": "Tombstone",
    "id": "https://example.org/actors/1/attributions/1",
    "formerType": "AttributionAuthorization",
    "attributedTo": "https://example.org/actors/1",
    "object": {
      "type": "Relationship",
      "subject": "https://example.com/article/1",
      "relationship": "https://schema.org/author",
      "object": "https://example.org/actors/1"
    }
  }
}
    </code>
  </pre>
</section>

## References

- Christine Lemmer-Webber, Jessica Tallon, Erin Shepherd, Amy Guy, Evan Prodromou, [ActivityPub], 2018
- James M Snell, Evan Prodromou, [Activity Streams 2.0][ActivityStreams], 2017
- S. Bradner, [Key words for use in RFCs to Indicate Requirement Levels][RFC-2119], 1997
- [FEP-8a8e: A common approach to using the ActivityPub Event object type][FEP-8a8e]
- [FEP-fe34: Origin-based security model][FEP-fe34]
- [FEP-044f: Consent-respecting quote posts][FEP-044f]

[ActivityPub]: https://www.w3.org/TR/activitypub/
[ActivityStreams]: https://www.w3.org/TR/activitystreams-core/
[RFC-2119]: https://datatracker.ietf.org/doc/html/rfc2119
[FEP-8a8e]: https://w3id.org/fep/8a8e
[FEP-fe34]: https://w3id.org/fep/fe34
[FEP-044f]: https://w3id.org/fep/044f

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
