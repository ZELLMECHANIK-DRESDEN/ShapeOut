import dclab
import numpy as np
import matplotlib.pylab as plt


# dataset
ds = dclab.new_dataset("fluorescence/fluorescence.rtdc")

evt = 54

# traces
flraw = ds["trace"]["fl2_raw"][evt]
flmed = ds["trace"]["fl2_median"][evt]

# plot
fig = plt.figure(figsize=(7, 3))

# image
axi = plt.subplot(221, title="event image")
axi.imshow(ds["image"][evt], cmap="gray")
axi.set_yticks([])
axi.set_xticks([])

# trace
ax1 = plt.subplot(223, title="fluorescence trace")
bin_size_us = 1 / 500000 * 1e6
time = np.linspace(0, bin_size_us*len(flraw), len(flraw))
ax1.plot(time, flraw/100, label="raw", lw=2)
ax1.plot(time, flmed/100, label="median filter", lw=1.5)
ax1.set_xlabel("time [µs]")
ax1.set_ylabel("signal [a.u]")
ax1.legend(borderaxespad=0, frameon=False)

# scatter plot
axs = plt.subplot(122, title="scatter plot")
# filter away saturation events
ds.config["filtering"]["fl2_max max"] = 31000
ds.config["filtering"]["fl2_area max"] = 1300000
ds.apply_filter()
filt = ds.filter.all
axs.scatter(ds["fl2_area"][filt]/1000, ds["fl2_max"][filt]/100, c="k",
            marker=".", alpha=.05)
axs.set_xlabel(dclab.dfn.feature_name2label["fl2_area"])
axs.set_ylabel(dclab.dfn.feature_name2label["fl2_max"])

fig.text(0, 1, "A",
         fontsize=17,
         fontweight="bold",
         va="top", ha="left")
fig.text(0, .57, "B",
         fontsize=17,
         fontweight="bold",
         va="top", ha="left")
fig.text(0.5, 1, "C",
         fontsize=17,
         fontweight="bold",
         va="top", ha="left")

plt.tight_layout()
plt.savefig("fluorescence.jpg", dpi=150)
plt.show()