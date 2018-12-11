# in order for chaco to work in frozen mode, uncomment the line
#
#    raise NotImplementedError("the %s pyface backend doesn't implement %s" % (ETSConfig.toolkit, oname))
#
# in pyface.toolkt.py in line 92
from PyInstaller.utils.hooks import collect_submodules

hiddenimports=['enable',
               'enable.toolkit_constants',
               'kiva',
               'kiwisolver',
               'pyface',
               'pyface.image_resource',
               'traitsui.toolkit',
               'traits.etsconfig.api',
               'wx',
               'reportlab',
               'reportlab.rl_settings',
               'pyface.action.action_item',
              ]

hiddenimports += collect_submodules('pyface.ui.wx')
hiddenimports += collect_submodules('traitsui.wx')
hiddenimports += collect_submodules('enable.wx')

excludedimports = ['PyQt4', 'PyQt5', 'PySide', 'Tkinter', 'wx.lib.activex']
