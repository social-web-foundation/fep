---
slug: "65ca"
authors: Daniel Supernault <danielsupernault@gmail.com>
status: DRAFT
dateReceived: 2026-10-26
discussionsTo: https://socialhub.activitypub.rocks/t/fep-65ca/8952
---
# FEP-65ca: Common Client Configuration

## Summary

Third-party fediverse clients routinely need to know what a server will accept before a user presses "post": how many attachments, which file types and sizes, how long a post, bio or alt text can be, whether usernames can change, and where a user goes to reset their password. Today this information is software-specific, undocumented, hardcoded into clients, or discovered only after a request is rejected.

This proposal defines a discovery endpoint at `/.well-known/activitypub-client-config` that links to a JSON document describing a server's media upload limits, composer limits, account limits, and human-facing account pages, in a software-neutral format.

## Motivation

Clients that support more than one kind of fediverse server currently face a bad set of options:

1. Hardcode limits per server software and version, which breaks whenever an administrator changes a setting.
2. Rely on a software-specific instance API, whose shape reflects one platform's feature set and cannot express things like photo albums, video duration caps, mixed media rules or username rules.
3. Let the user compose a post, upload a file or edit a profile, then surface a rejection error after the work is done.

NodeInfo describes server metadata and usage statistics, and is explicitly not designed for this. This FEP fills that gap with a small, versioned, extensible document focused on the limits a client needs to build a correct composer, uploader and profile editor.

### Scope

Although the endpoint name references ActivityPub, this FEP is not tied to the ActivityPub client-to-server protocol. It describes the server a client is talking to, and is equally useful to clients that use ActivityPub C2S, a Mastodon-compatible API, or a software-specific API.

## Requirements Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119] and [RFC 8174] when, and only when, they appear in all capitals.

## Terminology

- **Server**: the software and host a client authenticates against and submits content to.
- **Client**: any application that lets a user interact with a server, including web, mobile and desktop applications.
- **Discovery document**: the JSON document served at `/.well-known/activitypub-client-config`.
- **Configuration document**: the JSON document linked from the discovery document, defined in this FEP.
- **Limit field**: a member of the configuration document whose value is a numeric bound (for example `max_length` or `max_bytes`).
- **Baseline account**: a standard, newly registered account on the server, with no elevated role or special allowances.

## Discovery

### Discovery document

A server implementing this FEP MUST respond to:

```
GET /.well-known/activitypub-client-config
```

with HTTP status `200` and a `Content-Type` of `application/json`. The body is a JSON object with a single REQUIRED member, `links`, an array of link objects:

```json
{
  "links": [
    {
      "rel": "https://w3id.org/fep/65ca/1.0",
      "href": "https://example.social/api/client-config/1.0"
    }
  ]
}
```

Each link object has two REQUIRED members:

| Member | Type   | Description |
|--------|--------|-------------|
| `rel`  | string | A URI identifying the configuration document version. For version 1.x of this FEP the value is `https://w3id.org/fep/65ca/1.0`. The URI is an identifier and need not be dereferenceable. |
| `href` | string | The absolute `https` URL of the configuration document. |

Requirements:

- The `href` MUST have the same origin as the discovery document request. A client talks to a known API host, and the configuration document describes that host.
- A server MAY list more than one link to advertise multiple major versions. Clients SHOULD use the highest major version they support.
- Clients MUST ignore link objects with a `rel` they do not recognize.
- A server MAY redirect the discovery request to another URL on the same origin. Clients SHOULD NOT follow redirects to a different origin.

### Configuration document

Fetching the `href` MUST return HTTP status `200`, a `Content-Type` of `application/json`, and a body conforming to [Configuration Document](#configuration-document-1).

### HTTP requirements

These requirements apply to both the discovery document and the configuration document.

- **No authentication.** Both documents MUST be retrievable without authentication. A server MUST return the same document to every requester, authenticated or not. This FEP describes limits for a baseline account only.
- **CORS.** Both responses MUST include `Access-Control-Allow-Origin: *` so that browser-based clients on other origins can read them.
- **Caching.** Servers SHOULD send `Cache-Control` with a `max-age` between 3600 and 86400 seconds, and SHOULD send an `ETag` or `Last-Modified` header. Clients SHOULD cache both documents, SHOULD revalidate at least once every 24 hours, and SHOULD refetch the configuration document when the server rejects a request in a way that contradicts the cached configuration.
- **Size.** Clients MAY refuse to process a configuration document larger than 256 KiB.

## Configuration Document

### General rules

#### Versioning

The `version` member is REQUIRED and has the form `"1.<minor>"`. Minor versions only add OPTIONAL members. Clients MUST ignore members they do not recognize, at every level of the document.

#### Absent, null and zero

- **Absent** means the server does not declare this value. Clients SHOULD fall back to their own defaults or behavior.
- **`null`** on a limit field means there is no limit.
- **`0`** on a limit field means the thing is not allowed. For example, `"max_attachments": 0` means posts cannot carry attachments.
- On a boolean field, absent means unknown. Clients SHOULD NOT assume either value.

`null` MUST NOT be used on non-limit fields.

#### Units

All limit fields are integers unless stated otherwise. Sizes are in bytes, durations are in seconds, and dimensions are in pixels. Frame rates are numbers (integer or decimal) in frames per second.

#### Length counting

Every `max_length` and `min_length` field in the document is measured in the unit given by the top-level `length_unit` member, unless a field states otherwise.

| Value         | Counts |
|---------------|--------|
| `code_points` | Unicode scalar values |
| `graphemes`   | Extended grapheme clusters as defined in [UAX #29] |
| `utf16`       | UTF-16 code units |
| `bytes`       | Bytes of the UTF-8 encoding |

If `length_unit` is absent, clients SHOULD assume `code_points`.

Lengths are measured on the text as the client submits it, before server-side processing such as Markdown rendering or link expansion, except where the composer's `url_weight` and `mention_counting` members say otherwise.

#### Advisory nature

The configuration document is advisory. Servers MUST continue to enforce their limits independently, and clients MUST continue to handle rejection errors. A server MAY grant some accounts limits that differ from the baseline account; this FEP does not express those differences.

### Top-level members

| Member         | Type   | Required | Description |
|----------------|--------|----------|-------------|
| `version`      | string | Yes      | Configuration document version, for example `"1.0"`. |
| `software`     | object | No       | `name` (string) and `version` (string) of the server software. Informational only; clients SHOULD NOT branch behavior on it when the information they need is present elsewhere in the document. |
| `length_unit`  | string | No       | Length counting unit. See [Length counting](#length-counting). |
| `media`        | object | No       | Media upload limits. See [Media](#media). |
| `composer`     | object | No       | Post composition limits. See [Composer](#composer). |
| `accounts`     | object | No       | Account and profile limits. See [Accounts](#accounts). |
| `links`        | object | No       | Human-facing web pages. See [Links](#links). |
| `extensions`   | object | No       | Software-specific members. See [Extensions](#extensions). |

## Media

### `media` object

| Member            | Type          | Description |
|-------------------|---------------|-------------|
| `max_attachments` | limit         | Maximum number of attachments on a single post, across all types. |
| `min_attachments` | integer       | Minimum number of attachments on a single post. `0` means text-only posts are allowed. `1` means every post requires media, as on photo-first or video-first platforms. |
| `max_total_bytes` | limit         | Maximum combined size of all attachments on a single post. |
| `types`           | array         | Media type rules. See [Media type rules](#media-type-rules). |
| `alt_text`        | object        | `max_length` (limit) and `required` (boolean). If `required` is `true`, every attachment MUST have alt text for the post to be accepted. |
| `focal_point`     | boolean       | Whether the server accepts a focal point for image attachments. |

### Media type rules

Each entry in `media.types` describes one group of mime types that share limits.

| Member                 | Type             | Required | Description |
|------------------------|------------------|----------|-------------|
| `id`                   | string           | Yes      | Identifier for this rule, unique within `media.types`. Short lowercase names such as `image`, `video`, `audio` or `gif` are RECOMMENDED. |
| `mime_types`           | array of strings | Yes      | Mime types matched by this rule. MUST NOT be empty. |
| `max_attachments`      | limit            | No       | Maximum number of attachments matched by this rule on a single post. |
| `combinable_with`      | array of strings | No       | `id`s of other rules whose attachments may appear on the same post. See [Combining media types](#combining-media-types). |
| `max_bytes`            | limit            | No       | Maximum size of a single file. |
| `max_width`            | limit            | No       | Maximum width. |
| `max_height`           | limit            | No       | Maximum height. |
| `max_pixels`           | limit            | No       | Maximum width multiplied by height. |
| `min_duration_seconds` | integer          | No       | Minimum duration of audio or video. |
| `max_duration_seconds` | limit            | No       | Maximum duration of audio or video. |
| `max_frame_rate`       | number or null   | No       | Maximum frame rate of video or animated images. `null` means no limit. |
| `strips_metadata`      | boolean          | No       | Whether the server removes embedded metadata (for example EXIF, XMP and GPS location) from files of this type before storing or serving them. |
| `transcodes`           | boolean          | No       | Whether the server re-encodes files of this type. Clients MAY skip their own compression when `true`. |

Mime type matching is exact and case-insensitive, and ignores parameters. Wildcards such as `image/*` MUST NOT be used. A mime type MUST NOT appear in more than one rule. Clients SHOULD treat a file whose mime type matches no rule as unsupported.

When a server declares dimension limits, it SHOULD state whether it rejects or downscales oversized files through `transcodes`: a server that downscales SHOULD set `transcodes` to `true`.

### Combining media types

The rules for which attachments may share a post are:

1. Any number of attachments matched by the same rule MAY appear on the same post, up to that rule's `max_attachments` and `media.max_attachments`. Mime types within one rule may be freely mixed (for example a JPEG and a PNG in one album).
2. Attachments matched by two different rules MAY appear on the same post only if each rule lists the other's `id` in `combinable_with`.
3. An absent `combinable_with` is equivalent to an empty array: the rule's attachments cannot share a post with attachments from any other rule.
4. `combinable_with` MUST be symmetric. If rule A lists B but B does not list A, clients MUST treat A and B as not combinable.
5. A rule MUST NOT list its own `id` in `combinable_with`. Combining attachments of the same rule is governed by rule 1.

#### Example: photo albums, standalone video

Any mix of image formats up to 20, or a single video, never both:

```json
"types": [
  {
    "id": "image",
    "mime_types": ["image/jpeg", "image/png", "image/webp", "image/avif"],
    "max_attachments": 20,
    "max_bytes": 15000000,
    "strips_metadata": true
  },
  {
    "id": "video",
    "mime_types": ["video/mp4", "video/webm"],
    "max_attachments": 1,
    "max_bytes": 100000000,
    "max_duration_seconds": 600,
    "strips_metadata": false
  }
]
```

#### Example: mixed carousel

Images and videos may share a post, up to 10 attachments in total:

```json
"max_attachments": 10,
"types": [
  { "id": "image", "mime_types": ["image/jpeg", "image/png"], "combinable_with": ["video"] },
  { "id": "video", "mime_types": ["video/mp4"], "combinable_with": ["image"], "max_duration_seconds": 60 }
]
```

## Composer

### `composer` object

| Member             | Type             | Description |
|--------------------|------------------|-------------|
| `max_length`       | limit            | Maximum length of the post body. |
| `url_weight`       | integer or null  | If an integer, every URL in the post body counts as exactly this many length units, regardless of its actual length. If `null` or absent, URLs are counted literally. |
| `mention_counting` | string           | `full` (default): a mention such as `@alice@example.com` counts in full. `local_part`: only `@alice` counts; the `@domain` part is free. |
| `content_types`    | array of strings | Mime types the server accepts for the post body, for example `text/plain`, `text/markdown`, `text/html`. |
| `content_warning`  | object           | See below. |
| `polls`            | object           | See below. |
| `visibility`       | array of strings | Supported visibility values. See [Visibility values](#visibility-values). |
| `editing`          | object           | See below. |
| `scheduling`       | object           | See below. |
| `quotes`           | object           | `supported` (boolean): whether the server allows quote posts. |
| `max_mentions`     | limit            | Maximum number of mentions in a single post. |
| `max_hashtags`     | limit            | Maximum number of hashtags in a single post. |
| `languages`        | object           | `supported` (array of [BCP 47] tags, or `null` for any language) and `required` (boolean: whether a post MUST declare its language). |

#### `content_warning`

| Member                     | Type    | Description |
|----------------------------|---------|-------------|
| `supported`                | boolean | Whether posts may carry a content warning (summary). |
| `max_length`               | limit   | Maximum length of the content warning. |
| `counts_toward_max_length` | boolean | If `true`, the content warning's length is added to the body's length when checking `composer.max_length`. |

#### `polls`

| Member                   | Type    | Description |
|--------------------------|---------|-------------|
| `supported`              | boolean | Whether posts may include a poll. |
| `min_options`            | integer | Minimum number of options. |
| `max_options`            | limit   | Maximum number of options. |
| `max_option_length`      | limit   | Maximum length of each option. |
| `multiple_choice`        | boolean | Whether polls may allow more than one choice. |
| `min_expiration_seconds` | integer | Shortest allowed poll duration. |
| `max_expiration_seconds` | limit   | Longest allowed poll duration. |

#### `editing`

| Member           | Type    | Description |
|------------------|---------|-------------|
| `supported`      | boolean | Whether published posts may be edited. |
| `window_seconds` | limit   | How long after publishing a post may be edited. |
| `max_edits`      | limit   | Maximum number of edits per post. |

#### `scheduling`

| Member             | Type    | Description |
|--------------------|---------|-------------|
| `supported`        | boolean | Whether posts may be scheduled for future publication. |
| `min_lead_seconds` | integer | Minimum time between scheduling and publication. |
| `max_lead_seconds` | limit   | Maximum time between scheduling and publication. |
| `max_scheduled`    | limit   | Maximum number of pending scheduled posts per account. |

### Visibility values

| Value       | Meaning |
|-------------|---------|
| `public`    | Visible to anyone and eligible for public timelines. |
| `unlisted`  | Visible to anyone, but excluded from public timelines and discovery features. |
| `followers` | Delivered to and visible to the author's followers only. |
| `direct`    | Delivered to and visible to mentioned recipients only. |
| `local`     | Visible only to accounts on the same server, and not federated. |

Software-specific visibility values MUST be absolute URLs.

## Accounts

### `accounts` object

| Member                | Type    | Description |
|-----------------------|---------|-------------|
| `username`            | object  | See [Username rules](#username-rules). |
| `display_name`        | object  | `max_length` (limit). |
| `bio`                 | object  | `max_length` (limit). |
| `fields`              | object  | Profile metadata fields: `max_count` (limit), `name_max_length` (limit), `value_max_length` (limit), `link_verification` (boolean: whether the server verifies links in field values, for example with `rel="me"`). |
| `avatar`              | object  | Image rule: `mime_types` (array), `max_bytes` (limit), `max_width` (limit), `max_height` (limit). |
| `header`              | object  | Image rule, same shape as `avatar`. |
| `max_pinned_posts`    | limit   | Maximum number of pinned posts. |
| `max_featured_tags`   | limit   | Maximum number of featured hashtags on a profile. |
| `storage_quota_bytes` | limit   | Total media storage available to an account. |
| `password`            | object  | `min_length` (integer) and `max_length` (limit). |
| `two_factor`          | object  | `methods`: array of supported second-factor methods. See [Two-factor methods](#two-factor-methods). An empty array means two-factor authentication is not supported. |
| `follow_approval`     | boolean | Whether accounts may require manual approval of new followers. |
| `migration`           | object  | `move_in` (boolean: whether the server accepts accounts moving in from other servers), `move_out` (boolean: whether accounts may move to another server), `max_aliases` (limit: maximum number of account aliases). |

### Username rules

| Member                    | Type             | Description |
|---------------------------|------------------|-------------|
| `min_length`              | integer          | Minimum username length. |
| `max_length`              | limit            | Maximum username length. |
| `pattern`                 | string           | A regular expression a valid username MUST match. See below. |
| `allowed_characters`      | array of strings | A summary of character classes permitted in usernames. See below. |
| `case_insensitive`        | boolean          | If `true`, usernames differing only in letter case identify the same account. |
| `changeable`              | boolean          | Whether a user may change their username after registration. |
| `change_cooldown_seconds` | integer          | Minimum time between username changes. |

Usernames are the local part only, without a leading `@` or a domain.

#### `pattern`

- MUST use [ECMA-262] regular expression syntax and MUST be evaluated with the `u` flag.
- MUST begin with `^` and end with `$`.
- SHOULD avoid constructs with poor portability or performance across engines, including backreferences, lookbehind and nested quantifiers.

#### `allowed_characters`

| Value             | Characters |
|-------------------|------------|
| `lowercase_ascii` | `a` to `z` |
| `uppercase_ascii` | `A` to `Z` |
| `digits`          | `0` to `9` |
| `underscore`      | `_` |
| `period`          | `.` |
| `hyphen`          | `-` |
| `unicode_letters` | Any character with the Unicode `Letter` general category |
| `unicode_digits`  | Any character with the Unicode `Decimal_Number` general category |

#### Using both

`pattern` is authoritative: it captures positional rules (for example "must start with a letter" or "no trailing period") that `allowed_characters` cannot. `allowed_characters` exists for help text ("Letters, numbers and underscores") and for clients that cannot or will not evaluate a regular expression.

When both are present, they MUST be consistent: every character class listed in `allowed_characters` MUST be accepted by `pattern` in at least one position, and `pattern` MUST NOT accept characters outside the listed classes. Clients that can evaluate `pattern` SHOULD use it for validation and use `allowed_characters` for display.

### Two-factor methods

| Value      | Method |
|------------|--------|
| `totp`     | Time-based one-time passwords, [RFC 6238] |
| `webauthn` | [WebAuthn] security keys and passkeys |
| `email`    | One-time codes delivered by email |

Software-specific method values MUST be absolute URLs.

## Links

The `links` object lists web pages intended for humans, not API endpoints. Every member is OPTIONAL. Every value MUST be an absolute `https` URL.

| Member                | Page |
|-----------------------|------|
| `registration`        | Account sign-up |
| `login`               | Web sign-in |
| `password_reset`      | Password reset request |
| `account_settings`    | General account settings |
| `two_factor_settings` | Two-factor authentication setup and management |
| `account_deletion`    | Account deletion |
| `data_export`         | Account data export |
| `about`               | About the server |
| `rules`               | Server rules |
| `terms`               | Terms of service |
| `privacy`             | Privacy policy |
| `support`             | Help or contact page |
| `status`              | Service status page |
| `donate`              | Funding or donation page for the server |

Clients SHOULD open these pages in the user's system browser rather than an embedded web view, so users can verify the address and use their password manager. Pages not listed here MUST be placed under `extensions`.

## Extensions

The `extensions` object holds software-specific configuration. Each key MUST be an absolute URL that identifies the extension and SHOULD dereference to its documentation. Values MAY be any JSON value.

```json
"extensions": {
  "https://pixelfed.org/ns/client-config#collections": {
    "max_collections": 100,
    "max_posts_per_collection": 50
  }
}
```

Clients MUST ignore extension keys they do not recognize. Implementers SHOULD propose broadly useful extensions for inclusion in a future minor version of this FEP rather than relying on extensions indefinitely.

## Non-Goals

This FEP intentionally does not cover:

- Server statistics, software identification and federation capabilities, which belong in NodeInfo.
- Rate limits, which change too often and vary per request to be usefully cached.
- Per-account or per-role limits. This document describes the baseline account only.
- OAuth and authentication endpoint discovery, which belongs in [RFC 8414] authorization server metadata.
- Moderation policies and rule text. The `links` object points to these pages but does not reproduce them.

## Security and Privacy Considerations

- **Public data only.** Both documents are public and identical for every requester. They MUST NOT contain per-user data, secrets or internal infrastructure details.
- **Server enforcement.** A malicious or buggy client can ignore this document entirely, so servers MUST enforce every limit independently.
- **Link safety.** Clients SHOULD show the destination host before opening a link from the `links` object, especially when it differs from the server's host.
- **Regular expressions.** A hostile server could publish a `pattern` designed to cause excessive backtracking. Clients SHOULD bound the time spent evaluating `pattern`, and SHOULD fall back to `allowed_characters` and length checks when evaluation fails or times out.
- **Media metadata.** When a media type rule has `strips_metadata` set to `false` or absent, clients SHOULD inform users that embedded metadata such as GPS location may be published, and SHOULD offer to remove it before upload.
- **Fingerprinting.** Because the documents do not vary by requester and require no authentication, fetching them reveals nothing about the user beyond the fact that a client is interacting with the server.

## IANA Considerations

This FEP requests registration of the following well-known URI in the "Well-Known URIs" registry established by [RFC 8615]:

- **URI suffix:** `activitypub-client-config`
- **Change controller:** The authors of FEP-65ca
- **Specification document:** This FEP
- **Status:** provisional
- **Related information:** None

## Full Example

Discovery document at `https://example.social/.well-known/activitypub-client-config`:

```json
{
  "links": [
    {
      "rel": "https://w3id.org/fep/65ca/1.0",
      "href": "https://example.social/api/client-config/1.0"
    }
  ]
}
```

Configuration document at `https://example.social/api/client-config/1.0`:

```json
{
  "version": "1.0",
  "software": { "name": "examplesoft", "version": "2.4.0" },
  "length_unit": "code_points",
  "media": {
    "max_attachments": 20,
    "min_attachments": 1,
    "max_total_bytes": null,
    "types": [
      {
        "id": "image",
        "mime_types": ["image/jpeg", "image/png", "image/webp", "image/avif"],
        "max_attachments": 20,
        "max_bytes": 15000000,
        "max_pixels": 16777216,
        "strips_metadata": true,
        "transcodes": true
      },
      {
        "id": "video",
        "mime_types": ["video/mp4", "video/webm"],
        "max_attachments": 1,
        "max_bytes": 100000000,
        "max_width": 3840,
        "max_height": 2160,
        "max_duration_seconds": 600,
        "max_frame_rate": 60,
        "strips_metadata": false,
        "transcodes": true
      }
    ],
    "alt_text": { "max_length": 2000, "required": false },
    "focal_point": false
  },
  "composer": {
    "max_length": 2000,
    "url_weight": 23,
    "mention_counting": "local_part",
    "content_types": ["text/plain"],
    "content_warning": {
      "supported": true,
      "max_length": 500,
      "counts_toward_max_length": false
    },
    "polls": {
      "supported": true,
      "min_options": 2,
      "max_options": 4,
      "max_option_length": 50,
      "multiple_choice": true,
      "min_expiration_seconds": 300,
      "max_expiration_seconds": 2629746
    },
    "visibility": ["public", "unlisted", "followers", "direct"],
    "editing": { "supported": true, "window_seconds": 86400, "max_edits": null },
    "scheduling": { "supported": false },
    "quotes": { "supported": true },
    "max_mentions": 5,
    "max_hashtags": 30,
    "languages": { "supported": null, "required": false }
  },
  "accounts": {
    "username": {
      "min_length": 2,
      "max_length": 30,
      "pattern": "^[a-zA-Z0-9_](?:[a-zA-Z0-9_.]*[a-zA-Z0-9_])?$",
      "allowed_characters": ["lowercase_ascii", "uppercase_ascii", "digits", "underscore", "period"],
      "case_insensitive": true,
      "changeable": true,
      "change_cooldown_seconds": 2592000
    },
    "display_name": { "max_length": 64 },
    "bio": { "max_length": 500 },
    "fields": {
      "max_count": 4,
      "name_max_length": 255,
      "value_max_length": 255,
      "link_verification": true
    },
    "avatar": {
      "mime_types": ["image/jpeg", "image/png", "image/webp"],
      "max_bytes": 2000000,
      "max_width": 1000,
      "max_height": 1000
    },
    "header": {
      "mime_types": ["image/jpeg", "image/png", "image/webp"],
      "max_bytes": 5000000
    },
    "max_pinned_posts": 3,
    "max_featured_tags": 10,
    "storage_quota_bytes": 1073741824,
    "password": { "min_length": 12, "max_length": 128 },
    "two_factor": { "methods": ["totp", "webauthn"] },
    "follow_approval": true,
    "migration": { "move_in": true, "move_out": true, "max_aliases": 5 }
  },
  "links": {
    "registration": "https://example.social/register",
    "login": "https://example.social/login",
    "password_reset": "https://example.social/password/reset",
    "account_settings": "https://example.social/settings",
    "two_factor_settings": "https://example.social/settings/security",
    "account_deletion": "https://example.social/settings/delete",
    "data_export": "https://example.social/settings/export",
    "about": "https://example.social/about",
    "rules": "https://example.social/rules",
    "terms": "https://example.social/terms",
    "privacy": "https://example.social/privacy",
    "support": "https://example.social/help",
    "status": "https://status.example.social",
    "donate": "https://example.social/donate"
  },
  "extensions": {
    "https://examplesoft.org/ns/client-config#collections": {
      "max_collections": 100
    }
  }
}
```

## JSON Schema

Non-normative [JSON Schema] files are published alongside this FEP: `discovery.schema.json` for the discovery document, and `client-config.schema.json` for the configuration document. Where a schema and this document disagree, this document is authoritative.

## Implementations

- [Loops](https://joinloops.org)

## References

- [RFC 2119] S. Bradner, Key words for use in RFCs to Indicate Requirement Levels, 1997
- [RFC 8174] B. Leiba, Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words, 2017
- [RFC 8615] M. Nottingham, Well-Known Uniform Resource Identifiers (URIs), 2019
- [RFC 8414] M. Jones, N. Sakimura, J. Bradley, OAuth 2.0 Authorization Server Metadata, 2018
- [RFC 6238] D. M'Raihi et al., TOTP: Time-Based One-Time Password Algorithm, 2011
- [WebAuthn] W3C, Web Authentication: An API for accessing Public Key Credentials
- [ECMA-262] Ecma International, ECMAScript Language Specification
- [UAX #29] Unicode Standard Annex #29, Unicode Text Segmentation
- [BCP 47] A. Phillips, M. Davis, Tags for Identifying Languages
- [NodeInfo] NodeInfo protocol, https://nodeinfo.diaspora.software/
- [ActivityPub] C. Webber et al., ActivityPub, W3C Recommendation, 2018
- [JSON Schema] JSON Schema: A Media Type for Describing JSON Documents, draft 2020-12

[RFC 2119]: https://tools.ietf.org/html/rfc2119
[RFC 8174]: https://tools.ietf.org/html/rfc8174
[RFC 8615]: https://tools.ietf.org/html/rfc8615
[RFC 8414]: https://tools.ietf.org/html/rfc8414
[RFC 6238]: https://tools.ietf.org/html/rfc6238
[WebAuthn]: https://www.w3.org/TR/webauthn/
[ECMA-262]: https://tc39.es/ecma262/
[UAX #29]: https://www.unicode.org/reports/tr29/
[BCP 47]: https://www.rfc-editor.org/info/bcp47
[NodeInfo]: https://nodeinfo.diaspora.software/
[ActivityPub]: https://www.w3.org/TR/activitypub/
[JSON Schema]: https://json-schema.org/draft/2020-12/json-schema-core

## Copyright

CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

To the extent possible under law, the authors of this Fediverse Enhancement Proposal have waived all copyright and related or neighboring rights to this work.