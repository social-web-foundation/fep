---
slug: "0caa"
authors: [panos <@panos@catodon.rocks>]
type: implementation
status: DRAFT
dateReceived: 2026-11-17
discussionsTo: https://socialhub.activitypub.rocks/t/fep-0caa-places-on-actors-and-objects/9000
relatedFeps: [FEP-8a8e, FEP-ee3a, FEP-5feb, FEP-268d, FEP-844e, FEP-e03f]
---
# FEP-0caa: Places on actors and objects

## Summary

Several Fediverse applications already say where something is: Pixelfed puts a place on a post, Vernissage on a picture, Mobilizon and Gancio on an event. Each does it a little differently, and nothing says how a person tells other servers where they are based.

This FEP describes one way to write a place, using only terms that Activity Streams 2.0 and schema.org already define. It says what `location` means on an actor, on an object and on an attachment, how to send a place at the precision its owner chose, how to say that a place is a known public place, and what a receiver may and may not do with it. It defines no new terms.

A second FEP, [FEP-e03f], builds on this one to let servers ask each other what they have near a place.

## Requirements language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119] and [RFC 8174] when, and only when, they appear in all capitals, as shown here.

In this document a *producer* is the server that sends a place, and a *consumer* is the server that receives it.

An object is *public* when its `to` or `cc` contains `https://www.w3.org/ns/activitystreams#Public`, as in [FEP-5feb].

## Background

(This section is non-normative.)

Activity Streams 2.0 has had a `Place` type and a `location` property from the start. `location` can be used on any object, actors included. A `Place` can have `latitude`, `longitude`, `radius` and `units`. The vocabulary's own example is an area, "Fresno Area", with a radius of 15 miles.

What is in use today, as seen in public objects in November 2026:

- Pixelfed puts a `Place` in a post's `location`, with a name, coordinates as strings and the country as an English name.
- Vernissage puts a `Place` in each attachment's `location`, with coordinates as strings (sometimes with a decimal comma), a GeoNames id and a country code. It also sends Exif tags as described in [FEP-ee3a].
- Mobilizon puts a `Place` with a schema.org address in an event's `location`, and Gancio one with the address as text. [FEP-8a8e] describes both.
- FediHood puts a `Place` with only a name on each post.
- [places.pub] publishes every OpenStreetMap object as a `Place` with its own `id`, and writes its addresses with vCard terms.
- The W3C Social Web Community Group's Geosocial Task Force has drafts that put a `Place` in `location`, and link a person's own place to a public one with `alsoKnownAs` ([Geosocial explainer], [Personal Places], [Geographical Microsyntax]).

This FEP keeps what these have in common, picks one shape to send, and lists the other shapes as things a consumer should be able to read.

## Terms used

This FEP defines no new terms. It uses these:

| Term | IRI | Defined in | Value |
|---|---|---|---|
| `location` | `https://www.w3.org/ns/activitystreams#location` | [AS2 Vocabulary] | A `Place`. On an event, see [On an event](#on-an-event). |
| `Place` | `https://www.w3.org/ns/activitystreams#Place` | [AS2 Vocabulary] | |
| `latitude`, `longitude` | `https://www.w3.org/ns/activitystreams#latitude`, `...#longitude` | [AS2 Vocabulary] | A number, in decimal degrees. |
| `radius` | `https://www.w3.org/ns/activitystreams#radius` | [AS2 Vocabulary] | A number, zero or more. |
| `units` | `https://www.w3.org/ns/activitystreams#units` | [AS2 Vocabulary] | `cm`, `feet`, `inches`, `km`, `m` or `miles`. `m` when absent. |
| `name` | `https://www.w3.org/ns/activitystreams#name` | [AS2 Vocabulary] | Text. |
| `alsoKnownAs` | `https://www.w3.org/ns/activitystreams#alsoKnownAs` | The Activity Streams context | One URI or several. |
| `tag` | `https://www.w3.org/ns/activitystreams#tag` | [AS2 Vocabulary] | |
| `address` | `http://schema.org/address` | [schema.org] | A `PostalAddress`. |
| `PostalAddress`, `streetAddress`, `addressLocality`, `addressRegion`, `postalCode`, `addressCountry` | `http://schema.org/PostalAddress` and so on | [schema.org] | Text. `addressCountry` is a country code. |
| `discoverable` | `http://joinmastodon.org/ns#discoverable` | Mastodon | `true` or `false`, on an actor. A missing value is not `true`. |
| `exifData` | `http://schema.org/exifData` | [FEP-ee3a] | |

`location` is the Activity Streams property. [FEP-8a8e] speaks of adopting `location` from schema.org, and its examples combine both contexts; this FEP reads the Activity Streams property, which is what the applications listed above send.

The schema.org terms are not in the Activity Streams context. A producer that sends JSON-LD adds them to its `@context`, for example:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    {
      "sc": "http://schema.org/",
      "address": "sc:address",
      "PostalAddress": "sc:PostalAddress",
      "streetAddress": "sc:streetAddress",
      "addressLocality": "sc:addressLocality",
      "addressRegion": "sc:addressRegion",
      "postalCode": "sc:postalCode",
      "addressCountry": "sc:addressCountry"
    }
  ]
}
```

Some applications write the schema.org namespace with `https`. A consumer that does not expand JSON-LD reads the compact names and is not affected; one that does SHOULD treat the `http` and `https` forms of these terms as the same.

## The place

### What a producer sends

A place is an object with `type` `Place`.

It can have these properties:

- `name`: what people call the place.
- `latitude` and `longitude`: a point, in WGS 84 decimal degrees. A producer MUST send both or neither. They SHOULD be JSON numbers, not strings.
- `radius` and `units`: how far the place reaches around the point. A producer MUST NOT send `radius` without `latitude` and `longitude`. A producer SHOULD send `units` whenever it sends `radius`, because the default, metres, is easy to forget.
- `address`: a schema.org `PostalAddress` with the parts that are known. `addressCountry` SHOULD be an ISO 3166-1 alpha-2 code in upper case, such as `GR`, not a country's name.
- `id` and `alsoKnownAs`: see [Public places](#public-places).

A place is one of three things, depending on what it has:

- A **point** has coordinates and no `radius`. It is an exact spot: a café, a theatre, a mountain top.
- An **area** has coordinates and a `radius`. It is everything within that distance of the point: a town, a region.
- A **country** has no coordinates. It has `address.addressCountry` and nothing finer.

`radius` is the size of the place. It is not a measure of how unsure the producer is about the point.

A place is *placeable* when it has coordinates, or a country code, or the `id` of a public place. A place with only a name is not placeable: there is a Paris in France and another in Texas, and a consumer cannot tell which one is meant. A producer that wants its place to be found by location MUST send a placeable place, and SHOULD send coordinates or a country code, since a consumer is not required to resolve an `id`. A name on top of that is welcome.

An area, as a person's place on their actor:

```json
{
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
```

A country:

```json
{
  "type": "Place",
  "name": "Greece",
  "address": {
    "type": "PostalAddress",
    "addressCountry": "GR"
  }
}
```

A point, as the place of a post:

```json
{
  "id": "https://places.pub/node/810790669",
  "type": "Place",
  "name": "Bily Kun",
  "latitude": 45.52346,
  "longitude": -73.58316,
  "address": {
    "type": "PostalAddress",
    "streetAddress": "354 Avenue du Mont-Royal Est",
    "addressLocality": "Montréal",
    "addressRegion": "Québec",
    "addressCountry": "CA"
  },
  "alsoKnownAs": "https://www.openstreetmap.org/node/810790669"
}
```

### What a consumer reads

A consumer MUST be able to read a place written as above.

A consumer MUST accept `latitude` and `longitude` written as JSON numbers, and SHOULD also accept them as strings that hold a decimal number, since several applications send them that way.

A consumer MUST ignore the coordinates of a place, and keep the rest of the place, when:

- only one of `latitude` and `longitude` is present;
- either is neither a number nor (if the consumer accepts strings) a string holding a decimal number;
- latitude is beyond ±90 or longitude is beyond ±180.

A place without coordinates is not invalid: a country is a place with a country code and no coordinates.

When `units` is absent, `radius` is in metres. A consumer that does not know the unit, or finds a `radius` that is not a number or is negative, ignores the `radius` and not the whole place.

A consumer MUST NOT work out coordinates or a country from a place's name alone. It can show such a place as a label, but it does not use it to put the actor or the object on a map, or in a list by distance or by country. The same holds for a place that has only an `id`: a consumer MAY show it as a label, and uses it to place something only after it has resolved the `id` from a source its administrator chose (see [Security considerations](#security-considerations)).

There is one exception. When an object's place has only a name, and the consumer keeps a place for the object's author that has the same name, and that place came from the author's own actor and is one the consumer may keep (see [On an actor](#on-an-actor)), the consumer MAY use the actor's place for the object, at the precision the actor shared it. The author has already chosen to share that place, and the object adds nothing finer.

A consumer SHOULD read an address written with vCard terms, as [places.pub] sends it, as well as a schema.org `PostalAddress`. The vCard terms (`vcard:hasAddress`, `vcard:street-address`, `vcard:locality`, `vcard:region`, `vcard:postal-code`, `vcard:country-name`) are in `http://www.w3.org/2006/vcard/ns#`, which a JSON-LD consumer declares in its context as `"vcard": "http://www.w3.org/2006/vcard/ns#"`. Other shapes that are worth reading are listed under [Input compatibility](#input-compatibility).

`location` is the structured place. Some applications also send a free-text address on profiles, for example as a vCard `Address` property. This FEP does not merge that text into `location`. A consumer that has both SHOULD prefer `location` for maps, lists by place and lists by distance.

## Public places

Many places are known to everybody: a town, a museum, a railway station. Services such as [places.pub] give each of them a stable address that returns a `Place`. Using that address lets two servers know they are talking about the same town without comparing names or coordinates.

There are two ways to refer to a public place, and the difference matters.

A place that **is** the public place, at its own point, SHOULD carry the public place's identifier as its `id`. The `id` MUST be an `http` or `https` URI. This is the case for a venue on a post or on an event. When it does, its `name`, coordinates and address SHOULD agree with what that `id` serves, and a consumer that has fetched the public place MAY prefer the fetched data when they differ.

A place that was **made less precise** than the public place is a different place, and MUST NOT carry the public place's `id`, or any other `id` that names the more precise place. Such a place MAY carry an `id` of its own, for example a personal place that its owner serves. This is the case for a person's town when its point was rounded, or for an area drawn around a town. Such a place SHOULD name the public place in `alsoKnownAs` instead. This is how the [Personal Places] draft links a person's own place to a public one.

A producer MAY also list other identifiers of the same place in `alsoKnownAs`: a Wikidata entity (`https://www.wikidata.org/entity/Q202337`), an OpenStreetMap object, or a GeoNames entry written as `https://www.geonames.org/<id>`.

An OpenStreetMap object has a places.pub address that can be built without asking anyone: `https://www.openstreetmap.org/node/810790669` is `https://places.pub/node/810790669`, and the same for `way` and `relation`.

A place with an `id` and nothing else, or with only an `id` and a `name`, is a valid reference. A consumer is not required to fetch it, so a producer that wants the place to be found by location SHOULD send coordinates and a country code with it.

## Where a place goes

### On an actor

`location` on an actor is the area the person, group or service is based in. It is not where they are at this moment.

A producer MUST NOT put a `location` on an actor unless the person behind the actor chose to share that place with other servers. A producer MUST NOT fill it in from an IP address, a device's position, a server-wide setting or the content of posts.

A producer SHOULD send `location` only on an actor that also has `discoverable` set to `true`. A place on a profile is there to help people find each other, which is what `discoverable` is a consent to.

An actor's `location` SHOULD be a single `Place`. It is usually an area or a country. Nothing forbids a point, but see [Privacy considerations](#privacy-considerations).

When the place changes or is removed, the producer SHOULD send an `Update` of the actor, as it does for any other change to the profile.

A consumer that keeps an actor's place:

- SHOULD keep it, and list the actor by place, only when the actor has `discoverable` set to `true`; a missing `discoverable` is not `true`;
- MUST replace it with what the newest copy of the actor says, and MUST delete it when that copy has no `location`, or when the actor is deleted.

### On an object

`location` on an object such as a `Note`, an `Article`, an `Image` or a `Video` is where the object was made, or where what it tells of happened.

A producer MUST NOT add a `location` to an object unless the author chose a place for that object. In particular a producer MUST NOT copy the place from the author's actor, or from the position recorded inside a picture, without the author asking for it.

A `Place` in an object's `tag` is something else: it is a place the object is about. Someone can write about Tokyo from Lisbon. A consumer that lists objects by place MAY use a `Place` in `tag` when the object has no usable `location`.

A consumer that lists objects by place is doing a search-like operation, so it SHOULD apply the consent rules it applies to its own search of posts (for example `indexable`, [FEP-5feb]). A server that answers place searches for others is held to the stricter rule in [FEP-e03f].

### On an attachment

`location` on an attachment (`Image`, `Video`, `Audio`, `Document`) is where that file was made. A post with pictures from three towns can say so for each picture.

An `Image` or `Audio` attachment can also carry the position that the camera recorded, as `GPSLatitude` and `GPSLongitude` in `exifData`, as [FEP-ee3a] describes. A producer MAY carry the same on a `Video` if its readers do. That position is exact, and FEP-ee3a requires the user's consent before it is sent. When an attachment has no `location` with coordinates and does carry such a position, a consumer MAY use the Exif position in its place.

### On an event

An event's `location` follows [FEP-8a8e], and this FEP adds only two things to it, both refinements:

- `addressCountry` SHOULD be a country code, where event applications commonly send a country name (Mobilizon sends "France", for example).
- A venue that is a public place SHOULD carry its `id`.

What FEP-8a8e allows stays allowed: an event's `location` can hold several places, a `VirtualLocation`, and an address as text. The rules of this FEP on `type` `Place`, on coordinates and on `address` apply to the places among them, and not to a `VirtualLocation` or an address given as text.

```json
{
  "type": "Place",
  "name": "Syntagma Square",
  "address": {
    "type": "PostalAddress",
    "streetAddress": "Syntagma Square",
    "addressLocality": "Municipal Unit of Nafplio",
    "addressRegion": "Peloponnese Region",
    "addressCountry": "GR"
  },
  "latitude": 37.5660207,
  "longitude": 22.7968219
}
```

## Precision

A producer can send a place at any precision. The person who owns the place decides how precise it is, and the producer sends it that way: as a point, as an area of the size they picked, or as a country.

A consumer MAY make a place less precise before it stores or shows it. It can round the coordinates, make the radius larger, or keep only the country.

A consumer MUST NOT present a place as more precise than it was sent. It does not show an area as an exact point, and it does not make a radius smaller.

## Input compatibility

(This section is non-normative.)

These shapes are sent today. They are not the shape a producer should send, but a consumer that reads them will understand more of the network. All of them were read from public objects on 2026-11-07, and personal data was replaced.

Pixelfed, on a post. Coordinates are strings, and `country` is a name in English:

```json
{
  "type": "Place",
  "name": "Barcelona",
  "longitude": "2.158990",
  "latitude": "41.388790",
  "country": "Spain"
}
```

Vernissage, on an attachment. Coordinates are strings and can have a decimal comma, `addressCountry` sits on the place itself, and `geonameId` is a GeoNames id:

```json
{
  "type": "Place",
  "name": "Wrocław",
  "latitude": "51,1",
  "longitude": "17,03333",
  "addressCountry": "PL",
  "geonameId": "3081368"
}
```

FediHood, on a post. A name alone, which is not placeable:

```json
{
  "type": "Place",
  "name": "Wilhelmshaven"
}
```

A personal place from the [Personal Places] draft. `lat` and `lon` stand for `latitude` and `longitude`:

```json
{
  "type": "Place",
  "name": "Home",
  "lat": 45.5245985,
  "lon": -73.5816468,
  "radius": 500,
  "units": "m",
  "alsoKnownAs": "https://places.pub/node/810790669"
}
```

A place from places.pub. The address is a vCard address, and `dcterms:source` points at the OpenStreetMap object:

```json
{
  "type": "Place",
  "id": "https://places.pub/node/810790669",
  "name": "Bily Kun",
  "latitude": 45.52346,
  "longitude": -73.58316,
  "dcterms:source": {
    "type": "Link",
    "href": "https://www.openstreetmap.org/node/810790669"
  },
  "vcard:hasAddress": {
    "type": "vcard:Address",
    "vcard:street-address": "354 Avenue du Mont-Royal Est"
  }
}
```

A list of what a tolerant consumer can read, beyond the shape of this FEP:

- coordinates as numeric strings, with a dot or a comma;
- `lat` and `lon`, or `latitude` and `longitude` inside a `geo` object;
- the country as a code or an English name, in `address.addressCountry`, in `addressCountry` or `country` on the place itself, or in a vCard `country-name`;
- the address as text, as a vCard address under `vcard:hasAddress`, or as flat keys (`street1`, `locality`, `region`, `postalCode`, `country`);
- `nameMap` when there is no `name`;
- `sameAs` and `dcterms:source` as other spellings of `alsoKnownAs`, each a URI or an object with an `id` or an `href`;
- `geonameId`, as `https://www.geonames.org/<id>`;
- an array in `location`, of which the first place that can be read is used.

A position in `exifData` comes in several forms too, because [FEP-ee3a] does not fix one: a plain decimal (`"50.1111"`), a decimal followed by the hemisphere letter (`"50.1111N"`), and the same with or without `GPSLatitudeRef` and `GPSLongitudeRef`.

Some applications cannot send a place at all. A server can still let their users tell it where they are, for example through a bot account that takes a town's name in a private message. FediHood does this, and so does Catodon. A place learned that way was given to one server only, and that server does not pass it on.

## Relation to other work

(This section is non-normative.)

**FEP-8a8e (events).** That FEP describes `location` on an `Event`. This one covers every other object and actors, and writes the place the same way, so one reader serves both. Where the two differ (country codes), this FEP refines FEP-8a8e, as said under [On an event](#on-an-event).

**FEP-ee3a (Exif metadata).** That FEP carries what the camera recorded, including the exact position. `location` on an attachment is what the author chose to say, which can be much less precise. A file can have both.

**FEP-5feb and FEP-268d (search consent).** `indexable` and `searchableBy` say whether posts may be searched. They do not say whether a place may be sent or stored. [FEP-e03f] uses `indexable` when servers search each other by place.

**The Geosocial Task Force.** Its drafts and this FEP agree on the basics: a `Place` in `location`, and `alsoKnownAs` from a person's own place to a public one. The Personal Places draft goes further and gives each person a collection of named places, which this FEP does not cover. The two can be used together. The Task Force's [issue 17] asked for a vocabulary FEP on coordinates and units; the answers given here are WGS 84 and the Activity Streams default of metres.

**Addresses.** places.pub writes addresses with vCard terms. This FEP sends schema.org's `PostalAddress`, because that is the shape [FEP-8a8e] and the event applications already use. A consumer SHOULD read both, as said under [What a consumer reads](#what-a-consumer-reads).

## Privacy considerations

Where someone lives is among the most sensitive things they can share. Used carelessly, it helps stalkers and harassers find people. Everything below follows from that.

**A sent place cannot be taken back.** An actor's `location` is visible to every server that fetches the actor. Removing it later asks other servers to forget it, and a well-behaved server will, but nothing can force one to.

**The person decides.** That is why the rules above forbid filling in a place from an IP address, a device or a server setting, and forbid copying a place onto posts. Applications SHOULD make "not shared" the starting choice.

**The size of the area is what protects, not the rounding.** If a profile says "Nafplio", rounding the coordinates of Nafplio hides nothing: the name already says it. What protects a person is choosing a place large enough to hold many people. A village of two hundred identifies someone almost as well as a street address does. Applications that let people pick a place are encouraged to warn about very small places and to offer the nearest larger town.

**A place on an actor is where someone is based, not where they are.** An application that updates it from a phone's position would publish a record of someone's movements. This FEP does not describe that use and advises against it.

**Points on people.** A consumer SHOULD show a person's place by its name, and SHOULD NOT show the coordinates of a person's place or the exact distance between two people. Distances in broad steps ("under 10 km") are enough to be useful.

**Pictures.** A camera's position is exact to a few metres, and many pictures are taken at home. Stripping the position from an uploaded file unless the owner asks to keep it is good practice, and is what [FEP-ee3a]'s consent rule amounts to.

**Old posts keep their place.** A place on a post stays there when the author moves. Authors can be reminded of that when they add one.

## Security considerations

A place is a claim made by the sender. Nothing proves that an actor is where it says it is, or that a picture was taken where its attachment says. A consumer does not use a place to decide what someone is allowed to do.

Every value in a place comes from another server and is checked like any other input: coordinates for type and range, text for length, arrays for size.

A consumer SHOULD NOT fetch a place's `id` just because an object that mentions it arrived. The sender chooses that address, and fetching it on arrival would let a sender make other servers send requests wherever it likes. A public place that needs looking up can be looked up later, from a service the consumer's administrator chose.

Looking up the `id` of a known public-place provider, such as places.pub, through a service the consumer's administrator chose is not fetching the sender's address, and a consumer MAY do it when it stores the place. What it SHOULD NOT do is request an address that the sender picked.

When a place is embedded in an object with an `id` on another host, the properties in it are still the sender's words, not that host's. A consumer that needs the public place's own data fetches it from that host.

A point at latitude 0 and longitude 0 is nearly always a missing value written as zeros. A consumer MAY ignore such a place when it has no name.

## Versioning and discovery

There is nothing to discover. A producer that implements this FEP sends `location`; a consumer that does not know it ignores the property, as ActivityPub already expects of unknown properties. [FEP-844e] asks that capability discovery not be used where support can be seen from the objects themselves, which is the case here.

This FEP adds no requests, so it has no errors, rate limits or caching rules of its own.

## Conformance

A producer conforms to this FEP when:

1. every place it sends, other than the forms that [FEP-8a8e] allows in an event's `location` (a `VirtualLocation`, an address as text), has `type` `Place`;
2. it sends `latitude` and `longitude` together or not at all, and `radius` only with them;
3. a place it means to be found by location is placeable;
4. it puts a `location` on an actor only when that person chose to share it, and on an object only when its author chose it;
5. a place that was made less precise than a public place does not carry that public place's `id`, or any other `id` that names the more precise place.

A consumer conforms when:

1. it reads a place written as in [What a producer sends](#what-a-producer-sends);
2. it ignores coordinates that are out of range, incomplete, or not a number (or a numeric string, when it accepts strings), and keeps the rest of the place;
3. it does not work out a position from a name alone, except as described under What a consumer reads;
4. it never presents a place as more precise than it was sent;
5. it replaces or deletes a stored actor place when the actor changes, loses its `location` or is deleted;
6. it lists by place only objects that are public.

## Implementations

- [Catodon], from version 26.12.0 (in development). Producer and consumer, for actors, posts, attachments and events.

Catodon's own choices, which this FEP does not require: a person's place is a town (the point rounded to one decimal of a degree, with a 10 km radius), a region (50 km) or a country; a place received on an actor is made at least that coarse before it is stored; a post's own `location` is sent only when the post is public, not local-only and not a reply, a file's place goes with the attachment on any post that carries that file, and an event's places go in the event's `location`; coordinates on attachments are sent as strings, because Vernissage's reader, as read from its source, rejects a post whose attachment has them as numbers.

Applications whose places a consumer of this FEP can read, without their having implemented it: Pixelfed, Vernissage, Mobilizon, Gancio, places.pub.

## Proposals for future versions

(This section is non-normative. Nothing here is implemented.)

- **Numbers on attachments.** Once the applications that need string coordinates on attachments also read numbers, the exception in "Implementations" can go, and "SHOULD be JSON numbers" can become "MUST".
- **A format for the Exif position.** FEP-ee3a could fix one form for `GPSLatitude` and `GPSLongitude`. Signed decimal degrees as a string would be the simplest.
- **Sending `Place` in `tag`.** This FEP describes reading it. Producers could send it for "this post is about that place".
- **A person's named places.** The Personal Places draft's `places` collection could sit next to `location` on an actor.

## References

- S. Bradner, [Key words for use in RFCs to Indicate Requirement Levels][RFC 2119], 1997
- B. Leiba, [Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words][RFC 8174], 2017
- James M Snell, Evan Prodromou, [Activity Vocabulary][AS2 Vocabulary], 2017
- Christine Lemmer-Webber, Jessica Tallon, Erin Shepherd, Amy Guy, Evan Prodromou, [ActivityPub], 2018
- [schema.org], `PostalAddress`
- André Menrath, les, [FEP-8a8e: A common approach to using the Event object type][FEP-8a8e], 2025
- Marcin Czachurski, [FEP-ee3a: Exif metadata support][FEP-ee3a], 2026
- Claire, [FEP-5feb: Search indexing consent for actors][FEP-5feb], 2023
- Daiki "tesaguri" Mizukami, [FEP-268d: Search consent signals for objects][FEP-268d], 2024
- silverpill, [FEP-844e: Capability discovery][FEP-844e], 2025
- panos, [FEP-e03f: Place search between servers][FEP-e03f], 2026
- Social Web Foundation, [places.pub]
- W3C Social Web Community Group, Geosocial Task Force, [Geosocial explainer], [Personal Places], [Geographical Microsyntax], [issue 17]
- [Catodon]

[RFC 2119]: https://datatracker.ietf.org/doc/html/rfc2119
[RFC 8174]: https://www.rfc-editor.org/rfc/rfc8174.html
[AS2 Vocabulary]: https://www.w3.org/TR/activitystreams-vocabulary/
[ActivityPub]: https://www.w3.org/TR/activitypub/
[schema.org]: https://schema.org/PostalAddress
[FEP-8a8e]: https://w3id.org/fep/8a8e
[FEP-ee3a]: https://w3id.org/fep/ee3a
[FEP-5feb]: https://w3id.org/fep/5feb
[FEP-268d]: https://w3id.org/fep/268d
[FEP-844e]: https://w3id.org/fep/844e
[FEP-e03f]: https://w3id.org/fep/e03f
[places.pub]: https://places.pub/
[Geosocial explainer]: https://github.com/swicg/geosocial/blob/main/explainer.md
[Personal Places]: https://github.com/swicg/geosocial/blob/main/personal-places.html
[Geographical Microsyntax]: https://github.com/swicg/geosocial/blob/main/microsyntax.html
[issue 17]: https://github.com/swicg/geosocial/issues/17
[Catodon]: https://codefloe.com/catodon/catodon

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
