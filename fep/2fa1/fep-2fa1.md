---
slug: "2fa1"
authors: André Menrath <andre.menrath@posteo.de>
status: DRAFT
dateReceived: 2026-10-29
discussionsTo: https://socialhub.activitypub.rocks/t/fep-2fa1-federated-categories/8957
tags: ["category", "classification", "concept"]
---

# FEP-2fa1: Federated Categories

## Summary

This FEP defines a way to represent semantic categories on ActivityPub objects using `Category` objects within `tag`.
Each category has a stable IRI and can be associated with a concept scheme.
Categories can also link to equivalent or related categories in other vocabularies using semantic matching relationships, enabling applications to map, compare, and interpret classifications in federation.


```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/2fa1"
  ],
  "type": "Event",
  "id": "https://instance.example/event/1",
  "name": "Jazz evening",
  "tag": [
    {
      "type": "Category",
      "id": "https://instance.example/vocab/topic/music",
      "name": "Music",
      "summary": "Covers creative work or art using sound.",
      "inScheme": "https://w3id.org/fep/2fa1#Topic",
      "closeMatch": "https://events.example/vocab/category/music",
      "exactMatch": [
        "https://www.wikidata.org/entity/Q638",
        "https://app.example/vocab/topic/music"
      ]
    }
  ]
}
```

> [!IMPORTANT]
> This FEP standardizes relationships between classifications, not authority over classification. A classification is a claim made by whoever publishes it, and each consumer decides how to interpret and act on that claim.

## Rationale

Many Fediverse applications already have categories built in, and nobody should have to give theirs up.
For example, PeerTube and Mobilizon have a predefined list of categories, and LAUTI separates event types from event topics, with lists configurable by each instance.
What is missing is a common way for applications and instances to understand how categories used by others relate to their own.

## Terminology & Requirements

In this FEP, a `Category` identifies a concept that has a particular meaning rather than merely providing a text label.
The iCalendar specification [RFC-5545] has a similar extension that addresses this problem: see [RFC-9253] and [SKOS].

The FEP uses the name `Category` rather than `Concept` because "Category" is a term already familiar to ActivityPub application developers and because it describes the application-level role of these objects.
Technically, the properties defined for `Category` correspond to a subset of [SKOS]; the FEP provides some ActivityPub-friendly JSON-LD aliases via [FEP-888d] so that implementations can use the model without requiring pure SKOS terminology.

The key words "MUST", "MUST NOT", "SHOULD", "SHOULD NOT" and "MAY" are to be interpreted as described in [RFC-2119]. Boxes marked Note, Warning or Important are non-normative.

## Publishing categories

- If an object has categories, they MUST be listed as `Category` objects in its `tag`.
- Category `id`s used on an object SHOULD share the same origin as the object that contains them, putting remote IRIs in the mapping properties.
- A publisher of a list of categories that others are meant to reuse or use as a starter pack (an application or community vocabulary)
  - MUST make every `id` publicly dereferenceable.
  - SHOULD give each category a description via `summary` or `summaryMap`.
  - SHOULD add `exactMatch` or `closeMatch` to categories of widely known vocabularies (other Fediverse applications, Wikidata, schema.org) where one exists.

## Consuming categories

A consumer

- MUST look for a limited number of `Category` objects in an object's `tag`.
- MUST NOT require `Category` objects in an object's `tag`.
- MUST NOT change how an object is processed at protocol level (as its `type` does) by a category, replace its `type`, or act as access control or as a content warning.
- MUST NOT automatically add remote previously unknown categories to the list of categories or tags its users can choose from.
- MUST always treat categories as claims by the publisher of the object.
- MUST match two categories if they have the same IRI, or one has a a trusted claim to an `exactMatch` to the other's IRI, or both have a trusted `extactMatch` to the same IRI.
- SHOULD NOT apply unknown `closeMatch` and `broader` mappings automatically. Those are suggestions and need mapping of a trusted human source.
- SHOULD NOT require category IRIs to be dereferenceable in order to accept an object or the category.
- SHOULD NOT rank or hide objects only because they have no category at all or no category it understands without user initiated filtering.
- SHOULD limit how many categories it processes and how far it follows `broader` and matches.
- MAY treat the `name` of a remote `Category` that it cannot map to its own categories as a `Hashtag`.
- MAY ignore, remap or limit categories.
- MAY ignore `inScheme`.


## Terms and vocabulary

Implementers of this FEP SHOULD add the FEP's context to their objects whenever the data contains a `Category` object.

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/2fa1"
  ]
  ...
}
```

### Category

`Category` and its properties are aliases for the corresponding [SKOS] terms.

| Property for a `Category` | Requirement | Semantics                       | SKOS term (`@id`) |
| ------------------------- | ----------- | ------------------------------- | ----------------- |
| `type`                    | MUST        | `Category`                      | `skos:Concept`    |
| `id`                      | MUST        | IRI identifying the category    | —                 |
| `name` / `nameMap`        | SHOULD      | Label                           | `skos:prefLabel`  |
| `summary` / `summaryMap`  | MAY         | Short description               | `skos:definition` |
| `inScheme`                | MAY         | Classification scheme           | `skos:inScheme`   |
| `broader`                 | MAY         | More general category           | `skos:broader`    |
| `exactMatch`              | MAY         | Category with the same meaning  | `skos:exactMatch` |
| `closeMatch`              | MAY         | Category with a similar meaning | `skos:closeMatch` |

When nested in an object, a `Category` SHOULD be represented as a stub containing `type` and `id`, and optionally `inScheme` and `exactMatch` if available. Consumers can use the IRI to identify the category and may dereference it for additional information.

<section id="Topic" resource="https://w3id.org/fep/2fa1#Topic" typeof="skos:ConceptScheme">
<h3>Topic</h3>
<dl>
<dt>URI</dt>
<dd><code>https://w3id.org/fep/2fa1#Topic</code></dd>
<dt>Label</dt>
<dd property="rdfs:label" lang="en">Topic</dd>
<dt>Comment</dt>
<dd property="rdfs:comment" lang="en">A scheme of categories that say what an object is about: its subject matter. It contains no categories defined by this FEP; a category states its membership with inScheme.</dd>
<dt>Is defined by</dt>
<dd><a property="rdfs:isDefinedBy" href="https://w3id.org/fep/2fa1">FEP-2fa1</a></dd>
</dl>
</section>

<section id="Form" resource="https://w3id.org/fep/2fa1#Form" typeof="skos:ConceptScheme">
<h3>Form</h3>
<dl>
<dt>URI</dt>
<dd><code>https://w3id.org/fep/2fa1#Form</code></dd>
<dt>Label</dt>
<dd property="rdfs:label" lang="en">Form</dd>
<dt>Comment</dt>
<dd property="rdfs:comment" lang="en">A scheme of categories that say what kind of thing an object is within its own object type, such as a concert or a workshop for an event, or a documentary or a tutorial for a video. It contains no categories defined by this FEP; a category states its membership with inScheme.</dd>
<dt>Is defined by</dt>
<dd><a property="rdfs:isDefinedBy" href="https://w3id.org/fep/2fa1">FEP-2fa1</a></dd>
</dl>
</section>

> [!NOTE]
> Topic and Form are interoperability hints, not an ontology of the Fediverse. Whether something is a form, a genre or an object type is not decided here.

---

*All following sections are non-normative.*

## Examples

### Categories embedded within an object

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/2fa1"
  ],
  "type": "Event",
  "id": "https://lauti.example/events/8010",
  "name": "Jazz evening",
  "tag": [
    {
      "type": "Category",
      "id": "https://lauti.example/vocab/type/concert",
      "nameMap": {
        "de": "Konzert",
        "en": "Concert"
      },
      "inScheme": "https://w3id.org/fep/2fa1#Form"
    },
    {
      "type": "Category",
      "id": "https://lauti.example/vocab/topic/jazz",
      "name": "Jazz",
      "inScheme": "https://w3id.org/fep/2fa1#Topic"
    },
    {
      "type": "Hashtag",
      "name": "#Saxophone"
    },
    {
      "type": "Hashtag",
      "name": "#Jazz"
    }
  ]
}
```

### Full category object

Taken from a potential shared vocabulary of an application:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/2fa1"
  ],
  "type": "Category",
  "id": "https://video-application.example/vocab/category/music",
  "nameMap": {
    "en": "Music",
    "de": "Musik",
    "fr": "Musique"
  },
  "summary": "Covers creative work or art that is using sound or music.",
  "inScheme": "https://w3id.org/fep/2fa1#Topic",
  "closeMatch": "https://event-application.example/vocab/category/music",
  "exactMatch": [
    "https://event-application.example/vocab/topic/jazz",
    "http://www.wikidata.org/entity/Q638"
  ]
}
```

Taken from an instance of an application:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/2fa1"
  ],
  "type": "Category",
  "id": "https://event-instance.example/vocab/topic/jazz",
  "name": "Jazz",
  "summary": "Jazz music and events.",
  "inScheme": "https://w3id.org/fep/2fa1#Topic",
  "exactMatch": [
    "https://event-application.example/vocab/topic/jazz",
    "http://www.wikidata.org/entity/Q8341"
  ],
  "broader": "http://www.wikidata.org/entity/Q638"
}
```

## Security considerations

- Authors can attach popular categories to unrelated objects. Limit how many you process.
- A hostile `Category` object can claim an `exactMatch` to a trusted category. Choose which origins you can trust.
- Fetching third party IRIs needs the usual SSRF and rate-limit care.
- Limit how far you follow chains of `broader`.

## Appendix

### Appendix A: How this FEP can help federated categories grow, even if sparsely implemented

This FEP is designed so that an application can adopt it incrementally, without replacing its existing category system.

#### Example: a video platform with predefined categories

Suppose a Fediverse video application (`https://videoapplication.example`) already has a fixed list of category-terms such as `HOWTO`, `MUSIC`, `NEWS`, `SPORTS` and so on.
They have no stable identifiers and no defined meaning beyond the application's own world within the Fediverse.

The application can adopt this FEP step by step:

1. **Give existing categories stable IRIs.**

   A category can initially be published as a small resource containing only its type, IRI and name.
   Each instance of that application uses their own `id` with an exactMatch to the applications IRI.

   ```json
   {
     "@context": [
       "https://www.w3.org/ns/activitystreams",
       "https://w3id.org/fep/2fa1"
     ],
     "type": "Category",
     "id": "https://video-instance.example/vocab/category/HOWTO",
     "name": "How-to",
     "exactMatch": "https://video-application.example/vocab/category/HOWTO",
   }
   ```

2. **Add translations and descriptions.**

   The application can add `nameMap` and `summaryMap`.

3. **State the classification scheme.**

   For example, categories describing what a video is about can use `inScheme` with the FEP's `Topic` scheme, while categories describing what kind of video it is can use `Form`, use other existing `ConceptSchemes`, or invent something new like `https://videoapplication.example/vocab/scheme/Genre` or `https://videoapplication.example/vocab/scheme/MovieType`.

4. **Relate categories to other Fediverse vocabularies.**

   The application can add `exactMatch`, `closeMatch` or `broader` relationships to categories used by other applications.
   A category can thus be related to a category from another application's vocabulary where their meanings overlap.

5. **Relate them to public vocabularies.**

   Where useful, the same categories can also be related to established public concepts such as Wikidata.

#### Example: an instance-configured category system

When creating a new category on an instance an administrator may provide mappings from a community vocabulary.
This allows interoperability to grow from existing category systems rather than requiring a universal taxonomy first.

### Appendix B: Sharing category mappings

For sharing category mappings a community in the Fediverse could utilize "Simple Standard for Sharing Ontological Mappings" ([SSSOM]), which are collaboratively maintained and may get trusted my instance moderators.

### Appendix C: Category as an Actor

ActivityPub does not require actors to have a particular type.
An object can act as an ActivityPub Actor by providing the actor interface, including `inbox` and `outbox`.

A `Category` can therefore also be an Actor by providing these properties.
This is not required by this FEP, but could be useful when a category should boost activities of its own.

### Appendix D: Categories as Collections

A `Category` might additionally be typed as an ActivityStreams `Collection` or `OrderedCollection`.
In this use, the collection contains objects that the application or instance has classified with that category.
For example:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/2fa1"
  ],
  "type": ["Category", "Collection"],
  "id": "https://example.org/categories/music",
  "name": "Music",
  "inScheme": "https://w3id.org/fep/2fa1#Topic",
  "exactMatch": "http://www.wikidata.org/entity/Q638",
  "totalItems": 42,
  "items": [
    "https://example.org/events/1",
    "https://example.org/videos/2",
    ...
  ]
}
```

## References

- [RFC-2119] S. Bradner, [Key words for use in RFCs to Indicate Requirement Levels][RFC-2119], 1997
- [RFC-5545] B. Desruisseaux, [Internet Calendaring and Scheduling Core Object Specification (iCalendar)][RFC-5545], 2009
- [RFC-9253] M. Douglass, Support for iCalendar Relationships, 2022
- [FEP-888d] a, [Using https://w3id.org/fep as a base for FEP-specific namespaces][FEP-888d]
- [SKOS] A. Miles, S. Bechhofer, [SKOS Simple Knowledge Organization System Reference][SKOS], 2009
- [SSSOM] [Simple Standard for Sharing Ontological Mappings][SSSOM]

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.

[RFC-2119]: https://datatracker.ietf.org/doc/html/rfc2119.html
[RFC-5545]: https://icalendar.org/RFC-Specifications/iCalendar-RFC-5545/
[RFC-9253]: https://www.rfc-editor.org/rfc/rfc9253.html
[FEP-888d]: https://codeberg.org/fediverse/fep/src/branch/main/fep/888d/fep-888d.md
[SKOS]: https://www.w3.org/TR/skos-reference/
[SSSOM]: https://mapping-commons.github.io/sssom/
