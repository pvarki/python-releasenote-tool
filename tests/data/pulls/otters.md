## Description

The pairing logic dropped a raft whenever one of the pair surfaced out of range. Reconciliation
moved into `raft.py` and is covered by the drift cases we saw in staging.

## User-Facing Changes

<!--
Used in the release notes, write from the user's point of view.
One ### per change, a screenshot can be included.
No user-visible changes? Remove this section.
-->
<!-- releasenote:start -->

### Otter pairs stay linked overnight

Sea otters hold hands while they sleep so they do not drift apart, and the map keeps a resting
pair on one marker instead of splitting them the moment one of them surfaces.

<!-- releasenote:end -->

## Anything Else You'd Like to Mention

The drift threshold is still a constant, worth a setting later.
