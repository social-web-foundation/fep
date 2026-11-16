---
slug: "c0a8"
authors: [Reese Armstrong <me@reeseric.ci>]
status: DRAFT
discussionsTo: https://socialhub.activitypub.rocks/t/fep-c0a8-queryable-governable-event-stores-for-moderators/8999
dateReceived: 2026-11-16
trackingIssue: https://codeberg.org/fediverse/fep/issues/991
---
# FEP-c0a8: Queryable Governable Event Stores for Moderators

## Summary

This FEP describes how instances are to expose a queryable Online Analytical Processing (OLAP) store of governable events to moderators via Apache Arrow Flight SQL (over gRPC-Web) and Substrait, enabling them to identify events requiring intervention or review actions automatically taken by instance policy. Specific actions and enforcement mechanisms are deliberately out of scope for this proposal.

## Requirements Notation and Conventions

 The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [BCP 14] \[[RFC2119][RFC2119]\] \[[RFC8174][RFC8174]\] when, and only when, they appear in all capitals, as shown here.

## Terminology

Governable events: Activity Streams and associated instance policy metadata recorded for moderator review and/or auditing

Moderators: Delegated actors authorized to query the governable event store, as determined by the instance’s access control policy

## Endpoints

Instances SHALL provide a queryable endpoint for accessing the governable event store to moderators at a sensible location to be determined by the instance. 

Instances SHALL provide for the discovery of this endpoint in the `endpoints` object under the key `governableEvents` on an authorized moderator’s actor object. 

Instances MAY limit the providing of this endpoint to requests with authentication provided, or MAY utilize a different endpoint URL for each moderator, as to obscure discovery from the public. Utilization of these obscurity mechanisms SHALL NOT be sufficient authentication.

### Example

```json
{
  "@context": [
    "https://www.w3.org/ns/activitystreams",
    "https://w3id.org/fep/c0a8",
    {
      "@language": "ja"
    }
  ],
  "type": "Person",
  "id": "https://kenzoishii.example.com/",
  "following": "https://kenzoishii.example.com/following.json",
  "followers": "https://kenzoishii.example.com/followers.json",
  "liked": "https://kenzoishii.example.com/liked.json",
  "inbox": "https://kenzoishii.example.com/inbox.json",
  "outbox": "https://kenzoishii.example.com/feed.json",
  "preferredUsername": "kenzoishii",
  "name": "石井健蔵",
  "summary": "この方はただの例です",
  "icon": [
    "https://kenzoishii.example.com/image/165987aklre4"
  ],
  "endpoints": {
      "governableEvents": "https://kenzoishii.example.com/governableEvents"
  }
}
```

*Modified from Example 9 in the ActivityPub specification.*

## Protocol

[Apache Arrow Flight SQL], building on the [Apache Arrow Flight RPC] framework, SHALL be the sole protocol utilized by the advertised queryable endpoint. The queryable endpoint SHALL support [gRPC-Web] and SHOULD support [gRPC].

## Authentication

Every RPC request to the queryable endpoint SHALL be authenticated via the HTTP `Authorization` header using an OAuth 2.0 Bearer Token [RFC6750] issued for the moderator's ActivityPub Client-to-Server session. An instance MAY require a specific OAuth 2.0 scope [RFC6749] or Rich Authorization Request [RFC9396], as defined in a future vocabulary.

Requests lacking valid credentials SHALL be rejected with RPC status `UNAUTHENTICATED`. Requests authenticated as an actor without moderator authorization or lacking a required scope SHALL be rejected with RPC status `UNAUTHORIZED`.

## Queries

Queries SHALL be a [Substrait] query plan submitted via `CommandStatementSubstraitPlan` (`GetFlightInfoSubstraitPlan` and `DoGet`). Queryable endpoints SHOULD reject raw SQL queries (e.g. `CommandStatementQuery`) with RPC status `UNIMPLEMENTED`.

Instances MAY enforce operational limits on query execution.

### Write rejection

The governable event store SHALL be immutable by any external actor other than the instance internally, and as such, the queryable endpoint SHALL reject all RPC mutation calls with RPC status `UNIMPLEMENTED`.

## Events

The governable event store SHALL contain a `governable_events` table consisting of the following columns, with each row reflecting an Activity Stream activity observed by the instance:

| Name | Type | Description |
|:--|:--|:--|
| `observed_at` | Timestamp(Millisecond, "UTC") | Time activity was observed |
| `direction` | `'inbound' \| 'outbound' \| 'local'` | Activity boundary. Inbound/outbound for Server-to-Server, Local for Client-to-Server. |
| `activity_json` | Utf8 (arrow.json) | Full Activity Stream |
| `source_ip?` | String | Source IP address |
| `verdicts?` | `List<Verdict>` | List of automated rule outcomes for a given activity |

*? means a column is nullable for a given row*

It is RECOMMENDED that instances include all activities transmitted to the server in the store, including Client-to-Server and Server-to-Server communication.

### Verdict

The `Verdict` struct SHALL contain the following fields, based on the [Open Digital Rights Language (ODRL)][ODRL] vocabulary:

| Name | Type | Description |
|:--|:--|:--|
| `rule` | String | IRI of odrl:Rule that was triggered |
| `action` | String | IRI of odrl:Action that was taken |
| `target` | String | IRI of action target |
| `applied_at`  | Timestamp(Millisecond, "UTC") | Time action was taken |


## References

- Internet Engineering Task Force, [BCP 14], 2023
- Scott Bradner, [RFC2119: Key words for use in RFCs to Indicate Requirement Levels][RFC2119], 1997
- Barry Leiba, [RFC8174: Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words][RFC8174], 2017
- Christine Lemmer-Webber, Jessica Tallon, Erin Shepherd, Amy Guy, Evan Prodromou, [ActivityPub], 2018
- James M Snell, Evan Prodromou, [Activity Streams], 2017
- Apache Foundation, [Apache Arrow Flight SQL], 2022
- Apache Foundation, [Apache Arrow Flight RPC], 2019
- gRPC, [gRPC over HTTP/2][gRPC], 2015
- gRPC, [gRPC Web][gRPC-Web], 2016
- Michael Jones, Dick Hardt, [RFC6750: OAuth 2.0 Bearer Token][RFC6750], 2012 
- Dick Hardt, [RFC6749: The OAuth 2.0 Authorization Framework][RFC6749], 2012
- Torsten Lodderstedt, Justin Richer, Brian Campbell, [RFC9396: OAuth 2.0 Rich Authorization Requests][RFC9396], 2023
- Substrait, [Substrait: Cross-Language Serialization for Relational Algebra][Substrait], 2021
- Renato Iannella, Serena Villata, [ODRL Information Model 2.2][ODRL], 2018

[BCP 14]: https://datatracker.ietf.org/doc/html/bcp14
[RFC2119]: https://datatracker.ietf.org/doc/html/rfc2119
[RFC8174]: https://datatracker.ietf.org/doc/html/rfc8174
[ActivityPub]: https://www.w3.org/TR/activitypub/
[Activity Streams]: https://www.w3.org/TR/activitystreams-core/
[Apache Arrow Flight SQL]: https://arrow.apache.org/docs/format/FlightSql.html
[Apache Arrow Flight RPC]: https://arrow.apache.org/docs/format/Flight.html
[gRPC]: https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md
[gRPC-Web]: https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-WEB.md
[RFC6750]: https://datatracker.ietf.org/doc/html/rfc6750/
[RFC6749]: https://datatracker.ietf.org/doc/html/rfc6749/
[RFC9396]: https://datatracker.ietf.org/doc/html/rfc9396
[Substrait]: https://substrait.io/spec/specification/
[ODRL]: https://www.w3.org/TR/odrl-model/

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.
