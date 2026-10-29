---
slug: "f799"
authors:
  - Hong Minhee <hong@minhee.org>
  - DongU Kang <hinata@natadeco.com>
type: implementation
status: DRAFT
discussionsTo: https://activitypub.space/topic/793/fep-f799-coordinated-inbox-delivery-suspension
dateReceived: 2026-10-29
trackingIssue: https://codeberg.org/fediverse/fep/issues/966
---

# FEP-f799: Coordinated Inbox Delivery Suspension

## Summary

This proposal lets an ActivityPub inbox or HTTPS origin ask peers to suspend
inbox delivery during maintenance or another announced pause. A controller
publishes a `DeliverySuspension` object whose stable URL serves its current
state. `Create` and `Update` activities notify peers of changes, and an
`Undo` of the original `Create` can end a suspension early. Mutual links
establish the controller's authority; WebFinger supplies the origin's side
of that relationship.

HTTP `Link` headers let peers discover the current object even if they
missed the activities. Object Integrity Proofs allow the object to be signed
in advance and served from static storage. A cancellation state on the
object lets new peers learn that a suspension has ended without fetching
activity history.

Every notice has a finite end time. Peers apply local limits to suspension
duration, authority caching, replay protection, and queue storage. Gradual
queue draining reduces traffic bursts after recovery. The protocol does
not require signing or sending activities during the pause.


## Motivation

ActivityPub servers need to stop accepting deliveries for database upgrades,
storage maintenance, and other planned work. Failure-based retry policies
cannot anticipate these interruptions. Peers continue attempting deliveries
until they observe failures, generating traffic and error logs that an advance
notice could avoid.

HTTP already provides `503 Service Unavailable` and `Retry-After` for
temporary overload and scheduled maintenance [RFC 9110]. Those responses
inform a sender after it has made a request. This proposal adds advance
notification, applies it to queued and newly generated deliveries, and lets
the recipient announce an early recovery.

The unit of control is an inbox URL or an explicitly authorized HTTPS origin,
not a physical server or a domain and all its subdomains.
A deployment might keep a cached website readable while its inbox storage
is offline. Conversely, stopping a processing worker does not require
suspending delivery if the inbox can still accept activities into durable
storage.

This proposal covers planned interruptions and other pauses that can be
announced before reception stops. It does not provide failure detection,
continuous availability monitoring, or negotiated delivery rates.


## Requirements

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [BCP 14] when, and only when,
they appear in all capitals, as shown here.

An *inbox* in this document is the exact URL used for ActivityPub inbox
delivery, including a shared inbox. A *controller* is an actor authorized
to announce suspensions for a target inbox or origin. A *peer* is a server
that delivers activities to an affected inbox. An *origin* is the
scheme, host, and port tuple defined in [RFC 6454].


## Establishing control of a target

### Individual inboxes

For an individual inbox, peers MUST verify both of the following:

- The controller actor's `inbox` identifies the target inbox.
- The inbox collection's `inboxOf`, defined in [FEP-5711], identifies that
  actor.

For example, the actor document at `https://social.example/actors/alice`:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "id": "https://social.example/actors/alice",
  "type": "Person",
  "inbox": "https://social.example/actors/alice/inbox",
  "outbox": "https://social.example/actors/alice/outbox"
}
```

The corresponding inbox representation:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/5711"
  ],
  "id": "https://social.example/actors/alice/inbox",
  "type": "OrderedCollection",
  "inboxOf": "https://social.example/actors/alice"
}
```

This proposal grants the mutually linked actor authority to request delivery
suspensions for that individual inbox. It does not grant that actor authority
over other inboxes.

### Shared inboxes

A shared inbox advertises its controller through `deliveryController`
(`https://w3id.org/fep/f799#deliveryController`). Its value MUST be a single
actor URI. Peers MUST verify both of the following:

- The shared inbox collection's `deliveryController` identifies the actor.
- The actor's `endpoints.sharedInbox` identifies that shared inbox.

For example, a controller actor:

```json
{
  "@context": "https://www.w3.org/ns/activitystreams",
  "id": "https://social.example/actor",
  "type": "Application",
  "inbox": "https://social.example/actor/inbox",
  "outbox": "https://social.example/actor/outbox",
  "endpoints": {
    "sharedInbox": "https://social.example/inbox"
  }
}
```

The shared inbox representation:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f799"
  ],
  "id": "https://social.example/inbox",
  "type": "OrderedCollection",
  "deliveryController": "https://social.example/actor"
}
```

Merely listing a shared inbox in an actor's `endpoints` does not establish
control. The reverse link MUST explicitly name the controller.
`deliveryController` identifies an authority, not the set of actors whose
deliveries use the shared inbox.
`inboxOf` MUST NOT be used as a substitute for this shared-inbox delegation.

The controller can be an existing instance actor or another service actor.
Neither a particular actor type nor discovery through [FEP-d556] establishes
authority on its own. This proposal does not require FEP-d556.

### Origins

Peers MUST verify an origin controller independently of any individual or
shared-inbox control relationship. Control of one inbox does not imply
control of its origin.

Peers discover the controller using [WebFinger]. They MUST begin the query
at the target origin's `/.well-known/webfinger` endpoint, preserving any
non-default port, and use the normalized origin as the `resource` value.
No lookup through an account domain, parent domain, or default-port
service can substitute for this query.

For example:

```http
GET /.well-known/webfinger?resource=https%3A%2F%2Fsocial.example&rel=https%3A%2F%2Fw3id.org%2Ffep%2Ff799%23deliveryController HTTP/1.1
Host: social.example
Accept: application/jrd+json
```

```json
{
  "subject": "https://social.example",
  "links": [{
    "rel": "https://w3id.org/fep/f799#deliveryController",
    "type": "application/activity+json",
    "href": "https://social.example/actor"
  }]
}
```

This relation explicitly authorizes its target actor to announce inbox
delivery suspensions for the subject origin. There MUST be exactly one
controller link with this relation, and its `href` MUST be an HTTPS actor
URI. Peers MUST check the returned `subject` against the requested origin
using the normalization below, and MUST verify that the controller's actor
document links back through `controlledOrigin`
(`https://w3id.org/fep/f799#controlledOrigin`). This property contains one
or more origin strings:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f799"
  ],
  "id": "https://social.example/actor",
  "type": "Application",
  "inbox": "https://social.example/actor/inbox",
  "outbox": "https://social.example/actor/outbox",
  "controlledOrigin": ["https://social.example"]
}
```

Peers MAY follow WebFinger HTTPS redirects under [WebFinger]'s security
requirements and their own fetch protections. A redirect delegates the
metadata response, not the scope of the notice: `subject` MUST still
normalize to the original target origin. Peers MUST NOT infer authority
from a generic server-actor link or an actor's origin alone.

The controller MAY be on a different origin if both links are verified.
The `rel` query parameter is a filter, not evidence of authority. Peers
MUST inspect the returned links themselves, because a server may ignore
that filter.
Existing Mastodon-style instance-actor discovery does not by itself
establish support for this relation or grant the authority it describes.

#### Origin normalization

Publishers MUST use the ASCII serialization of an HTTPS origin defined in
[RFC 6454 §6.2] for `targetOrigin`, `controlledOrigin`, and this WebFinger
application's `subject` and query `resource`. This form has no trailing
slash, uses an ASCII host, and omits the default port 443.

Internationalized DNS names MUST use valid IDNA2008 A-labels, as defined
in [RFC 5890] and [RFC 5891]. Publishers converting Unicode names MUST
perform IDNA2008 validation and conversion before publication. Origin
identifiers on the wire MUST be ASCII; peers MUST NOT apply IDNA2003 or
transitional compatibility mappings when comparing them. For example,
`faß.example` is published as `xn--fa-hia.example`, not `fass.example`;
those ASCII hosts identify different origins. A-labels MUST be validated
under IDNA2008 rather than treated as arbitrary `xn--` strings.

For comparison and incoming WebFinger queries, implementations MUST accept
equivalent root-URI spellings, including a trailing `/` and an explicit
default port. Before computing an origin, they MUST parse the input as an
absolute URI under [RFC 3986] and reject it for this purpose unless it has
the HTTPS scheme, a nonempty host, no user information, no query or
fragment component, and a path that is either empty or exactly `/`.
Implementations MUST compute and ASCII-serialize origins according to
[RFC 6454], including its rules for scheme and host case, internationalized
host names, and default ports. Comparisons MUST NOT use string prefixes.

Thus `https://social.example`, `https://social.example/`, and
`https://SOCIAL.example:443/` normalize to `https://social.example`.
`https://social.example:8443` is a different origin.
`https://social.example/users/alice` and `https://social.example/?x=1`
are not origin identifiers for this application. Their ordinary WebFinger
descriptions MUST NOT be treated as origin-control metadata.

Implementations MUST preserve a DNS host's trailing dot when comparing
origins: `https://social.example.` is not interchangeable with
`https://social.example`. IP literals are permitted. IPv4 hosts MUST use
four decimal octets without leading zeros, and IPv6 hosts MUST use the
canonical address form in [RFC 5952], enclosed in brackets when serialized.
Alternative IPv6 spellings are normalized to that form before comparison.
IPv6 zone identifiers and legacy abbreviated, integer, octal, or hexadecimal
IPv4 spellings MUST NOT be accepted as origin identifiers. These host rules
also apply when computing a delivery URL's origin for a scope comparison.

A WebFinger server MUST return the same controller information for
equivalent origin spellings and emit the normalized `subject`. Peers
MUST accept a subject with an equivalent spelling after the checks above.
These rules apply only to this origin-controller discovery application,
not to WebFinger resources in general.

Normalization is for comparison. Implementations MUST NOT rewrite signed
documents before verifying their integrity proofs; proof verification
uses the procedure required by the proof's cryptosuite.

### Verification and caching

Peers MUST authenticate each control activity or fetched suspension object
and verify that its actor or `attributedTo` controller is authorized for
the target inbox or origin. HTTP Signatures, including
deployed draft-cavage signatures or [RFC 9421] signatures, can authenticate
requests. Implementations MUST also bind the authenticated identity to the
activity's actor under their federation authentication rules. Object
Integrity Proofs provide another authentication path, described below.
Neither form of authentication alone establishes control of the target.

Peers MUST also verify ownership of identifiers before recording notice,
revision, or cancellation state. Each control activity's `id` and the
`DeliverySuspension.id` MUST have the same origin as the authenticated
controller actor's `id`. When present, the original `Create.id`, and thus
`announcement`, MUST meet the same condition. An authenticated wrapper or
proof does not authorize its actor to claim another origin's identifiers.
The controller's origin need not equal the target origin if the required
mutual links establish control. A static mirror's location does not change
these identifier rules.

Peers MUST obtain actor and inbox representations from their HTTPS URLs,
and origin-control metadata from the WebFinger query above, unless they
use previously verified cached representations. Objects embedded in a
notification are not sufficient evidence of the reverse link.
The retrieved representations MUST identify the actor and inbox being
verified. Following an HTTP redirect does not change the target inbox's
identity or expand the suspension to a different delivery URL or origin.

Inbox operators SHOULD publish these links before announcing maintenance.
An inbox MAY return a minimal collection representation without exposing its
items. Publishing control metadata does not require making inbox contents
public.

Peers MAY cache verified control relationships and MUST record the
controller that authorized each accepted notice. Each peer MUST define a
finite local maximum age for such evidence, measured from its last
successful verification. HTTP freshness information MAY shorten that age
but MUST NOT extend it beyond the local limit.

When evidence expires, the peer MUST reverify the mutual links before
accepting a new suspension or any change that prolongs an accepted one.
An unsuccessful revalidation attempt, such as a connection failure or
`5xx`, does not by itself revoke a previously verified relationship.
A missing or unusable metadata response is not affirmative evidence of
removal. The peer MAY continue honoring already accepted notices, but
only within the previously accepted `endTime` and applicable proof and
local-policy deadlines. While relying on expired control evidence, a
failed fetch, cached response, renewed proof, or re-delivery MUST NOT
restart or extend those deadlines. Expired evidence MUST NOT authorize
a new notice or a later end time.

This exception preserves an existing grant; it does not treat stale
authority as current. Without fresh evidence, the peer MUST NOT accept
another active revision, including one that changes the schedule, nor
reactivate a notice it has stopped applying. It MAY accept cancellation
under the recorded-controller rule below.

If a successful, authenticated refresh of the control metadata shows the
relationship removed or changed, the peer MUST immediately stop applying
notices that depend on that relationship and MUST NOT accept new notices
on its strength. This is loss of authority, not cancellation of the object.
Reestablishing control still requires normal freshness and replay checks.
Delivery returns to ordinary scheduling and gradual-resume rules.

A peer MAY accept an authenticated cancellation from the recorded
controller, either an `Undo` or a matching cancelled object, without
refreshing target-control metadata. This exception can only end that
controller's previously accepted suspension; it cannot authorize a new
suspension, a revision that prolongs one, or a change of target.

The maximum evidence age is an implementation or deployment policy. This
proposal specifies no common duration and does not promise that every peer
will honor the same maintenance window.


## The `DeliverySuspension` object

A `DeliverySuspension` (`https://w3id.org/fep/f799#DeliverySuspension`) is
an Activity Streams `Object` describing a temporary request to suspend
inbox delivery.
It has the following properties:

- `id` (required): a stable HTTPS URI identifying the notice and serving its
  current complete representation.
- `attributedTo` (required): the single controller actor URI.
- `published` (required): an `xsd:dateTime` with an explicit time zone,
  recording the object's first publication, unchanged across revisions.
- `status` (`https://w3id.org/fep/f799#status`, required): the string
  `active` or `cancelled`. `active` means the request has not been cancelled;
  the time interval still determines whether delivery is suspended now.
- `targetInbox` (`https://w3id.org/fep/f799#targetInbox`): the single exact
  inbox URL whose deliveries are to be suspended. Exactly one of
  `targetInbox` and `targetOrigin` MUST be present.
- `targetOrigin` (`https://w3id.org/fep/f799#targetOrigin`): the single
  HTTPS origin string whose inbox deliveries are to be suspended.
  Its spelling and comparison follow "Origin normalization" above.
- `announcement` (`https://w3id.org/fep/f799#announcement`): the URI of the
  original `Create` activity, required if the object is announced through
  `Create`. A notice published only for fetching MAY omit it. Its presence
  and value MUST be fixed from the object's first publication.
- `revision` (`https://w3id.org/fep/f799#revision`, required): a positive
  JSON integer in the range 1–9007199254740991 ($2^{53}-1$), starting at
  1 and increasing with each revision. Peers MUST reject values outside
  this range. Publishers MUST NOT wrap or reuse revision numbers.
- `startTime` (optional): an `xsd:dateTime` with an explicit time zone,
  indicating when suspension begins.
- `endTime` (required): an `xsd:dateTime` with an explicit time zone,
  indicating when this notice stops authorizing suspension.
- `summary` (optional): a human-readable reason for the interruption.
- `url` (optional): a human-readable status page for this maintenance.

`startTime` and `endTime` reuse the [Activity Vocabulary] properties.
When both are present, `endTime` MUST be later than `startTime`. If
`startTime` is absent, suspension begins when the peer first accepts the
notice. A later revision without `startTime` retains that immediate-start
meaning; it does not wait for another event.

`endTime` is the expiry of the request, not a promise that service will have
recovered. Peers MUST NOT continue suspending delivery solely because of a
notice whose `endTime` has passed. They MAY still defer delivery under
ordinary retry policies, HTTP `Retry-After`, or another active notice.

A notice applies only to ActivityPub delivery `POST` requests. With
`targetInbox`, it covers the exact delivery URL. With `targetOrigin`, it
covers every inbox delivery URL whose computed origin equals the target,
including individual and shared inboxes. Membership is determined from the
actual delivery URL, not the addressed actor's ID.

Neither scope suspends actor, object, key, or media fetches. Peers MUST NOT
extend a notice to a different origin, subdomains, or other ports. An
inbox-scoped notice does not cover a replacement delivery URL; an
origin-scoped notice covers new delivery URLs only within that origin.
Peers SHOULD NOT switch between shared and individual inboxes, in either
direction, solely to evade an accepted suspension. This does not prohibit
ordinary delivery-endpoint changes for other reasons.

The `id`, `attributedTo`, `published`, `announcement` presence and value,
target kind, and target value MUST remain unchanged across revisions.
A controller MUST use a new suspension ID for a different target or a new
event. A fetched-only notice cannot later acquire an `announcement` under
the same ID; publishing through activities requires a new notice in that case.

The JSON-LD context at `https://w3id.org/fep/f799` defines the new terms:

```json
{
  "@context": {
    "fep-f799": "https://w3id.org/fep/f799#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "DeliverySuspension": "fep-f799:DeliverySuspension",
    "deliveryController": { "@id": "fep-f799:deliveryController", "@type": "@id" },
    "controlledOrigin": { "@id": "fep-f799:controlledOrigin", "@container": "@set", "@type": "xsd:string" },
    "targetInbox": { "@id": "fep-f799:targetInbox", "@type": "@id" },
    "targetOrigin": { "@id": "fep-f799:targetOrigin", "@type": "xsd:string" },
    "announcement": { "@id": "fep-f799:announcement", "@type": "@id" },
    "status": { "@id": "fep-f799:status", "@type": "xsd:string" },
    "revision": { "@id": "fep-f799:revision", "@type": "xsd:integer" }
  }
}
```


## Publishing and updating a suspension

A controller publishes the current complete object at its `id`. It MAY
also notify peers with `Create` and `Update`, or publish only for fetching.
An activity MUST have its own unique HTTPS `id`, a `published` timestamp
with an explicit time zone, and an `actor` equal to the object's
`attributedTo`. A `Create` MUST have an `id` equal to `announcement` and
carry revision 1 of the object.

Publicly discoverable notices SHOULD use one public `Create` that can be
delivered unchanged to multiple peers. A publisher MUST NOT change `to`
or other signed activity content while reusing the same activity ID.
This proposal does not require exposing the list of actual delivery
destinations in the activity.

For example, this notice asks peers to stop delivering at 01:00 UTC and
allows time until 05:00 UTC, including an operational margin:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f799"
  ],
  "id": "https://social.example/activities/maintenance-1-create",
  "type": "Create",
  "actor": "https://social.example/actor",
  "published": "2026-10-31T12:00:00Z",
  "to": ["https://www.w3.org/ns/activitystreams#Public"],
  "object": {
    "id": "https://social.example/maintenance/1",
    "type": "DeliverySuspension",
    "attributedTo": "https://social.example/actor",
    "published": "2026-10-31T12:00:00Z",
    "status": "active",
    "targetInbox": "https://social.example/inbox",
    "announcement": "https://social.example/activities/maintenance-1-create",
    "revision": 1,
    "startTime": "2026-11-01T01:00:00Z",
    "endTime": "2026-11-01T05:00:00Z",
    "summary": "Database maintenance; deliveries will resume when ready.",
    "url": "https://status.example/maintenance/1"
  }
}
```

A controller changes the schedule or explanatory metadata with an `Update`.
It MUST increase the object's revision, publish the new complete object
at the same object URL, and sign the replacement if object proofs are
used. Each pushed `Update` MUST use the same actor and carry the complete
revised object, as required for server-to-server `Update` in
[ActivityPub §7.3]. It MUST NOT alter the original `Create`. For example,
an extension:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f799"
  ],
  "id": "https://social.example/activities/maintenance-1-update-2",
  "type": "Update",
  "actor": "https://social.example/actor",
  "published": "2026-11-01T00:30:00Z",
  "to": ["https://www.w3.org/ns/activitystreams#Public"],
  "object": {
    "id": "https://social.example/maintenance/1",
    "type": "DeliverySuspension",
    "attributedTo": "https://social.example/actor",
    "published": "2026-10-31T12:00:00Z",
    "status": "active",
    "targetInbox": "https://social.example/inbox",
    "announcement": "https://social.example/activities/maintenance-1-create",
    "revision": 2,
    "startTime": "2026-11-01T01:00:00Z",
    "endTime": "2026-11-01T06:00:00Z",
    "updated": "2026-11-01T00:30:00Z",
    "summary": "The maintenance window has been extended.",
    "url": "https://status.example/maintenance/1"
  }
}
```

Peers MUST retain the highest accepted revision for a suspension ID and
MUST NOT replace it with a lower revision. Receiving an identical revision
again has no effect. Conflicting state with the same revision is invalid
and MUST NOT replace the accepted state. Authenticated cancellation is
the exception: after the identity, authority, and immutable-property checks,
it applies regardless of revision comparison, as described under
"Cancelling a suspension". A renewed integrity proof over
otherwise unchanged state does not constitute a new revision. Peers MAY
refresh proof metadata after verifying the new proof, without resetting
notice age or revision state. `updated` MAY be included for display but
MUST NOT determine revision ordering.

A peer MAY first learn of a notice from a fetched object or an authenticated
`Update`, even if the `Create` is unavailable. It MUST authenticate the
object, verify target control, check its local freshness and replay rules,
and compare immutable properties with any known version. A revision that
changes any immutable property MUST be rejected and MUST NOT alter retained
revision, cancellation, or notice-age state. A trusted activity can
authenticate its embedded object under the peer's federation rules;
a fetch is not a substitute for authenticating the surrounding activity.
The peer MUST NOT require fetching the original `Create` merely to accept
the current object.

A notice received after its start applies to future delivery attempts, not
requests already in progress. A revision can move the start into the
future, in which case that notice no longer suspends delivery until the
new start. A newer revision MAY extend an expired notice that has not
been cancelled; peers MUST verify authority before applying the extension.

For an origin-wide interruption, a fetched-only notice can omit
`announcement`. The following is an unsigned illustration of its contents;
static proof-based publication adds a valid object proof as described below:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f799"
  ],
  "id": "https://social.example/maintenance/2",
  "type": "DeliverySuspension",
  "attributedTo": "https://social.example/actor",
  "published": "2026-11-07T12:00:00Z",
  "status": "active",
  "targetOrigin": "https://social.example",
  "revision": 1,
  "startTime": "2026-11-08T01:00:00Z",
  "endTime": "2026-11-08T05:00:00Z",
  "summary": "All inboxes on this origin will stop accepting deliveries."
}
```


## Discovering the current object through HTTP

An HTTP service MAY advertise a `DeliverySuspension` object using a
`Link` header as defined in [RFC 8288], with the extension relation
`https://w3id.org/fep/f799#deliverySuspension`. The link target MUST equal
the suspension object's stable `id`, from which its current complete state
can be retrieved. It MUST NOT identify a `Create` activity or a
human-readable status page.

For example, an inbox that cannot accept a delivery:

```http
HTTP/1.1 503 Service Unavailable
Retry-After: 7200
Link: <https://social.example/maintenance/1>; rel="https://w3id.org/fep/f799#deliverySuspension"; type="application/activity+json"
```

This relation means that the linked object describes a suspension affecting
inbox delivery associated with the response's context. It does not mean that
every request to that resource is suspended. Services MAY include the link
in successful responses as well as errors, including responses from a
reverse proxy or CDN. They MAY advertise several notices with separate
links. Publishers SHOULD link only to notices relevant to that response
and remove links when those notices are cancelled or expire.

A peer MAY fetch the link using ActivityPub media types. A static host
SHOULD serve the object with `Content-Type: application/activity+json`
regardless of the request's `Accept` header; content negotiation is not a
requirement for static hosting. Dynamic publishers MAY negotiate an
ActivityStreams representation.

Before applying a fetched object, the peer MUST authenticate it, verify its
controller's authority over the declared target, and apply the same revision,
cancellation, time, and local-policy checks used for inbox-delivered
objects. Authentication MAY use an authoritative fetch under the peer's
federation rules or a valid object proof. A link neither grants authority
nor expands the notice's scope. Fetching an object again MUST NOT reset
an existing revision or cancellation record.

The HTTP response status still applies to the original request. In
particular, a `503` does not acknowledge delivery, and a valid link does
not turn it into a success. A peer that has never accepted a notice MUST
NOT suspend delivery on an object it cannot fetch or verify; ordinary
HTTP error handling and `Retry-After` remain applicable.

Failure to fetch an already accepted object's stable URL, including a
connection failure, `5xx`, `404`, or `410`, is not cancellation. The peer
MAY continue applying the previously accepted state within its existing
deadlines, subject to the control-verification rules above. Such a failure
MUST NOT erase cancellation or highest-revision records, reset notice
age, or extend any deadline. An authenticated cancelled object or `Undo`,
not the absence of a file, communicates cancellation.

Peers SHOULD cache link-discovery results and bound fetch frequency,
response size, redirect count, and fetch depth. Receiving the same link
on repeated failed deliveries SHOULD NOT cause an unbounded series of
metadata requests.

The object URL is the current-state resource; activity URLs identify
individual notifications and MUST NOT be rewritten with new state.
Publishers SHOULD use HTTP cache validators and cache lifetimes appropriate
to their operational needs. An HTTP `304` only revalidates cached content;
it does not prove a new signature time or renew cached controller authority.

While deferring deliveries, peers SHOULD conditionally fetch the current
object at a jittered interval chosen under local request and resource
budgets. They SHOULD also attempt a bounded revalidation before resuming,
so they can discover a verified extension or cancellation even if push
notifications were missed. These GET requests are not delivery POSTs and
are not suspended by the notice. Peers SHOULD avoid simultaneous polling
or an extra fetch for every queued activity.

Successful revalidation is not a prerequisite for resumption. A failed
or incomplete fetch MUST NOT postpone resumption beyond an existing
deadline. A newly authenticated revision can change that deadline only
after the normal authority, freshness, and replay checks. Ordinary HTTP
backoff or `Retry-After` may still delay actual delivery.


## Static hosting with Object Integrity Proofs

Controllers MAY sign the complete `DeliverySuspension` object in advance
using Object Integrity Proofs [FEP-8b32] and serve it from static storage or
a CDN. The canonical object ID MUST meet the identifier-ownership rule
above. Its HTTPS URL MAY redirect to static storage on another origin;
a peer accepting a copy from a different origin MUST verify its object
proof rather than trusting the storage host.

Publishers and verifiers MUST follow FEP-8b32's proof generation,
verification, and actor-binding rules. In particular, the verification
method MUST be an authorized `assertionMethod` of the actor identified by
`attributedTo`, or of its provably associated identifier as permitted by
FEP-8b32. Merely naming an actor in `attributedTo` does not bind the key to
that actor. An unresolved key, unsupported cryptosuite, or expired proof
does not authorize suspension through this authentication path.

An object proof authenticates the object, not a surrounding activity.
Pushed activities still require their own authentication. If a publisher
adds an integrity proof to a `Create` or `Update`, that proof MUST cover
the complete activity, including its embedded object, and be verified
against its `actor`. A valid HTTP delivery signature is another activity
authentication path.

The static host needs neither the controller's private key nor the ability
to sign HTTP responses. A peer's signed fetch request
authenticates the requester, not the downloaded object. Serving a file
over HTTPS on an unrelated static host is not, by itself, evidence that
the controller issued it.

Proof verification does not replace target-control verification. Operators
SHOULD keep public actor documents, verification methods, and inbox or
WebFinger control metadata available independently of the application
being maintained. A peer MAY use verified cached metadata under the rules
above, but a new peer may need to fetch it. Private signing keys need not
be available during maintenance.

Static hosting does not introduce a weaker hint tier. An unverified
object MUST NOT create, extend, or cancel a suspension merely because
it is available at a linked URL. HTTP `Retry-After` retains its ordinary,
independent role.

To change the schedule, the controller increases the object's revision,
generates a new proof, and replaces the file at the stable object URL.
To cancel, it publishes a newly signed `cancelled` revision at that URL.
Peers do not need separately hosted `Update` or `Undo` files to discover
these changes.

An integrity proof establishes authenticity, not that a snapshot is the
latest revision. Proof `created` and `expires` values, when present, MUST
be checked under the peer's local freshness policy, but do not establish
that no newer snapshot exists. `endTime` and proof expiry, if any, both
limit applicability; neither extends the other. Peers MUST retain the
normal ordering, cancellation, authority-age, and replay checks.
A canonical URL can also return stale content through a cache; its origin
alone does not establish freshness.

Publishers SHOULD retain the cancelled object long enough for their peers
to discover it and SHOULD remove obsolete discovery links. Removing a
file or link does not recall cached copies. A peer that missed cancellation
can continue to defer on an older snapshot until its applicable local,
proof, or notice deadline. Control metadata that is merely unreachable
does not shorten that existing grant; confirmed removal of the
relationship does.


## Cancelling a suspension

A controller cancels a notice by increasing its revision and publishing
the complete object with `status` set to `cancelled`. A fetched-only notice
needs no activity. If the notice has an `announcement`, the controller
SHOULD also send an `Undo` identifying the original `Create`, not the
`DeliverySuspension` object or an `Update`. The `Undo` MUST have its own
unique HTTPS `id`, a `published` timestamp, and the same actor as the
original `Create`. The same-actor requirement follows [ActivityPub §7.11].
As with other control activities, `published` MUST include an explicit time
zone.

The same operation cancels future maintenance or ends an ongoing suspension
early. It does not assert that a process has restarted or guarantee that
subsequent deliveries will succeed.

For example, the object after the extended suspension above is cancelled:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f799"
  ],
  "id": "https://social.example/maintenance/1",
  "type": "DeliverySuspension",
  "attributedTo": "https://social.example/actor",
  "published": "2026-10-31T12:00:00Z",
  "status": "cancelled",
  "targetInbox": "https://social.example/inbox",
  "announcement": "https://social.example/activities/maintenance-1-create",
  "revision": 3,
  "startTime": "2026-11-01T01:00:00Z",
  "endTime": "2026-11-01T06:00:00Z",
  "updated": "2026-11-01T03:00:00Z",
  "summary": "Database maintenance is complete.",
  "url": "https://status.example/maintenance/1"
}
```

The corresponding push notification:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/f799"
  ],
  "id": "https://social.example/activities/maintenance-1-undo",
  "type": "Undo",
  "actor": "https://social.example/actor",
  "published": "2026-11-01T03:00:00Z",
  "to": ["https://www.w3.org/ns/activitystreams#Public"],
  "object": "https://social.example/activities/maintenance-1-create"
}
```

An authenticated cancelled object or an accepted `Undo` ends the suspension
for every revision of that object. An authenticated `Update` carrying a
cancelled object has the same effect. Peers MUST record cancellation as a
terminal fact and MUST NOT reactivate the ID from a later fetch, `Create`,
or `Update`, even one with a higher revision. Cancellation takes precedence
over conflicting active state; learning a cancellation does not require
replacing retained higher-revision data with lower-revision data.
A publisher MUST NOT emit an active revision after cancellation.
A new suspension requires a new object ID and, if pushed, a new announcement.
The cancelled object remains a `DeliverySuspension`, not an Activity Streams
`Tombstone`.

If an `Undo` arrives before its `Create`, a peer MAY fetch and authenticate
the referenced activity to establish the connection immediately. If it
cannot, it MAY retain a pending cancellation keyed by the authenticated
actor and referenced `Create.id`, after checking their identifier origins
and local replay rules. This record alone MUST NOT change delivery policy
or cancel another actor's activity. If that actor's matching `Create`, or
an object with the matching controller and `announcement` through an
`Update` or fetch, later arrives, the peer MUST perform the normal activity
or object authentication, identity, authority, and immutable-property
checks. It MUST then apply the pending cancellation before activating the
notice, regardless of which of those paths supplied the object.
Peers SHOULD bound pending-cancellation counts and retention.

Publishers MUST NOT make a pre-signed cancellation object or `Undo`
publicly accessible before cancellation is intended. Anyone can relay it
once available; its signature timestamp does not schedule its effect.

If several notices apply to one inbox, whether directly or through its
origin, delivery remains suspended while any accepted notice is within
its effective interval. Cancelling or expiring one notice does not
cancel another.


## Local freshness and replay policies

Every peer MUST define finite local limits for accepted notice age, future
publication clock skew, and the age of cached control evidence. It MAY
also limit the future scheduling horizon, effective suspension duration,
and queue retention. Implementations MAY expose these limits as operator settings.
This proposal prescribes no numerical defaults, common maximum, or minimum
retention period across deployments.

The notice-age limit is measured from the object's immutable `published`,
not the time of fetch, delivery, or revision. A newer `revision`, proof,
`updated`, or wrapper `published` MUST NOT restart that age. A peer MUST
reject a suspension whose first publication is too far in the future or
whose notice age exceeds its local limit. It MUST also enforce its local
activity replay policy using each wrapper's `published`; authenticity
alone does not establish freshness.

An accepted notice stops authorizing deferral at the earliest of its
`endTime`, applicable proof expiry when relying on that proof, the local
notice-age limit, or any local duration limit. When control evidence ages
out, an already accepted notice can continue within these existing bounds
if revalidation is unsuccessful, as described under "Verification and
caching"; stale evidence cannot authorize a new suspension or extension.
Confirmed removal of control stops the dependent notice immediately.
Stopping on one of these grounds does not assert that reception has
recovered. Ordinary HTTP failures and backoff may continue to defer deliveries.

Peers MUST retain cancellation and highest-revision state while old
snapshots of the notice remain admissible under their local policies.
This requirement also applies to pending cancellation pairs.
They MAY discard that state once all such snapshots would be rejected.
Changing policy to allow older notices MUST NOT make discarded
cancellations or revisions replayable; implementations can preserve
per-controller publication cutoffs rather than retaining every notice
forever. A cached fetch or re-delivery MUST NOT reset these cutoffs.

For example, one deployment might accept notices for up to 30 days after
first publication, reverify control evidence after 24 hours, and retain
notice state through its acceptance window. Another might choose a
week-long control cache for longer offline work, or much shorter notice
and cache limits to conserve resources. These are illustrations, not
recommended defaults. Cache, notice, and queue limits serve different
purposes and need not have equal values. Operators choosing shorter limits
may resume ordinary retry behavior before the announced pause ends.


## Delivery behavior

Peers implementing this proposal SHOULD defer ordinary deliveries during
an accepted suspension. This applies both to existing queue entries and
new deliveries. They MAY impose a local maximum suspension duration and
MUST NOT interpret a notice as an obligation to retain an unbounded queue.

Deferral itself MUST NOT count as a successful delivery or a failed
delivery attempt. Peers SHOULD exclude time deferred under this proposal
from retry-age calculations. Independent maximum retention periods and
storage limits MAY still apply. This proposal does not guarantee eventual
delivery.

Only this proposal's `Create(DeliverySuspension)`,
`Update(DeliverySuspension)`, and
corresponding `Undo` control activities are exempt from its delivery
suspensions. A peer MUST NOT defer those activities solely because of such
a suspension. Authentication, authorization, blocking policies, rate
limits, and failure backoff still apply. A generic `Create`, `Update`, or
`Undo` is not exempt just because of its activity type.

For example, if A and B both suspend inbox delivery, A's cancellation
notification to B is not held by B's announced suspension. If B actually
returns `503`, ordinary HTTP retry handling still applies; the exemption
does not require bypassing a `Retry-After` or continuously retrying.

At cancellation or expiry, peers SHOULD apply randomized delay and drain
queues with bounded per-destination concurrency and delivery rates.
Ending suspension MUST NOT itself reset failure backoff or override a
still-applicable HTTP `Retry-After`. It permits delivery under the peer's
other scheduling rules; it is not an instruction to flush the queue.


## Conformance

A publisher MUST serve the complete current `DeliverySuspension` at its
stable URL, include the required object fields, increase the revision on
each state change, and publish the mutual control links for its chosen
target scope. It MUST keep cancelled IDs terminal. A publisher using push
MUST also follow the activity
identity, authentication, and announcement rules. Object Integrity Proofs
and HTTP discovery links are optional publication features; each has the
additional requirements in its section.

A receiving peer MUST apply the identity, authority, scope, time,
revision, cancellation, and local-policy checks regardless of whether it
learns state through a fetch or an activity. It MUST process verified
cancelled objects and `Undo` consistently, protect against replay, and
preserve control-activity exceptions and gradual-resume behavior.
Applying an otherwise valid suspension is subject to the delivery
recommendation and local limits above; conformance does not promise
unbounded storage or equal retention across peers. Object Integrity
Proof support is optional: a peer without it MUST NOT trust an object
solely because it carries a proof it cannot verify.


## Operational guidance

This section is non-normative.

Operators should announce maintenance while actor documents, inbox metadata,
signing keys, and outbound delivery are still available. The end time should
include a margin beyond the expected work. No renewal during maintenance
is required. An operator with a separate working control service can send
updates, but peers cannot assume that service exists.

Once inbox reception is ready, the controller should send cancellation
notices at a bounded rate and concurrency, spreading them across peers
rather than releasing all peers at once. Randomizing peer order avoids
always favoring the same peers. Sender-side spreading complements, but
does not replace, peer-side jitter: peers may also resume at the common
expiry time without receiving a cancellation.

Controllers can notify known federation peers, preferably their service
actors when known, using ordinary ActivityPub addressing and delivery.
They need not obtain acknowledgements or every peer's consent before
starting work. Peer discovery is incomplete, so notifications are
best-effort. A successful HTTP inbox response does not prove that the
receiver implements this proposal or has applied the notice.

During an interruption, an HTTP service that can still answer inbox requests
should return `503 Service Unavailable` with `Retry-After` where possible,
and can include a discovery link to a pre-signed suspension object.
This remains useful for peers that missed the notice or do not support
this extension. An HTTP service must not acknowledge a delivery as
successful unless it has actually accepted responsibility for it.

For unexpected failures, use HTTP error responses when available and
ordinary retry backoff when no HTTP response is possible. Peers must not
wait indefinitely for a recovery activity that might never be sent.

Long interruptions can exceed remote retention limits. After recovery,
a server may use available outboxes or implementation-specific
synchronization mechanisms to recover missing data. This proposal does
not define such recovery or guarantee its completeness. Signed HTTP
requests authenticate a requester; they do not by themselves authorize
access to private activities or ensure that an outbox retains them.


## Capability discovery

Implementations MAY advertise support for receiving and applying these
notices using [FEP-844e], with `https://w3id.org/fep/f799` as the capability
identifier. For example, an actor's `generator`:

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/844e"
  ],
  "id": "https://peer.example/actor",
  "type": "Application",
  "inbox": "https://peer.example/actor/inbox",
  "outbox": "https://peer.example/actor/outbox",
  "generator": {
    "type": "Application",
    "implements": [{
      "href": "https://w3id.org/fep/f799",
      "name": "Coordinated Inbox Delivery Suspension"
    }]
  }
}
```

Advertising a controller for an inbox or origin does not advertise the
ability to process remote suspension notices. Capability advertising, in
turn, does not grant control of an inbox or origin. Peers MUST NOT require
capability advertising before processing an otherwise valid notice.


## Security and privacy considerations

A forged suspension notice can suppress legitimate federation traffic.
Peers MUST verify the object's or activity's authenticity and the
controller's authority over the declared target inbox or origin. Sharing
an origin with an inbox, controlling a user account on that origin, or
claiming to be an instance actor is insufficient.

Dereferencing actor, inbox, WebFinger, proof, and discovery-link URLs can
expose implementations to server-side request forgery. Implementations MUST
apply their normal federation fetch protections, including restrictions on
private network access, redirects, response sizes, and fetch depth.
Cancellation references must not trigger unbounded chains of fetches.

Peers SHOULD limit accepted notices, revisions, future scheduling horizons,
and queue storage per controller. Local limits on suspension length also
bound the effect of a compromised controller or an operator error.
Implementations SHOULD allow administrators to inspect or override
suspensions.

Suspension schedules can reveal operational information. Operators choosing
public discovery and static hosting expose their schedules beyond the
peers receiving activities. They SHOULD omit peer-specific addressing and
private operational details before signing and publication. The public
activity examples do not require publishing the federation graph.
Publishers MUST NOT strip fields from an already signed object or activity
and reuse its proof. Deployments needing restricted disclosure can apply
access controls to the current object and send notices only to intended
peers rather than publicly advertising them.

Status-page links are informational. They are neither evidence of authority
nor machine-readable recovery signals. Peers MUST NOT require fetching
them to process a notice. Human-readable metadata must be rendered with the same sanitization
and link-handling precautions as other remote Activity Streams content.
Operators should avoid including private contact details.

NodeInfo, administrator contact information, and delivery-rate negotiation
are not required by this proposal. A status page can provide public
operational contacts without copying them into every federated notice.


## Compatibility

Implementations that do not support this proposal continue using their
existing delivery and retry policies. Operators must therefore retain
ordinary HTTP failure handling; notices cannot guarantee silence during
maintenance.

An unsupported `Create` is not guaranteed to disappear without side
effects. A peer might store it, display it, or forward a public activity
without applying the suspension semantics. Publishers SHOULD NOT include
private operational information in a public notice or assume that only
implementations of this proposal will retain it. Actual storage, display,
and forwarding behavior requires implementation-specific testing; this
proposal makes no claim about particular products or versions.

An individual-inbox suspension does not suspend its shared inbox, and a
shared-inbox suspension does not automatically suspend every individual
inbox on the same deployment. Covering all inboxes at an origin requires
an explicit `targetOrigin` notice and independently verified origin control.
Support for Object Integrity Proofs is optional; a peer unable to verify
a statically hosted notice can still use ordinary HTTP retry handling.

In this context, the compact term `status` denotes
`https://w3id.org/fep/f799#status`, not an actor's profile status from
another vocabulary. Implementations using fixed vocabularies MUST
distinguish these expanded properties rather than merge unrelated
short-name mappings. JSON-LD publishers combining vocabularies can use
scoped contexts or distinct aliases when compact terms overlap.


## Open questions

The property names `deliveryController`, `controlledOrigin`, `targetInbox`,
`targetOrigin`, `announcement`, `status`, and `revision` remain provisional.
Notice lifetimes, authority-cache ages, replay-state retention, and queue
limits are intentionally implementation or deployment policies, not values
to standardize in a later revision.

Do deployments need multiple controllers for one shared inbox or origin,
or controller replacement during a maintenance event? This draft allows one
controller per shared inbox or origin and does not define transfer of an
existing notice.

Would additional recovery examples help operators choose resume jitter
and cancellation distribution policies without prescribing common timing
values?


## References

- Christine Lemmer-Webber, Jessica Tallon, Erin Shepherd, Amy Guy, Evan
  Prodromou, [ActivityPub], 2018
- James M. Snell, Evan Prodromou, [Activity Streams 2.0], 2017
- James M. Snell, Evan Prodromou, [Activity Vocabulary], 2017
- S. Bradner, B. Leiba, [Key words for use in RFCs to Indicate Requirement
  Levels][BCP 14], 1997, 2017
- R. Fielding, M. Nottingham, J. Reschke, [HTTP Semantics][RFC 9110], 2022
- A. Backman, J. Richer, M. Sporny, [HTTP Message Signatures][RFC 9421], 2024
- T. Berners-Lee, R. Fielding, L. Masinter, [Uniform Resource Identifier
  (URI): Generic Syntax][RFC 3986], 2005
- A. Barth, [The Web Origin Concept][RFC 6454], 2011
- P. Jones, G. Salgueiro, M. Jones, J. Smarr, [WebFinger], 2013
- M. Nottingham, [Web Linking][RFC 8288], 2017
- S. Kawamura, M. Kawashima, [A Recommendation for IPv6 Address Text
  Representation][RFC 5952], 2010
- J. Klensin, [Internationalized Domain Names for Applications (IDNA):
  Definitions and Document Framework][RFC 5890], 2010
- J. Klensin, [Internationalized Domain Names in Applications (IDNA):
  Protocol][RFC 5891], 2010
- silverpill, [FEP-8b32: Object Integrity Proofs][FEP-8b32], 2022
- Evan Prodromou, [FEP-5711: Inverse Properties for Collections][FEP-5711]
- Steve Bate, [FEP-d556: Server-Level Actor Discovery Using
  WebFinger][FEP-d556], 2024
- silverpill, [FEP-844e: Capability discovery][FEP-844e], 2025

[ActivityPub]: https://www.w3.org/TR/activitypub/
[ActivityPub §7.3]: https://www.w3.org/TR/activitypub/#update-activity-inbox
[ActivityPub §7.11]: https://www.w3.org/TR/activitypub/#undo-activity-inbox
[Activity Streams 2.0]: https://www.w3.org/TR/activitystreams-core/
[Activity Vocabulary]: https://www.w3.org/TR/activitystreams-vocabulary/
[BCP 14]: https://www.rfc-editor.org/info/bcp14
[RFC 9110]: https://www.rfc-editor.org/rfc/rfc9110.html
[RFC 9421]: https://www.rfc-editor.org/rfc/rfc9421.html
[RFC 3986]: https://www.rfc-editor.org/rfc/rfc3986.html
[RFC 6454]: https://www.rfc-editor.org/rfc/rfc6454.html
[RFC 6454 §6.2]: https://www.rfc-editor.org/rfc/rfc6454.html#section-6.2
[WebFinger]: https://www.rfc-editor.org/rfc/rfc7033.html
[RFC 8288]: https://www.rfc-editor.org/rfc/rfc8288.html
[RFC 5952]: https://www.rfc-editor.org/rfc/rfc5952.html
[RFC 5890]: https://www.rfc-editor.org/rfc/rfc5890.html
[RFC 5891]: https://www.rfc-editor.org/rfc/rfc5891.html
[FEP-8b32]: https://w3id.org/fep/8b32
[FEP-5711]: https://w3id.org/fep/5711
[FEP-d556]: https://w3id.org/fep/d556
[FEP-844e]: https://w3id.org/fep/844e

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement
Proposal have waived all copyright and related or neighboring rights to this
work.
