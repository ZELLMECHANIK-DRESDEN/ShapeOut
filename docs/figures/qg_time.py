import dclab
import numpy as np
import matplotlib.pylab as plt

# dataset
ds = dclab.new_dataset("fluorescence/fluorescence.rtdc")

kde1 = ds.get_kde_scatter(xax="time", yax="deform")
kde2 = ds.get_kde_scatter(xax="time", yax="area_um")

scatkw = {"marker": ".",
          "s": 2,
          "cmap": "jet",
          "alpha": .7}

fig = plt.figure(figsize=(7, 3))

ax1 = plt.subplot(121)
ax1.scatter(ds["time"], ds["deform"], c=kde1, **scatkw)
ax1.set_xlabel(dclab.dfn.feature_name2label["time"])
ax1.set_ylabel(dclab.dfn.feature_name2label["deform"])


ax2 = plt.subplot(122)
ax2.scatter(ds["time"], ds["area_um"], c=kde2, **scatkw)
ax2.set_xlabel(dclab.dfn.feature_name2label["time"])
ax2.set_ylabel(dclab.dfn.feature_name2label["area_um"])


plt.tight_layout()
plt.savefig("qg_time.jpg", dpi=150)
plt.show()
