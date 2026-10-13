# The Art Atlas: every image the map ships, browsable

**Live page:** https://claude.ai/artifact/4asJNWDJnvJYrivKW89YfE ("Fallen Cybercity Art Atlas", private to the user)

User, 2026-10-04: *"create an easily navigable artifact of the current art and keep it updated so I
can always easily browse current art in game."*

The page shows every image the zone packs, resolved through its GDT to the source file. It also
shows the vendored and stock images we hold no source for, the PNGs on disk that no zone line
packs, and generated art still in production (`art/generated/<pack>/`). Each image has
filters, search, its usage in code, its briefs, its compression, and a change log of what moved
at every rebuild.

## Keep it current: after ANY art change

Do this after landing, replacing or retiring images, and after a generator writes new art to
`art/generated/`.

```
python tools/art_gallery/build_gallery.py
```

It takes about 50 s. It writes `tmp/art_gallery/site/` (gitignored) and appends to the tracked
change log `art/gallery/history.json`. Then republish to the SAME URL with the Artifact tool:

- `action` publish
- `file_path` `tmp/art_gallery/site/index.html`
- `url` the link above. Omit it only in the session that first published it, which can
  republish by file path. Read the artifact first when a new session updates it.
- `files` the JSON object in `tmp/art_gallery/site/publish_files.json`, verbatim. It maps every
  atlas, and sets `null` for any atlas an earlier build published that this one no longer writes.

`--dry` rebuilds without touching the change log (for a look that is not a real update).

## How it is built

- Thumbnails (longest side 240) and previews (720) are packed into WebP sprite atlases
  (`a/t_NN.webp`, `a/p_NN.webp`). The artifact allows 255 files per version, and the map has
  more than 1,000 images.
- The manifest is inlined into `index.html`, so the page needs no fetch.
- The headings use the map's own typeface (`fonts/tod_tower1.ttf`, embedded).
- Categories are the ordered rules in `CATEGORIES` (first match wins). Add a rule when a new
  family of images appears, or it lands in "Other".
