## v1.2.0 (2026-08-29)

### Colony size estimated from one photo ([#131](https://example.com/example/test/pull/131))

An emperor penguin colony huddles tightly enough that counting heads is hopeless, so a photo of
one gives you an estimate of its size instead.

### Migration routes on the map ([#129](https://example.com/example/test/pull/129))

Arctic terns fly from pole to pole every year, the longest migration of any animal, and the map
draws that whole route as one line now.

### Night mode for field work ([#127](https://example.com/example/test/pull/127))

Tarsiers have eyes as large as their brains because they hunt in the dark. The field view dims
the same way, so nobody out at night is blinded by their own screen.

### Tracker settings moved into the sidebar ([#126](https://example.com/example/test/pull/126))

Everything that used to sit behind the gear icon is in the sidebar.

#### On the web

The sidebar stays open, so the settings sit next to whatever you are editing.

#### On mobile

The sidebar slides over the map and closes once you pick a setting.

### Plumage colour on the sighting card ([#124](https://example.com/example/test/pull/124))

Flamingos are born grey and take their pink from the brine shrimp they eat, so the card shows
where a bird sits on that scale instead of one flat colour for the whole species.

![The sighting card showing the plumage scale](https://example.com/attachments/plumage-scale.png)

### Tusk measurements on the sighting form ([#123](https://example.com/example/test/pull/123))

A narwhal tusk is really a tooth grown out through the animal's lip, so the form records it
apart from body length:

- length in centimetres, spiral direction optional
- left tusk, right tusk, or both for the rare double
- whatever you enter follows the sighting into the export

### Scat photos are classified for you ([#121](https://example.com/example/test/pull/121))

Wombat droppings come out cube shaped, which is why the classifier can pick them out of a photo
without you tagging the species first.

### Filter sightings by species ([#121](https://example.com/example/test/pull/121))

The sightings list takes a species filter:

- one species, or several at once
- the filter survives a reload
- clearing it puts every sighting back on the map

### Exports keep the last sighting ([#121](https://example.com/example/test/pull/121))

An export used to stop one row short of the end. It no longer does.

### Hive health at a glance ([#120](https://example.com/example/test/pull/120))

- brood, stores and temper sit on one line per hive
- a queenless hive is called out before you open it
- honeybees can recognise human faces, the card settles for recognising the hive number

### Inspection history on the hive card ([#120](https://example.com/example/test/pull/120))

- the last three inspections, newest first
- each one keeps whatever notes you typed in the field
- older inspections are still in the export

### Otter pairs stay linked overnight ([#118](https://example.com/example/test/pull/118))

Sea otters hold hands while they sleep so they do not drift apart, and the map keeps a resting
pair on one marker instead of splitting them the moment one of them surfaces.
