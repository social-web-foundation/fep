---
slug: "e03f"
authors: [panos <@panos@catodon.rocks>]
type: implementation
status: DRAFT
discussionsTo: https://socialhub.activitypub.rocks/t/fep-e03f-place-search-between-servers/9001
relatedFeps: [FEP-0caa, FEP-2677, FEP-5feb, FEP-268d, FEP-c180, FEP-844e, FEP-0151]
dateReceived: 2026-11-18
trackingIssue: https://codeberg.org/fediverse/fep/issues/997
---
# FEP-e03f: Place search between servers

## Summary

A server only knows the people and posts its own users have come across. Someone who looks for what is near them finds little on a small server, even when a server next door is full of it.

This FEP lets one server ask another what it has near a place. The asked server publishes a rough map of where it has something, and answers signed searches for a point and a radius, or for a country. It answers only for its own public actors and objects, and only for those whose owners agreed to be found.

The places themselves are written as in [FEP-0caa]. This FEP adds two endpoints, a small JSON document, and the rules that keep the search from telling more than it should.

## Requirements language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119] and [RFC 8174] when, and only when, they appear in all capitals, as shown here.

In this document the *asker* is the server that sends a search, and the *answerer* is the server that receives it.

An object is *public* when its `to` or `cc` contains `https://www.w3.org/ns/activitystreams#Public`, as in [FEP-5feb].

## Overview

(This section is non-normative.)

There are three parts.

1. **Discovery.** The answerer's application actor names two addresses in its `endpoints`: one for searches, one for the coverage.
2. **Coverage.** A public document that says which kinds of thing the answerer offers and, for each one-degree cell of the map, roughly how many actors, objects and events it has there. An asker reads it about once a day and uses it to decide whom to ask, so that a search goes to a few servers that have something there, not to every server it knows.
3. **Search.** A signed `GET` with a point and a radius, or a country, and one kind of thing to look for. The answer is a page of the answerer's own objects.

A plain signed `GET` with query parameters was chosen over a collection that the asker pages through, because the answerer has to decide what is in the answer from the question: an area, a kind, a language. A collection per area would have to be published, cached and kept in step with every change of consent, for areas nobody asked about.

## Terms defined

Both terms are properties of an actor's `endpoints` object.

| Term | IRI | Value |
|---|---|---|
| `placeSearch` | `https://w3id.org/fep/e03f#placeSearch` | The URI that answers searches. |
| `placeCoverage` | `https://w3id.org/fep/e03f#placeCoverage` | The URI of the coverage document. |

The context document of this FEP is published with it as `fep-e03f.jsonld`:

```json
{
  "@context": {
    "placeSearch": {
      "@id": "https://w3id.org/fep/e03f#placeSearch",
      "@type": "@id"
    },
    "placeCoverage": {
      "@id": "https://w3id.org/fep/e03f#placeCoverage",
      "@type": "@id"
    }
  }
}
```

## Discovery

A server that answers place searches MUST have an application actor that can be found as [FEP-2677] describes, and that actor's `endpoints` MUST contain both `placeSearch` and `placeCoverage`.

Both values MUST be `https` URIs on the same host as the application actor, and MUST NOT have a query, a fragment or credentials.

The application actor is found through the `/.well-known/nodeinfo` document, as [FEP-2677] describes: besides the NodeInfo link it holds a link with the `Application` relation.

```json
{
  "links": [
    {
      "rel": "http://nodeinfo.diaspora.software/ns/schema/2.1",
      "href": "https://social.example/nodeinfo/2.1"
    },
    {
      "rel": "https://www.w3.org/ns/activitystreams#Application",
      "href": "https://social.example/actor"
    }
  ]
}
```

and it looks like this:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/e03f"
  ],
  "id": "https://social.example/actor",
  "type": "Application",
  "inbox": "https://social.example/actor/inbox",
  "outbox": "https://social.example/actor/outbox",
  "endpoints": {
    "sharedInbox": "https://social.example/inbox",
    "placeSearch": "https://social.example/nearby/search",
    "placeCoverage": "https://social.example/nearby/coverage"
  }
}
```

The paths are the answerer's choice.

An asker MUST ignore a pair of which either address is not `https`, is on another host than the actor, or has a query, a fragment or credentials.

An asker SHOULD read the application actor again from time to time (once a day is enough), and stops asking a server whose actor no longer names the endpoints.

A server that stops answering removes both properties. From then on it answers `404` at both addresses.

## The coverage document

The coverage tells askers what an answerer offers and where it is worth asking. It is fetched with a plain `GET`, without a signature, and is `application/json`.

```json
{
  "version": 1,
  "updated": "2026-11-12T01:50:00.000Z",
  "kinds": ["actors", "objects", "media", "events", "actor-objects"],
  "cells": [
    {
      "latitude": 37,
      "longitude": 22,
      "countries": ["GR"],
      "counts": {
        "actors": "10-99",
        "objects": "100+",
        "media": "10-99",
        "events": "1-9",
        "actor-objects": "10-99"
      }
    },
    {
      "latitude": 45,
      "longitude": -74,
      "countries": ["CA", "US"],
      "counts": {
        "objects": "1-9"
      }
    }
  ],
  "countries": [
    {
      "country": "GR",
      "counts": {
        "actors": "10-99"
      }
    }
  ]
}
```

- `version` is the number `1`.
- `updated` is when the document was made, as an ISO 8601 date and time.
- `kinds` lists the [kinds](#kinds) the answerer offers, whether or not it has anything in any cell today. A kind that is not listed is not offered.
- `cells` lists the cells in which the answerer has something a search could find. A cell is one degree of latitude by one degree of longitude, and is named by its south-west corner in whole degrees. The cell `{"latitude": 37, "longitude": 22}` covers latitudes from 37 up to, but not including, 38, and longitudes from 22 up to, but not including, 23. `latitude` runs from -90 to 89 and `longitude` from -180 to 179. A point on the north pole belongs to row 89, and a point on the 180th meridian to column -180. A place is counted in the cell that holds its point (the centre, for an area).
- `countries`, in a cell, lists the ISO 3166-1 alpha-2 codes of the countries of what was counted there.
- `counts` has one entry for each [kind](#kinds) the answerer has in that cell, under the kind's own name. A kind with nothing is left out.
- The top-level `countries` lists what has a country and no coordinates (see "a country" in [FEP-0caa]). Only a search by country finds those, besides the placed things in that country.

A count is one of three ranges, written as a string: `"1-9"`, `"10-99"` or `"100+"`.

The answerer:

- MUST NOT publish exact counts;
- MUST count only what it would return to a search (see [What is answered](#what-is-answered));
- MUST list in `kinds` only kinds it answers;
- SHOULD NOT publish an `actors` count for a cell or a country in which fewer than five actors could be found, and MAY leave out any cell, country or kind;
- SHOULD send a `Cache-Control` header that lets the document be kept for some hours. Making it once a day is enough.

The asker:

- MUST ignore a coverage document whose `version` it does not know;
- SHOULD NOT fetch a server's coverage more than about once a day;
- SHOULD ask a server only for kinds that are in its `kinds`, and, for a search of an area, for kinds that its coverage counts in the area. An asker that does not read `kinds` MAY ask only for kinds that the coverage counts in the area, which gives the same servers and kinds when the answerer lists in `kinds` every kind it counts;
- SHOULD, to decide whether to search a server by country, use the `countries` of its cells together with its top-level `countries`;
- MAY read a cell sent with `latitude` 90 as row 89, and one with `longitude` 180 as column -180.

To turn a circle into cells, an asker takes every cell whose rectangle the circle touches. A circle that crosses the 180th meridian touches cells at both ends of the range of longitudes, and a circle that holds a pole touches every column of the row next to it. (This paragraph is non-normative.)

## The search

### Request

A search is a `GET` to the `placeSearch` address with these query parameters:

| Parameter | Meaning |
|---|---|
| `lat`, `lon` | A point, in WGS 84 decimal degrees. Both or neither. |
| `radius` | A distance from the point, in kilometres. Only with a point. |
| `country` | An ISO 3166-1 alpha-2 code. Can be repeated. |
| `kind` | What to look for. Exactly one of the [kinds](#kinds). Required. |
| `lang` | A BCP 47 language tag. Can be repeated. |
| `limit` | The largest number of items wanted on a page. At least 1. |
| `cursor` | Only as part of a `next` address from an earlier page. |

A search MUST name an area: a point, or at least one country, or both. A `radius` without a point, a point with only one of `lat` and `lon`, a coordinate out of range, a `radius` that is not greater than zero, or a `limit` below 1 is an [invalid query](#errors).

- With a point, the area is the circle of `radius` around it. If countries are given too, only what is in those countries counts.
- With countries and no point, the area is those countries as a whole.
- Repeated `country` values and repeated `lang` values are alternatives: a match for any of them counts.

The answerer chooses the radius to use when none is given, the largest radius it accepts, and the largest `limit`. It MAY reduce a radius or a limit that is too large instead of refusing it. It MAY round the point, if it makes the radius larger by as much as the rounding can move the point.

`lang` asks for objects in those languages. An answerer that knows the language of its objects SHOULD apply it. Objects that declare no language MAY be included, and an asker has to expect them. An answerer MAY refuse a tag that is longer than 35 characters, or that is not well formed, as an [invalid query](#errors). It need not check that a tag is registered.

The answerer MUST ignore parameters it does not know.

An asker that rounds `lat` and `lon` to one decimal (about 11 km) before sending, so that the answerer learns less, MUST then add to `radius` the distance between the original point and the rounded one, so that the circle it sends still holds the circle it meant. That distance is never more than about 8 km, and is much less for a point that is already close to a multiple of a tenth of a degree. An asker MAY cap the enlarged radius at the largest radius it uses itself. The circle it sends then may not hold the circle it meant, and the asker accepts that.

### How a place matches

For a search, an actor has the place in its `location`. An object has its own `location` or, when it has none, a `Place` in its `tag` ([FEP-0caa]). An attachment has its own `location` or, when it has none, a position in its `exifData` that the author chose to share ([FEP-ee3a]). The consent rules of those FEPs decide what an answerer holds as such a place; this FEP adds none.

A search finds by a place's point:

- an actor or object whose place has coordinates matches a search with a point when that point (the centre, for an area) is within the circle, and, when countries are given, when the place's country is one of them;
- a place with a country and no coordinates matches only a search by country, for that country;
- a place with coordinates also matches a search by country when its country is given and is one of the countries asked for.

The radius of an area is not used for matching. The coverage counts by cell and a search matches by circle, but both go by the point, so the coverage is a fair guide to what a search will find.

### Signature

The request MUST be signed with an HTTP signature, in the way the two servers already sign their ActivityPub requests ([RFC 9421], or the older [draft-cavage] signatures).

The signature MUST cover the whole question, and say to which server it is put:

- With RFC 9421, the covered components MUST include `@method`, and either `@target-uri`, or `@authority`, `@path` and `@query` together.
- With draft-cavage, the signed headers MUST include `(request-target)`, which holds the path and the query, and `host` and `date`.

The answerer MUST refuse a signature that leaves out any of these, and one that covers the path alone. The query is the whole question, and a signature that left it out could be reused with another question for as long as its date is accepted. A signature that left out the host could be reused at another server that has the same path. The answerer SHOULD also refuse a signature whose date or `created` time is more than a few minutes away from its own clock.

The asker SHOULD sign as its application actor. It MUST NOT sign as the actor of the person who searched, and MUST NOT put anything else in the request that says who they are. The answerer takes the asker to be the server that hosts the actor that owns the signing key.

```
GET /nearby/search?lat=37.6&lon=22.8&radius=25&country=GR&kind=actors&limit=20 HTTP/1.1
Host: social.example
Date: Thu, 12 Nov 2026 10:24:05 GMT
Accept: application/activity+json
Signature: keyId="https://asker.example/actor#main-key",algorithm="rsa-sha256",headers="(request-target) host date",signature="..."
```

### Kinds

A kind says what sort of thing a search looks for. Kinds are not Activity Streams types: `objects` can return a `Note`, an `Article`, a `Video` or anything else the answerer has. The order of kinds is not significant.

| Kind | What it finds |
|---|---|
| `actors` | Actors whose own `location` matches the area. |
| `objects` | Objects with a place that matches the area: the place of the object, or the place of one of its attachments (see [How a place matches](#how-a-place-matches)). |
| `media` | The same as `objects`, but only objects with at least one attachment. |
| `events` | `Event` objects with a place that matches the area and that have not ended. |
| `actor-objects` | Objects by actors whose place matched the area when the object was made, wherever the objects themselves are. Optional; see below. |

An answerer does not have to offer every kind. It lists the ones it offers in `kinds` in its coverage, and answers a search for a kind it does not offer with an [invalid query](#errors) problem.

`actor-objects` is for answerers that remember where an author was based when they wrote something. Other answerers leave it out. It has a privacy cost, described under [Privacy considerations](#privacy-considerations). An answerer that offers it MUST remove the remembered place of an author's objects when the author removes their place or stops sharing it, and the object stops being found by it.

### Answer

The answer is an `OrderedCollectionPage`, served as `application/activity+json`, or as `application/ld+json; profile="https://www.w3.org/ns/activitystreams"` when the asker’s `Accept` prefers it, as ActivityPub allows.

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "id": "https://social.example/nearby/search?lat=37.6&lon=22.8&radius=25&country=GR&kind=actors&limit=20",
  "type": "OrderedCollectionPage",
  "orderedItems": [
    {
      "@context": [
        "https://www.w3.org/ns/activitystreams",
        {
          "toot": "http://joinmastodon.org/ns#",
          "discoverable": "toot:discoverable",
          "sc": "http://schema.org/",
          "address": "sc:address",
          "PostalAddress": "sc:PostalAddress",
          "addressLocality": "sc:addressLocality",
          "addressRegion": "sc:addressRegion",
          "addressCountry": "sc:addressCountry"
        }
      ],
      "id": "https://social.example/users/alice",
      "type": "Person",
      "preferredUsername": "alice",
      "discoverable": true,
      "location": {
        "type": "Place",
        "name": "Nafplio",
        "latitude": 37.6,
        "longitude": 22.8,
        "radius": 10,
        "units": "km",
        "address": {
          "type": "PostalAddress",
          "addressLocality": "Nafplio",
          "addressRegion": "Peloponnese Region",
          "addressCountry": "GR"
        },
        "alsoKnownAs": [
          "https://places.pub/relation/2488391",
          "https://www.wikidata.org/entity/Q202337"
        ]
      }
    }
  ],
  "next": "https://social.example/nearby/search?lat=37.6&lon=22.8&radius=25&country=GR&kind=actors&limit=20&cursor=1"
}
```

(The actor is cut down to the properties that matter here.)

- `orderedItems` holds the actors or objects found. The answerer SHOULD embed each one in full, which saves the asker a request per item. Each embedded item carries its own `@context`, the one it has when it is fetched alone, so that the terms in it mean the same as they do there.
- Each item MUST be the same as what the answerer would return if the asker fetched the item's `id` with the same signature. Nothing is added for the search.
- Each item's `id` MUST have the same origin (scheme, host and port) as the `placeSearch` address.
- Under `objects`, `media` and `events`, each item SHOULD carry the place it was found by: in its own `location`, in a `Place` in its `tag`, in an attachment's `location`, or in an attachment's `exifData`.
- `next`, when present, is the address of the next page, and MUST have the same origin as the `placeSearch` address. The asker uses it as it is and does not build one itself. The answerer MAY stop offering `next` whenever it wants, even if more could be found.
- The answerer SHOULD NOT include `totalItems`.

The order of the items is the answerer's choice. Nearest first, then newest, works well.

### What is answered

The answerer:

1. MUST return only its own actors and objects, never copies of what it received from other servers.
2. MUST return only public objects, and only actors whose actor document carries the `location` the search matched.
3. MUST apply to each item the rules it applies when the asker fetches that item directly. If an author blocks the asker's server, that author and their objects are left out.
4. MUST NOT return an actor under `actors` unless the actor has `discoverable` set to `true`. An actor without `discoverable` is not discoverable.
5. MUST NOT return, under any other kind, an object whose author does not have `indexable` set to `true` ([FEP-5feb]). An author without `indexable` is not indexable. A place search is a search. This version does not read `searchableBy` ([FEP-268d]); an answerer that does MAY also return an object whose `searchableBy` names the asker.
6. SHOULD refuse, with `403`, an asker whose server it has blocked.

### What the asker does with an answer

The asker:

1. MUST drop every item whose `id` does not have the origin of the `placeSearch` address it asked.
2. MUST NOT follow a redirect to another origin, and MUST ignore a `next` that has another origin.
3. MUST treat each remaining item as it treats any object it fetched from that server: it checks it, applies its own blocks and filters, and stores it or not by its usual rules.
4. SHOULD NOT ask a server that it has blocked.

### Searches nobody asked for

An asker can search on its own, for example once a day, so that its users find something before they search themselves. Such a search tells the answerer where the asker is looking, and if the asker chose those areas from its users' places, it would be giving their places away.

So, for a search that no person started:

- the asker MUST choose the area from the answerer's own coverage document and from nothing else, for example by asking about the cells with the highest counts;
- the asker MUST NOT send `lang` or `country` values taken from its users.

This way the answerer learns only that another server asked about cells the answerer itself listed.

## Errors

A refusal SHOULD have a problem details body ([RFC 9457], `application/problem+json`), as [FEP-c180] recommends.

| Status | `type` | When |
|---|---|---|
| `400` | `https://w3id.org/fep/e03f#invalid-query` | The query cannot be read, names no area, or asks for a kind that is not offered. |
| `401` | `https://w3id.org/fep/e03f#signature-required` | There is no signature, it does not verify, its key cannot be found, or it does not cover what it must. |
| `403` | `https://w3id.org/fep/c180#principal-not-authorized` | The answerer does not answer this asker. |
| `404` | (no body needed) | The server does not answer place searches. |
| `429` | `https://w3id.org/fep/c180#rate-limit-exceeded` | The asker sent too many searches. |

An `invalid-query` problem MAY name the parameter at fault in a `parameter` member:

```json
{
  "type": "https://w3id.org/fep/e03f#invalid-query",
  "title": "Invalid query",
  "status": 400,
  "detail": "kind must be one of the kinds this server offers",
  "parameter": "kind"
}
```

## Rate limits and caching

An answerer MAY limit how many searches it takes from one server. When the limit is passed it SHOULD answer `429` with a `Retry-After` header. An asker that gets a `429` SHOULD NOT ask that server again before the time in `Retry-After` has passed. An asker MAY cap that time at its own limit, so that a server cannot silence it for good.

An asker SHOULD keep the answer to a search for a while (some minutes), so that the same question from several of its users is sent once.

An answer depends on who asked. The answerer SHOULD mark it `Cache-Control: private`, so that a shared cache in front of the answerer never gives one asker's answer to another.

The coverage document is the same for everyone and can be cached by anyone.

## Versioning

The coverage document has a `version`, and this FEP describes version `1`. The search request has no version of its own: a server that publishes a coverage of version 1 answers searches as described here.

Things that can be added without a new version: new kinds, new query parameters and new problem types. An answerer ignores a parameter it does not know and refuses a kind it does not offer, and an asker asks only for kinds it finds in the coverage. New optional fields in the coverage can be added without a new version; a new required field needs one.

A change to the meaning of something that exists needs a new version number, and, so that a server can speak two versions at once, a later FEP defines its own endpoint terms for the new version, next to `placeSearch` and `placeCoverage`, and says how the two relate. An asker that meets a version it does not know leaves that server alone. Capability discovery as in [FEP-844e] is not needed for this: the endpoints in the application actor are the discovery.

## Privacy considerations

**What the answerer learns.** Every search tells the answerer which server asked and about which area. On a server with one user, the server is the person. Rounding the point helps a little. People who run a single-user server may prefer to switch off searches that a person starts, and rely on the kind described under [Searches nobody asked for](#searches-nobody-asked-for).

**The coverage is public.** Anyone can read it, including servers the answerer has blocked, since it is not signed. The ranges keep it from counting people one by one, and an answerer that follows the SHOULD above does not publish an `actors` count for a place with fewer than five actors. Even so, on a server with few accounts, `"actors": "1-9"` in one cell still says about where those five to nine people are. Such a server can leave out cells or the `actors` kind, or not offer the search at all.

**Blocks and the coverage.** The coverage is the same for every reader, so it counts people who have blocked one server or another. Those people are still left out of the answers given to the servers they blocked.

**Being findable is a choice.** Search makes it easy to find what was already public but hard to come across. That is why `actors` is tied to `discoverable` and every other kind to `indexable`, and why a missing value is taken as no. An answerer that has finer settings of its own applies those too.

**`actor-objects` remembers.** An answerer that records where an author was based when they wrote a post will go on returning that post for the old area after the author has moved. That shows where someone used to be. An answerer that offers this kind MUST remove those records when the author removes their place or stops sharing it, and is encouraged to tell its users that old posts stay where they were written.

**No totals.** An answer has no `totalItems`, and paging can stop early, so that a search cannot be used to count exactly how many people are in an area.

**Logs.** An answerer has little reason to keep the areas it was asked about for longer than its rate limit needs.

## Security considerations

**Replay.** A signature that does not cover the query would let anyone who saw one signed request ask other questions with it, and one that does not cover the host or the method would let it be sent to another server. This is why the whole request has to be signed.

**Whose objects.** An answer is trusted only for objects of the server that gave it. Dropping items from other origins, and refusing redirects and `next` links to other origins, keeps a server from planting objects in the name of another. The price is that a server whose actors and objects have `id`s on another host than its application actor cannot answer under this FEP. That is meant: such an answer could not be told from a planted one.

**Endpoints.** The two addresses must be on the application actor's own host. Otherwise a server could point askers at a third party, and have them send it signed requests.

**Size.** A coverage document can list up to 64,800 cells, and a page can hold large objects. An asker sets limits on what it reads (bytes, cells, items) and on how long it waits.

**Cost.** A search over a large radius is more work than a fetch. The largest radius, the page size, the number of pages and the rate limit are the answerer's protection, and it chooses them. An asker limits how many servers it asks for one search, so that a search of its own does not become a burst of requests across the network.

**Many servers.** A rate limit per asker does not stop someone who starts many servers to go through an area. What such a person can read is what the owners of those places chose to make findable, and nothing more, but an answerer that is worried about it can limit searches by area as well as by asker, or not answer servers it does not already know.

**False claims.** A server can publish a coverage that is not true, to attract searches and learn where other servers look. An asker limits how many servers it asks for one search, and applies its usual blocks. Rounding the point limits what such a server learns.

**Places are claims.** As in [FEP-0caa], nothing proves that an actor or an object is where it says it is.

## Conformance

An answerer conforms to this FEP when:

1. its application actor names `placeSearch` and `placeCoverage`, both on its own host;
2. its coverage has `version` 1, lists the kinds it offers in `kinds`, names cells by their south-west corner, and gives counts only as the three ranges;
3. it refuses a search whose signature is missing, wrong, or does not cover the method, the host and the query;
4. it returns an `OrderedCollectionPage` whose items are its own, each as a fetch of its `id` would give it, and whose `next` is on its own origin;
5. it follows the six rules of [What is answered](#what-is-answered).

An asker conforms when:

1. it uses the two addresses only when both are `https` and on the host of the server it found them for;
2. it ignores a coverage of a version it does not know;
3. it signs each search, with a signature that covers the method, the host and the query, and not as a user;
4. it drops items from other origins, and does not follow redirects or `next` links to other origins;
5. for searches that no person started, it chooses the area from the answerer's coverage alone.

## Implementations

- [Catodon]

Catodon implements both roles, as answerer and as asker, from version 26.12.0 (in development). Its own choices, which this FEP does not require, are these.

As an answerer it has a default radius of 50 km and a largest of 250 km, pages of at most 40 items and at most five pages for a query, and 60 searches a minute from one server; it rounds the point to one decimal, counts the coverage once a day, and offers all five kinds.

As an asker it asks at most 10 servers per kind, those whose coverage counts the most in the area, and reads the first page only; it does not repeat the same search for 15 minutes, and it searches each server's three busiest cells for each kind once a day. A pause set by `Retry-After` is capped at 24 hours.

Catodon also publishes the two addresses, a `version` and the list of kinds in its NodeInfo document, under `metadata.placeSearch`, and reads that when a server has no application actor link. [FEP-0151] advises against finding capabilities through NodeInfo, and the coverage's `kinds` makes it unnecessary, so this FEP does not include it.

Catodon's asker does not read kinds yet; it asks for a kind only where the coverage counts something of that kind, which for a conforming answerer is the same set of servers. Reading kinds would mean keeping it with the stored coverage (a column and a migration), and is left for later.

## Proposals for future versions

(This section is non-normative. Nothing here is implemented.)

- **A box instead of a circle.** A `bbox` parameter (west, south, east, north) would let an asker ask about exactly one cell, or one tile of a map. It would also suit software that keys places by geohash, since a geohash is a box, and would let askers use the coverage's own grid, which helps both privacy and caching.
- **Time.** `since` and `until` parameters, to ask only for recent objects, or for events in a given week.
- **A capability entry.** An `implements` entry for this FEP on the application actor ([FEP-844e]), for software that wants to list what it supports. The two endpoints are enough to find the search.
- **Other hosts.** A way for an answerer to declare the hosts its actors and objects live on, for servers with custom domains, which this version leaves out on purpose.
- **Consent for single objects.** `searchableBy` ([FEP-268d]) on an object could widen or narrow who may find it by place, beyond the author's `indexable`.
- **Places in `tag`.** A kind that finds objects by a `Place` in `tag` even when the object has a `location` of its own, to find what is about a place and not only what was made there.

## References

- S. Bradner, [Key words for use in RFCs to Indicate Requirement Levels][RFC 2119], 1997
- B. Leiba, [Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words][RFC 8174], 2017
- Christine Lemmer-Webber, Jessica Tallon, Erin Shepherd, Amy Guy, Evan Prodromou, [ActivityPub], 2018
- panos, [FEP-0caa: Places on actors and objects][FEP-0caa], 2026
- Helge, [FEP-2677: Identifying the Application Actor][FEP-2677], 2023
- Claire, [FEP-5feb: Search indexing consent for actors][FEP-5feb], 2023
- Daiki "tesaguri" Mizukami, [FEP-268d: Search consent signals for objects][FEP-268d], 2024
- Evan Prodromou, [FEP-c180: Problem Details for ActivityPub][FEP-c180], 2025
- silverpill, [FEP-0151: NodeInfo in Fediverse Software (2025 edition)][FEP-0151], 2025
- silverpill, [FEP-844e: Capability discovery][FEP-844e], 2025
- M. Nottingham, E. Wilde, S. Dalal, [RFC 9457: Problem Details for HTTP APIs][RFC 9457], 2023
- A. Backman, J. Richer, M. Sporny, [RFC 9421: HTTP Message Signatures][RFC 9421], 2024
- M. Cavage, M. Sporny, [Signing HTTP Messages][draft-cavage], draft 12, 2019
- [Catodon]

[RFC 2119]: https://datatracker.ietf.org/doc/html/rfc2119
[RFC 8174]: https://www.rfc-editor.org/rfc/rfc8174.html
[ActivityPub]: https://www.w3.org/TR/activitypub/
[FEP-0caa]: https://w3id.org/fep/0caa
[FEP-2677]: https://w3id.org/fep/2677
[FEP-5feb]: https://w3id.org/fep/5feb
[FEP-268d]: https://w3id.org/fep/268d
[FEP-c180]: https://w3id.org/fep/c180
[FEP-0151]: https://w3id.org/fep/0151
[FEP-844e]: https://w3id.org/fep/844e
[RFC 9457]: https://www.rfc-editor.org/rfc/rfc9457.html
[RFC 9421]: https://www.rfc-editor.org/rfc/rfc9421.html
[draft-cavage]: https://datatracker.ietf.org/doc/html/draft-cavage-http-signatures-12
[Catodon]: https://codefloe.com/catodon/catodon

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
