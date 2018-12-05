import dclab
import matplotlib.pylab as plt


# dataset
ds = dclab.new_dataset("fluorescence/fluorescence.rtdc")

# plot
fig = plt.figure(figsize=(7, 3))


ax1a = plt.subplot(121)
ax1a.scatter(ds["area_um"], ds["deform"], s=.2,
             marker=".", color="#A51200", alpha=1)
ax1a.tick_params('x', colors='#A51200')
ax1a.set_xlabel(dclab.dfn.feature_name2label["area_um"], color='#A51200')
ax1a.set_ylabel(dclab.dfn.feature_name2label["deform"])
ax1a.set_xlim(0, 300)
ax1a.set_ylim(0, .2)

ax1b = ax1a.twiny()
ax1b.scatter(ds["volume"], ds["deform"], s=.1,
             marker=".", color="#046D71", alpha=1)
ax1b.tick_params('x', colors='#046D71')
ax1b.set_xlabel(dclab.dfn.feature_name2label["volume"],
                color='#046D71')
ax1b.set_xlim(0, 2500)


ax2a = plt.subplot(122)
ax2a.scatter(ds["area_um"], ds["inert_ratio_cvx"], s=.2,
             marker=".", color="#A51200", alpha=1)
ax2a.tick_params('x', colors='#A51200')
ax2a.set_xlabel(dclab.dfn.feature_name2label["area_um"], color='#A51200')
ax2a.set_ylabel(dclab.dfn.feature_name2label["inert_ratio_cvx"])
ax2a.set_xlim(0, 300)
ax2a.set_ylim(0.8, 3)

ax2b = ax2a.twiny()
ax2b.scatter(ds["volume"], ds["inert_ratio_cvx"], s=.1,
             marker=".", color="#046D71", alpha=1)
ax2b.tick_params('x', colors='#046D71')
ax2b.set_xlabel(dclab.dfn.feature_name2label["volume"],
                color='#046D71')
ax2b.set_xlim(0, 2500)


fig.text(0, 1, "A",
         fontsize=17,
         fontweight="bold",
         va="top", ha="left")
fig.text(0.5, 1, "B",
         fontsize=17,
         fontweight="bold",
         va="top", ha="left")

plt.tight_layout()
plt.savefig("volume.jpg", dpi=150)
plt.show()
