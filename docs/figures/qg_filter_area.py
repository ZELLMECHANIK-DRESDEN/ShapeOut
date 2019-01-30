import dclab
import matplotlib.pylab as plt


# dataset
ds = dclab.new_dataset("fluorescence/fluorescence.rtdc")

evts = {"reference": 546,
        "debris": 1979,
        "doublet": 1323,
        "aggregate": 2223,
        }

# plot
fig = plt.figure(figsize=(7, 3))


for ii, key in enumerate(evts.keys()):
    evt = evts[key] - 1
    axi = plt.subplot(2, 2, ii+1, title=key)
    axi.text(250, 15, "Area [µm²]: {:.0f}".format(ds["area_um"][evt]),
             va="top", ha="right", color="#B80000")
    axi.imshow(ds["image"][evt], cmap="gray", vmin=0, vmax=100)
    axi.set_yticks([])
    axi.set_xticks([])


plt.tight_layout()
plt.savefig("qg_filter_area.jpg", dpi=150)
plt.show()