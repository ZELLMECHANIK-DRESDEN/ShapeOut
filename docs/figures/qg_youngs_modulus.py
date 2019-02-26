import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors

from dclab.features.emodulus import get_emodulus

settings = [{"channel width": 15,
             "flow rate 1": 0.016,
             "flow rate 2": 0.032,
             "flow rate 3": 0.048,
             "x range": [10, 170],
             "x max": 200,
             },
            {"channel width": 20,
             "flow rate 1": 0.04,
             "flow rate 2": 0.08,
             "flow rate 3": 0.12,
             "x range": [20, 300],
             "x max": 300,
             },
            {"channel width": 30,
             "flow rate 1": 0.16,
             "flow rate 2": 0.24,
             "flow rate 3": 0.32,
             "x range": [50, 680],
             "x max": 700,
             },
            {"channel width": 40,
             "flow rate 1": 0.32,
             "flow rate 2": 0.40,
             "flow rate 3": 0.60,
             "x range": [90, 1200],
             "x max": 1200,
             },
            ]

for st in settings:
    temperature = 24
    pixel_size = 0.34
    Emin = 0.04
    Emax = 30

    x = np.linspace(0, st["x max"], 400)
    y = np.linspace(0, 0.17, 800)

    x, y = np.meshgrid(x, y)

    emodkw = {"area_um": x,
              "deform": y,
              "temperature": temperature,
              "px_um": pixel_size,
              }

    E_CC_1 = get_emodulus(medium="CellCarrier",
                          channel_width=st["channel width"],
                          flow_rate=st["flow rate 1"],
                          **emodkw)
    E_CC_2 = get_emodulus(medium="CellCarrier",
                          channel_width=st["channel width"],
                          flow_rate=st["flow rate 2"],
                          **emodkw)
    E_CC_3 = get_emodulus(medium="CellCarrier",
                          channel_width=st["channel width"],
                          flow_rate=st["flow rate 3"],
                          **emodkw)

    E_CCB_1 = get_emodulus(medium="CellCarrier B",
                           channel_width=st["channel width"],
                           flow_rate=st["flow rate 1"],
                           **emodkw)
    E_CCB_2 = get_emodulus(medium="CellCarrier B",
                           channel_width=st["channel width"],
                           flow_rate=st["flow rate 2"],
                           **emodkw)
    E_CCB_3 = get_emodulus(medium="CellCarrier B",
                           channel_width=st["channel width"],
                           flow_rate=st["flow rate 3"],
                           **emodkw)

    E_H2O_1 = get_emodulus(medium="water",
                           channel_width=st["channel width"],
                           flow_rate=st["flow rate 1"],
                           **emodkw)
    E_H2O_2 = get_emodulus(medium="water",
                           channel_width=st["channel width"],
                           flow_rate=st["flow rate 2"],
                           **emodkw)
    E_H2O_3 = get_emodulus(medium="water",
                           channel_width=st["channel width"],
                           flow_rate=st["flow rate 3"],
                           **emodkw)

    # start with a rectangular Figure
    plt.rcParams['axes.grid'] = True
    fig, ax = plt.subplots(nrows=3, ncols=3, figsize=(7, 5),
                           sharey=True, sharex=True)
    fig.suptitle(str(st["channel width"])+" µm channel")
    ax[0, 0].set_xlim(st["x range"])
    ax[0, 0].set_ylim([0, 0.17])
    ax[2, 0].set_xlabel("Area [µm²]")
    ax[2, 1].set_xlabel("Area [µm²]")
    ax[2, 2].set_xlabel("Area [µm²]")
    ax[0, 0].set_ylabel("Deformation")
    ax[1, 0].set_ylabel("Deformation")
    ax[2, 0].set_ylabel("Deformation")
    scatkw = {"x": x,
              "y": y,
              "s": 6,
              "norm": colors.LogNorm(vmin=Emin, vmax=Emax),
              "marker": "o",
              "linewidth": 0,
              "zorder": 3,
              "cmap": "nipy_spectral",
              }
    pem = ax[0, 0].scatter(c=E_CC_1, **scatkw)
    ax[0, 1].scatter(c=E_CC_2, **scatkw)
    ax[0, 2].scatter(c=E_CC_3, **scatkw)

    ax[1, 0].scatter(c=E_CCB_1, **scatkw)
    ax[1, 1].scatter(c=E_CCB_2, **scatkw)
    ax[1, 2].scatter(c=E_CCB_3, **scatkw)

    ax[2, 0].scatter(c=E_H2O_1, **scatkw)
    ax[2, 1].scatter(c=E_H2O_2, **scatkw)
    ax[2, 2].scatter(c=E_H2O_3, **scatkw)

    fig.subplots_adjust(right=0.83)
    cbar_ax = fig.add_axes([0.86, 0.11, 0.02, .77])
    cbar = fig.colorbar(pem, cax=cbar_ax, extend="max")
    cbar.ax.set_ylabel("apparent Young's modulus [kPa]")
    ax[0, 0].set_title("flow rate: {} µl/s".format(st["flow rate 1"]),
                       fontsize=10)
    ax[0, 1].set_title("flow rate: {} µl/s".format(st["flow rate 2"]),
                       fontsize=10)
    ax[0, 2].set_title("flow rate: {} µl/s".format(st["flow rate 3"]),
                       fontsize=10)
    fig.subplots_adjust(left=0.15)
    row_ax = fig.add_axes([0.0, 0.0, 0.03, 1.0])
    row_ax.spines['top'].set_visible(False)
    row_ax.spines['right'].set_visible(False)
    row_ax.spines['bottom'].set_visible(False)
    row_ax.spines['left'].set_visible(False)
    textkw = {"rotation": "vertical",
              "fontsize": 10,
              "fontweight": "demibold",
              "va": "center"}
    row_ax.text(0.5, 0.23, "Water", **textkw)
    row_ax.text(0.5, 0.5, "CellCarrier B", **textkw)
    row_ax.text(0.5, 0.77, "CellCarrier", **textkw)
    row_ax.grid(False)

    fig.savefig("qg_youngs_modulus_{}um.png".format(
        st["channel width"]), dpi=150)

    plt.close()
