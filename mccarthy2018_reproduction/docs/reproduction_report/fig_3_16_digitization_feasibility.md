# Fig. 3.16 Digitization Feasibility

Fig. 3.16 is a static 3D torus rendering. It remains unsuitable for precise
3D digitization from the image alone because the camera, projection model, and
raw branch states are not encoded in the bitmap.

Current status: digitization is no longer needed to justify the Fig. 3.16 source
layer. The current figure uses the accepted Route H fixed-time quasi-DRO branch
from `data/computed/chapter3_fixed_mapping_cache_accepted_family.csv`.

Route H evidence:

- accepted validation rows: `30`
- best max abs z: `14573.10318409037` km
- rows above 10,500 km: `30`
- rows above 11,000 km: `29`
- max map residual: `6.469474407020314e-10`

The static original figure can still be used as a qualitative visual reference,
but not as a raw numerical data source.
