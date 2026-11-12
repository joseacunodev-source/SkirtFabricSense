# Interface motion — October 22, 2026

The user requested improved animations. Station-v6/research-v11 adds short transitions to the existing interface; station-v5 is the rollback. All model/data and capture timing contracts are unchanged.

- Page heading/panels enter once over 280–340 ms, with a 65 ms panel offset.
- Buttons/selects use 150 ms hover/press transitions; the fabric switch uses 180 ms thumb/track transitions.
- A connecting indicator pulses only while the camera connection is pending. The live feed has a 200 ms entrance; stopping still hides it immediately.
- Changed supported result labels reveal over 180 ms. Repeated labels do not replay the effect across frames, and numeric scores do not animate per frame.
- Clearing/invalidation cancels value effects and replaces text synchronously. Motion never delays expiry, cancellation, camera failure or result removal.
- The reduced-motion preference disables CSS entrances/transitions and optional value effects. Changes to that preference cancel active value effects. Missing/failing animation APIs preserve ordinary rendering.

The existing 18 lifecycle scenarios and 21 score cases pass alongside six new motion cases. A separate agent reviewed and reran them. Browser inspection observes the expected 280 ms heading entrance,150 ms control transitions and180 ms switch thumb transition; the fabric switch still behaves correctly and its saved Off setting was restored. The camera remained off. No physical-camera or Pi performance was measured.

The new package was inventory-verified and the running server serves its exact HTML. Backend/model bytes are identical to station-v5, whose 12 saved-frame HTTP jobs remain earlier evidence; no new inference accuracy or repeated HTTP model run is claimed for this presentation-only update. No dependencies were installed.

The owned loopback preview remains at http://127.0.0.1:8766/. Check its current process/session in the [continuation pointer](../records/continuation/latest.json) before restarting it. [Package instructions](STATION_PACKAGE.md).
