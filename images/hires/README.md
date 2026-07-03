# Where to put your high-res photos

**Put every high-res photo somewhere under this folder (`images/hires/`),
grouped into one subfolder per source (book).** Filenames inside don't matter —
we track everything by folder + an intake manifest, not by filename.

```
images/hires/
  wendell-berry__selected-poems/     <- one folder per book you photographed
    IMG_4821.jpg
    IMG_4822.jpg
  mary-oliver__devotions/
    photo1.heic
    photo2.heic
  unknown-source-01/                 <- don't know the book? use a placeholder
    IMG_5003.jpg                        we'll fill in title/author later by eye
```

## Rules of thumb

- **One folder per book/source.** Name it however you like; a readable slug
  like `author__book-title` is ideal but not required. This folder is how we
  record provenance for poems whose title/author aren't visible in the photo.
- **Don't know where it came from?** Make an `unknown-source-NN/` folder and
  drop it there. We'll transcribe it anyway and you can identify it later.
- **A poem that spans multiple pages = multiple photos.** Just put all the
  photos in the source folder. The intake step (Stage 1) groups several images
  into a single poem, in reading order.
- **High-res only here.** Low-res copies go in `images/lores/` (gitignored) and
  are never used for transcription.

Nothing here is read directly by name — `scripts/intake.py` scans these folders
and helps you group images into poems, producing one YAML per poem in `poems/`.
