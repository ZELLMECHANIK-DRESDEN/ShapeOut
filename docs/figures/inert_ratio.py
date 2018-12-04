import dclab
from dclab.features import contour, inert_ratio
import numpy as np
import matplotlib.pylab as plt
from scipy.ndimage.interpolation import rotate
from skimage.draw import polygon

# setup inertia ratio contours
img1 = np.zeros((300, 800), dtype=bool)
pol1 = np.array((
    (50, 50),
    (50, 750),
    (250, 750),
    (250, 50),
))
rr, cc = polygon(pol1[:, 0], pol1[:, 1], img1.shape)
img1[rr, cc] = True

img2 = rotate(np.array(img1, dtype=int), 5, reshape=False)
img2 = img2 > .5

cont1 = contour.get_contour(img1)
cont2 = contour.get_contour(img2)

# convert mask to inertia ratio
# regular inertia ratio
rir1 = inert_ratio.get_inert_ratio_raw(cont1)
rir2 = inert_ratio.get_inert_ratio_raw(cont2)
# principal inertia ratio
pir1 = inert_ratio.get_inert_ratio_prnc(cont1)
pir2 = inert_ratio.get_inert_ratio_prnc(cont2)

fig = plt.figure(figsize=(7, 3))

ax1 = plt.subplot(221, title="rectangle")
ax1.imshow(img1, cmap="gray_r")
ax1.text(.5, .5,
         "inertia ratio: {:.1f}\nprincipal inertia ratio: {:.1f}".format(
             rir1, pir1),
         transform=ax1.transAxes, color="w", va="center", ha="center")

ax2 = plt.subplot(223, title="rotated rectangle")
ax2.imshow(img2, cmap="gray_r")
ax2.text(.5, .5,
         "inertia ratio: {:.1f}\nprincipal inertia ratio: {:.1f}".format(
             rir2, pir2),
         transform=ax2.transAxes, color="w", va="center", ha="center")


for ax in [ax1, ax2]:
    ax.set_yticks([])
    ax.set_xticks([])

# dataset
ds = dclab.new_dataset("fluorescence/fluorescence.rtdc")


ax3a = plt.subplot(122, title="correlation to porosity")
ax3a.scatter(ds["area_ratio"], ds["deform"], s=.2,
             marker=".", color="#072BA3", alpha=1)
ax3a.tick_params('y', colors='#072BA3')
ax3a.set_xlabel(dclab.dfn.feature_name2label["area_ratio"])
ax3a.set_ylabel(dclab.dfn.feature_name2label["deform"], color='#072BA3')
ax3a.set_xlim(1, 2)
ax3a.set_ylim(0, .2)


ax3b = ax3a.twinx()
ax3b.scatter(ds["area_ratio"], ds["inert_ratio_cvx"], s=.1,
             marker=".", color="#9507A3", alpha=1)
ax3b.tick_params('y', colors='#9507A3')
ax3b.set_ylabel(dclab.dfn.feature_name2label["inert_ratio_cvx"],
                color='#9507A3')
ax3b.set_ylim(0, 6)


fig.text(0, 1, "A",
         fontsize=17,
         fontweight="bold",
         va="top", ha="left")
fig.text(0, .57, "B",
         fontsize=17,
         fontweight="bold",
         va="top", ha="left")
fig.text(0.45, 1, "C",
         fontsize=17,
         fontweight="bold",
         va="top", ha="left")

plt.tight_layout()
plt.savefig("inert_ratio.jpg", dpi=150)
plt.show()
