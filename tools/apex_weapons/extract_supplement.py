"""Keep source paths for clips, and collect named camouflage textures."""
from extract_sources import COMMON, FILTER, LIBRARY, run

if __name__ == "__main__":
    # Do not traverse dependencies again: it repeats thousands of PNG conversions.
    # Full paths prevent different skins' identically named clips overwriting.
    run("extract_motion_fullpaths", COMMON, ["-export", "--exporttypes", "arig,aseq,txtr",
        "--exportfilter", FILTER, "--exportdir", str(LIBRARY / "source_paths"),
        "-exportfullpaths", "-exportrigsequences"])
