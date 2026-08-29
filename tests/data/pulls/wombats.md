## Description

Adds the scat classifier, the species filter it needs, and a fix to the export that dropped the
last row. Tested against the reference set in `tests/fixtures/scat`.

## User-Facing Changes

<!-- releasenote:start -->

### Scat photos are classified for you

Wombat droppings come out cube shaped, which is why the classifier can pick them out of a photo
without you tagging the species first.

### Filter sightings by species

The sightings list takes a species filter:

- one species, or several at once
- the filter survives a reload
- clearing it puts every sighting back on the map

### Exports keep the last sighting

An export used to stop one row short of the end. It no longer does.

<!-- releasenote:end -->

## Anything Else You'd Like to Mention

<!-- Open word -->
