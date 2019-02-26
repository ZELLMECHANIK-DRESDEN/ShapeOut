import dclab
import matplotlib.pylab as plt


# dataset
ds = dclab.new_dataset("fluorescence/fluorescence.rtdc")

evts = {"reference": 397,
        "extremely porous": 8228,
        "porosity above 1.05": 347,
        "invalid event": 4740,
        }

# plot
fig = plt.figure(figsize=(7, 3))


for ii, key in enumerate(evts.keys()):
    evt = evts[key] - 1
    axi = plt.subplot(2, 2, ii+1, title=key)
    text = "Porosity: {:.2f}\n".format(ds["area_ratio"][evt]) \
           + "Area [µm²]: {:.0f}\n".format(ds["area_um"][evt]) \
           + "Deformation: {:.3f}".format(ds["deform"][evt])
    axi.text(250, 15, text,
             va="top", ha="right", color="#B80000")
    image = ds["image"][evt]
    contour = ds["contour"][evt]
    axi.imshow(image, cmap="gray", vmin=0, vmax=100)
    plt.plot(contour[:, 0], contour[:, 1], color="#B80000", alpha=.5)
    axi.set_yticks([])
    axi.set_xticks([])


plt.tight_layout()
plt.savefig("qg_filter_porosity.jpg", dpi=150)
plt.show()
