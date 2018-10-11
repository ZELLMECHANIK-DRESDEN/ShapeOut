import dclab
import matplotlib.pylab as plt


# dataset
ds = dclab.new_dataset("deform/M1_data.tdms")
# kernel density estimate
kde = ds.get_kde_scatter(xax="area_um", yax="deform")
# isoelasticity lines
isodef = dclab.isoelastics.get_default()
iso = isodef.get_with_rtdcbase(method="numerical",
                               col1="area_um",
                               col2="deform",
                               dataset=ds)

fig = plt.figure(figsize=(7, 3))

# simple scatter plot
ax1 = plt.subplot(121)
sc = ax1.scatter(ds["area_um"], ds["deform"], c=kde,
                 marker=".", cmap="jet", alpha=.7)

cax = fig.add_axes([.09, .41, .015, .53])
cax.set_ylabel("density")
cbar = plt.colorbar(sc, cax=cax, ticks=[kde.min(), kde.max()])
cbar.set_ticklabels(["min", "max"])

# isoelasticity lines only
ax2 = plt.subplot(122)
ax2.text(55, .105,
         "isoelasticity line",
         fontsize=13,
         color="gray",
         rotation=67)
# arrows
bbox_props1 = dict(boxstyle="larrow", fc="#0200A4",
                   ec="#0200A4", alpha=.6, lw=1)
ax2.text(210, .08, "      softer     ", ha="center", va="center", rotation=-35,
         size=15,
         color="w",
         bbox=bbox_props1)
bbox_props2 = dict(boxstyle="rarrow", fc="#A40400",
                   ec="#A40400", alpha=.6, lw=1)
ax2.text(175, .05, "     stiffer     ", ha="center", va="center", rotation=-35,
         size=15,
         color="w",
         bbox=bbox_props2)


# plot adjustments
for ax in [ax1, ax2]:
    # isoelasticity lines
    for ss in iso:
        ax.plot(ss[:, 0], ss[:, 1], color="gray", zorder=0)
    # axes labels
    ax.set_xlabel(dclab.dfn.feature_name2label["area_um"])
    ax.set_ylabel(dclab.dfn.feature_name2label["deform"])
    # axes limits
    ax.set_xlim(25, 280)
    ax.set_ylim(0.0, 0.12)

fig.text(0, 1, "A",
         fontsize=17,
         fontweight="bold",
         va="top", ha="left")
fig.text(0.5, 1, "B",
         fontsize=17,
         fontweight="bold",
         va="top", ha="left")


plt.tight_layout(pad=0)
plt.savefig("deform.jpg", dpi=150)
