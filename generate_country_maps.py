
from lib.kartograph import Kartograph, KartographOptions
import lib.proj

countries = ["AGO", "BDI", "BEN", "BFA", "BWA", "CAF", "CIV", "CMR", "COD", "COG", "COM", "DJI", "DZA", "EGY", "ERI", "ETH", "FRA", "GAB", "GHA", "GIN", "GMB", "GNB", "GNQ", "KEN", "LBR", "LBY", "LSO", "MAR", "MDG", "MLI", "MOZ", "MRT", "MWI", "NAM", "NER", "NGA", "RWA", "SDN", "SEN", "SLE", "SOM", "STP", "SWZ", "SYC", "TCD", "TGO", "TUN", "TZA", "UGA", "ZAF", "ZMB", "ZWE"]

countries = ["SSD"]

opt = KartographOptions()

opt.out_height = 700
opt.out_width = 700
opt.round_coordinates = True
opt.out_padding_perc = 0.05
opt.projection = lib.proj.projections['laea']
opt.applyDefaults()

k = Kartograph(opt)

for iso in countries:
	k.render_country_and_context(iso, outfile=iso+'.svg')
