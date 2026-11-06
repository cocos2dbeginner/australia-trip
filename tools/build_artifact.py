"""Build a Claude Artifact version of index.html.

Artifacts block map tiles, Google iframes and outside stylesheets, so this:
- drops the document skeleton (the artifact host adds its own),
- inlines Leaflet's CSS and loads Leaflet JS from cdnjs,
- draws Australia's coastline as polygons instead of OpenStreetMap tiles,
- hides the Google Maps mode (links to Google Maps still open in a new tab).
Usage: python3 tools/build_artifact.py <leaflet.css> <output.html>
"""
import re, sys

src = open("index.html", encoding="utf-8").read()
leaflet_css = open(sys.argv[1], encoding="utf-8").read()
out_path = sys.argv[2]

def rep(old, new, count=1):
    global src
    assert src.count(old) == count, (src.count(old), old[:80])
    src = src.replace(old, new)

# skeleton -> artifact header
head_end = src.index("<style>")
src = ('<title>Australia Summer Run</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
       '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>\n'
       "<style>\n/* Leaflet 1.9.4 (BSD-2-Clause) */\n" + leaflet_css + "\n</style>\n" + src[head_end:])
rep("</style>\n</head><body>", "</style>")
rep("</body></html>", "")
src = src.replace("</body></html>\n", "")

# land + ocean tokens
rep("--route-fly:#625e5b; --halo:#ffffff;", "--route-fly:#625e5b; --halo:#ffffff; --ocean:#dfe9ec; --land:#efebe4; --land-edge:#cfc8bd;")
rep("--route-fly:#a8a39e; --halo:#141413;", "--route-fly:#a8a39e; --halo:#141413; --ocean:#16201f; --land:#2a2926; --land-edge:#45423e;", 2)
rep(".leaflet-container{font-family:var(--body);background:var(--panel)}",
    ".leaflet-container{font-family:var(--body);background:var(--ocean)}\n.chip.show,#m-route,#m-google,.mapcard>.seg[aria-label=\"Map type\"],#gbox{display:none!important}")

# coastline instead of tiles
COAST = "[[142.5,-10.7],[143.5,-12.5],[143.8,-14],[145.3,-15],[145.5,-16.5],[146.1,-18.3],[147,-19.3],[148.5,-20.1],[149.4,-21.2],[150.6,-22.5],[151,-23.6],[152.4,-24.7],[153.1,-25.8],[153.1,-27.5],[153.6,-28.6],[153.1,-30.5],[152.7,-31.8],[152,-32.8],[151.2,-33.9],[150.8,-34.8],[150.2,-35.9],[149.9,-37.5],[148,-37.8],[146.4,-39.1],[145,-38.5],[144.5,-38.2],[143.5,-38.8],[141.5,-38.4],[140,-37.5],[139.6,-36.5],[138.6,-35.6],[138.5,-34.8],[138.1,-34.2],[137.7,-35.1],[136.9,-35.3],[137.4,-34],[137.8,-32.6],[136.5,-33.8],[135.6,-34.9],[135.2,-34.5],[134.2,-32.9],[132.5,-32],[131,-31.5],[129,-31.7],[126.5,-32.3],[124,-33],[123.5,-33.9],[121,-33.8],[119.5,-34.4],[117.9,-35.1],[116,-34.8],[115,-34.3],[115.7,-33.3],[115.7,-31.7],[115,-29.5],[114.6,-28.5],[113.5,-26.5],[113.7,-24.5],[113.6,-22.5],[114.2,-21.8],[116.7,-20.6],[118.8,-20.3],[121,-19.5],[122.3,-18],[123.5,-17],[124.5,-16],[125.5,-14.5],[127.5,-14],[128.2,-15],[129.6,-14.9],[130.2,-13.2],[130.8,-12.4],[132.5,-11.6],[133,-11.4],[135,-12.1],[136.7,-12.2],[136,-13.5],[135.5,-14.9],[137,-15.9],[139.3,-17.4],[140.8,-17.4],[141.5,-15.5],[141.6,-12.5]]"
TAS = "[[144.6,-40.7],[146,-41.1],[148.3,-40.9],[148.3,-42.2],[147.9,-43.2],[146.8,-43.6],[145.9,-43.5],[145.2,-42.2]]"
tile = re.search(r'L\.tileLayer\(.*?\}\)\.addTo\(lmap\);', src, re.S).group(0)
src = src.replace(tile, f'''const landTok = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
let landLayer = null;
function drawLand() {{
  if (landLayer) landLayer.remove();
  const style = {{ color: landTok("--land-edge"), weight: 1, fillColor: landTok("--land"), fillOpacity: 1, interactive: false }};
  landLayer = L.layerGroup([{COAST}, {TAS}].map(p => L.polygon(p.map(([lon, lat]) => [lat, lon]), style))).addTo(lmap);
  landLayer.eachLayer(l => l.bringToBack());
}}
drawLand();
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", drawLand);
lmap.attributionControl.addAttribution("Coastline simplified");''')
rep("const lmap = L.map(box, { zoomControl: true, scrollWheelZoom: true, worldCopyJump: false })",
    "const lmap = L.map(box, { zoomControl: true, scrollWheelZoom: true, worldCopyJump: false, minZoom: 3, maxZoom: 9, maxBounds: [[-5, 105], [-50, 165]] })")
rep("lmap.flyTo(ll(stops()[sel].c), 11,", "lmap.flyTo(ll(stops()[sel].c), 8,")
rep("Map data © OpenStreetMap contributors. Activity links open Google Maps for reviews.",
    "Map coastline is simplified. Activity names and “Google Maps ↗” open Google Maps in a new tab for reviews.")
open(out_path, "w", encoding="utf-8").write(src)
print("wrote", out_path, len(src), "bytes")
