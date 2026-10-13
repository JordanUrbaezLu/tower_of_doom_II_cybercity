"""Install the canonical rendered Dealer photograph unchanged as static screen content."""
from pathlib import Path
import hashlib,json,shutil,struct
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'art/dealer_presence/dealer_surveillance_1024.png'
DEST=ROOT/'model_export/tod_dealer_presence/_images/i_tod_dealer_surveillance.png'
ART=ROOT/'art/dealer_presence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
portrait=json.loads((ART/'portrait.json').read_text())
assert portrait['image_sha256']==sha(SOURCE)
assert portrait['author_script_sha256']==sha(Path(__file__).with_name('author_portrait.py'))
assert all(sha(ROOT/p)==h for p,h in portrait['sources'].items()),'Canonical Dealer source changed; re-author portrait'
assert struct.unpack('>II',SOURCE.read_bytes()[16:24])==(1024,1024),'Native mipped screen requires 1024 POT portrait'
from process_guard import check
check()
DEST.parent.mkdir(parents=True,exist_ok=True);ART.mkdir(parents=True,exist_ok=True)
shutil.copyfile(SOURCE,DEST)
# The photograph is screen content, so its authored lighting stays in the image.
# Only this screen has constant low emission; the shared metal frame stays unlit.
gdt='''{
 "i_tod_dealer_surveillance" ( "image.gdf" )
 {
  "baseImage" "model_export\\tod_dealer_presence\\_images\\i_tod_dealer_surveillance.png"
  "semantic" "diffuseMap"
  "imageType" "Texture"
  "coreSemantic" "sRGB3chAlpha"
  "streamable" "1"
  "noMipMaps" "0"
  "noPicMip" "0"
  "compressionMethod" "compressed high color"
  "type" "image"
 }
 "mtl_tod_dealer_surveillance" ( "material.gdf" )
 {
  "template" "material.template"
  "materialCategory" "Geometry"
  "materialType" "lit_emissive"
  "surfaceType" "glass"
  "colorMap" "i_tod_dealer_surveillance"
  "colorTint" ".4 .4 .4 1"
  "colorMap00" "i_tod_dealer_surveillance"
  "colorTint1" "1 1 1 1"
  "scaleRGB" ".65"
  "emissiveIncompetence" "1"
  "emissiveFalloff" "0"
  "specAmount" ".12"
  "reflectionProbeAmount" ".08"
  "glossRangeMin" "0"
  "glossRangeMax" "5"
  "usage" "wall"
 }
}
'''
GDT=ROOT/'source_data/tod_dealer_presence.gdt';GDT.write_text(gdt,encoding='utf-8')
receipt={'schema':1,'source':SOURCE.relative_to(ROOT).as_posix(),'source_sha256':sha(SOURCE),
 'installed_image':DEST.relative_to(ROOT).as_posix(),'installed_image_sha256':sha(DEST),
 'gdt':GDT.relative_to(ROOT).as_posix(),'gdt_sha256':sha(GDT),
 'portrait_receipt_sha256':sha(ART/'portrait.json'),
 'description':'Canonical native Dealer rendered at 1024; shared worn city metal border; fixed static emission .65; no added lights or runtime behavior.',
 'native_appearance':'Unplayed; Blender review approximates native shader and lighting.'}
(ART/'install.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print('DEALER_PRESENCE_INSTALLED',sha(DEST))
