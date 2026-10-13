"""Rebuild the Talon / R.A.P.S. / Cerberus materials from the real T7 texture set.

Read-only inputs:
  * T7 Assets V2.8 (the pack's own material GDTs + its _images PNGs), extracted
    on demand from ~/Downloads/T7 Assets V2.8.rar into tmp/partner_assets/.
  * the private tools database (stock image definitions / stock image files,
    including the read-only model_export junctions such as black_ops_3/).
Outputs (all map-owned, written by install_assets.py):
  * mtl_tod_ptn_* material blocks cloned field-for-field from the original
    definitions, image references renamed,
  * i_tod_ptn_* image blocks + PNGs in model_export/tod_partner/_images/
    (capped at 1024, dimensions multiples of 4).
Stock images that already exist in the tools database WITH their source file
are referenced by their stock name (never copied, never redefined).
Maps that exist in NO readable source (W2A 2026-10-05: the Talon wing set, 34
Cerberus maps, the Civil Protector's shell / arm / chassis / gold-finish maps)
are AUTHORED by tools/companion_maps/compose.py under their original names in
art/companion_maps/authored/; the resolver finds them there, after the pack and
before the stock tools, and takes each one's semantic from that folder's
_authored.json (an authored spec map is a specularMap whatever its suffix says).

Nothing here writes to the tools root, the pack or the donor meshes.
"""
from pathlib import Path
import json, re, sqlite3, subprocess, shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MT = Path('C:/BO3Tools/TOD2Cybercity')
RAR = Path.home()/'Downloads/T7 Assets V2.8.rar'
SEVENZIP = Path('C:/Program Files/7-Zip/7z.exe')
PACK = ROOT/'tmp/partner_assets/T7 Assets V2.8'
STAGE = Path.home()/'Downloads/_t7stage/T7 Assets V2.8'
IMG_OUT = ROOT/'model_export/tod_partner/_images'
AUTHORED = ROOT/'art/companion_maps/authored'
IMG_CAP = 1024
BS = '\\\\'   # a GDT path separator as written in the file

def norm(p): return re.sub(r'[\\/]+', '/', p)

def authored_index():
    """original image name -> {semantic, coreSemantic, compressionMethod, ...} for every authored map."""
    rec = AUTHORED/'_authored.json'
    return json.loads(rec.read_text(encoding='utf-8'))['images'] if rec.exists() else {}

# ---------------------------------------------------------------- pack GDTs
_HDR = re.compile(r'^\s*"([^"]+)"\s*(\(|\[)\s*"([^"]+)"\s*(\)|\])\s*$')
_KV = re.compile(r'^\s*"([^"]*)"\s*"(.*)"\s*$')

def extract(patterns):
    """Pull files out of the pack by wildcard (7-Zip, recursive)."""
    if not patterns: return
    lst = ROOT/'tmp/partner_assets/_extract.txt'
    lst.parent.mkdir(parents=True, exist_ok=True)
    lst.write_text('\n'.join(patterns)+'\n', encoding='utf-8')
    subprocess.run([str(SEVENZIP), 'x', '-y', '-r', str(RAR), '@'+str(lst),
                    '-o'+str(PACK.parent)], check=True, stdout=subprocess.DEVNULL)

def pack_index():
    src = PACK/'source_data/_midgetblaster'
    if not src.exists() or not any(src.glob('*.gdt')):
        extract(['T7 Assets V2.8\\source_data\\_midgetblaster\\*.gdt'])
    idx = {}
    for f in sorted(src.glob('*.gdt')):
        cur = None
        for line in f.read_text(encoding='utf-8', errors='replace').splitlines():
            m = _HDR.match(line)
            if m:
                cur = {'_file': f.name, '_kind': m.group(3) if m.group(2) == '(' else None}
                idx.setdefault(m.group(1), cur)
                continue
            if cur is not None:
                m = _KV.match(line)
                if m: cur[m.group(1)] = m.group(2)
    return idx

# ---------------------------------------------------------------- resolver
IMG_KEY = re.compile(r'(Map\d*|heatmap|flickerLookupMap)$')
# Semantic -> (coreSemantic, compressionMethod), from stock usage in these material types.
CORE = {'diffuseMap': ('sRGB3chAlpha', 'compressed high color'),
        'normalMap': ('Normal', 'compressed'),
        'occlusionMap': ('Linear1ch', 'compressed'),
        'revealMap': ('Linear1ch', 'compressed'),
        'glossMap': ('Linear1ch', 'compressed'),
        'specularMask': ('Linear1ch', 'compressed'),
        'specularMap': ('sRGB3ch', 'compressed'),
        'thicknessMap': ('Linear1ch', 'compressed')}
SUFFIX_SEMANTIC = [('_nml', 'normalMap'), ('_n', 'normalMap'), ('_o', 'occlusionMap'),
                   ('_r', 'revealMap'), ('_m', 'revealMap'), ('_g', 'glossMap'),
                   ('_s', 'specularMask'), ('_e', 'diffuseMap'), ('_c', 'diffuseMap')]

class Resolver:
    def __init__(self, pack):
        self.pack = pack
        self.db = sqlite3.connect((MT/'gdtdb/gdt.db').as_uri()+'?mode=ro', uri=True)
        self.db.execute('pragma writable_schema=ON')
        self.db.row_factory = sqlite3.Row
        self.images = {}      # our image name -> block fields
        self.sources = {}     # our image name -> source path (evidence)
        self.stock_used = set()
        self.missing = {}     # original image -> [material, field]
        self.subst_used = {}
        self.authored = authored_index()

    def stock(self, kind, name):
        r = self.db.execute('select * from '+kind+' where _name=?', (name,)).fetchone()
        return dict(r) if r else None

    def stock_ok(self, name):
        d = self.stock('image', name)
        return bool(d and d.get('baseImage') and (MT/norm(d['baseImage'])).exists())

    def find_file(self, name):
        """The real texture for a pack image name: pack PNG, else a stock-tools file."""
        d = self.pack.get(name)
        rels = []
        if d and d.get('_kind') == 'image.gdf' and d.get('baseImage'):
            rels.append(norm(d['baseImage']))
        for rel in rels:
            for base in (PACK, STAGE):
                if (base/rel).exists(): return base/rel
        # The pack stores every image as _images/<name>.png somewhere under model_export.
        for base in (PACK, STAGE):
            hits = sorted((base/'model_export').rglob(name+'.png')) if (base/'model_export').exists() else []
            if hits: return hits[0]
        # Authored (no source anywhere; tools/companion_maps/compose.py, under the original name)
        if name in self.authored and (AUTHORED/(name+'.png')).exists():
            return AUTHORED/(name+'.png')
        # Stock tools (read-only junctions): <anything>/_images/<name>.tif(f)
        for ext in ('tiff', 'tif', 'png'):
            hits = sorted((MT/'model_export/black_ops_3').glob('*/_images/'+name+'.'+ext))
            if hits: return hits[0]
        return None

    def prefetch(self, names):
        """Extract every pack PNG we might need in one 7-Zip pass."""
        want = [n for n in sorted(set(names)) if n and not n.startswith('$')
                and not self.stock_ok(n) and self.find_file(n) is None]
        extract([n+'.png' for n in want])   # 7-Zip -r matches the file name in any folder

    def semantic_of(self, name, field, mtype):
        if name in self.authored: return self.authored[name]['semantic']
        d = self.pack.get(name)
        if d and d.get('semantic'): return d['semantic']
        for suf, sem in SUFFIX_SEMANTIC:
            if name.endswith(suf) or name.endswith(suf+'_tile'): return sem
        return 'diffuseMap'

    def image(self, name, material, field, mtype):
        """Return the name to put in the material, or None when no real texture exists."""
        if not name or name.startswith('$'): return name
        if self.stock_ok(name):
            self.stock_used.add(name); return name
        src = self.find_file(name)
        if src is None:
            self.missing.setdefault(name, []).append(material+'.'+field)
            return None
        ours = 'i_tod_ptn_'+(name[2:] if name.startswith('i_') else name)
        assert len(ours) < 64, ours
        if ours not in self.images:
            sem = self.semantic_of(name, field, mtype)
            core, comp = CORE.get(sem, CORE['diffuseMap'])
            if name in self.authored:
                core, comp = self.authored[name]['coreSemantic'], self.authored[name]['compressionMethod']
            pd = self.pack.get(name) or {}
            if pd.get('compressionMethod') and sem == 'diffuseMap': comp = pd['compressionMethod']
            if comp.startswith('compressed') and sem == 'diffuseMap' and comp not in ('compressed high color', 'compressed no alpha'):
                comp = 'compressed high color'
            IMG_OUT.mkdir(parents=True, exist_ok=True)
            im = Image.open(src)
            im.load()
            w, h = im.size
            f = min(1.0, IMG_CAP/max(w, h))
            if f < 1.0:
                im = im.resize((max(4, int(w*f)), max(4, int(h*f))), Image.LANCZOS)
            w, h = im.size
            assert w % 4 == 0 and h % 4 == 0, (name, im.size)
            if im.mode not in ('RGB', 'RGBA'):
                im = im.convert('RGBA' if 'A' in im.mode else 'RGB')
            dest = IMG_OUT/(ours+'.png')
            im.save(dest, optimize=True)
            self.images[ours] = {'baseImage': 'model_export'+BS+'tod_partner'+BS+'_images'+BS+ours+'.png',
                                 'imageType': 'Texture', 'type': 'image', 'semantic': sem,
                                 'streamable': 1, 'compressionMethod': comp, 'coreSemantic': core}
            try: shown = str(src.relative_to(PACK.parent))
            except ValueError:
                try: shown = str(src.relative_to(ROOT))
                except ValueError: shown = str(src)
            self.sources[ours] = {'from': norm(shown), 'original': name, 'size': list(im.size)}
        return ours

    def material(self, src_name, fields, new_name, overrides=None, subst=None):
        """Clone a definition, point every image at a real texture (or leave it unset)."""
        out = {k: v for k, v in fields.items() if not k.startswith('_') and k != 'PK_id'
               and v is not None and not isinstance(v, bytes)}
        for k, v in (overrides or {}).items(): out[k] = v
        mtype = out.get('materialType', '')
        for k, v in list(out.items()):
            if not isinstance(v, str) or not v or not IMG_KEY.search(k): continue
            if subst and v in subst:
                self.subst_used[v] = subst[v]; v = subst[v]
            r = self.image(v, new_name+' ('+src_name+')', k, mtype)
            out[k] = r if r is not None else ''
        return out

def stock_material(res, name):
    d = res.stock('material', name)
    if not d: return None
    return {k: v for k, v in d.items() if not k.startswith('_') and k != 'PK_id' and v not in (None, '')}
