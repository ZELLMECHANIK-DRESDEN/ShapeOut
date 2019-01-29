import dclab
import numpy as np
import matplotlib.pylab as plt

# dataset
ds = dclab.new_dataset("fluorescence/fluorescence.rtdc")

fig = plt.figure(figsize=(7, 3))

ax1 = plt.subplot()
ax1.plot([ds["time"][0], ds["time"][-1]],
         [ds["index"][0], ds["index"][-1]],
         label="constant slope",
         lw=3)
ax1.plot(ds["time"], ds["index"], label="data")
ax1.set_xlabel(dclab.dfn.feature_name2label["time"])
ax1.set_ylabel(dclab.dfn.feature_name2label["index"])
ax1.legend()

plt.tight_layout()
plt.savefig("qg_countrate.jpg", dpi=150)
plt.show()
