# in order for chaco to work in frozen mode, uncomment the line
#
#    raise NotImplementedError("the %s pyface backend doesn't implement %s" % (ETSConfig.toolkit, oname))
#
# in pyface.toolkt.py in line 92
hiddenimports=['enable',
               'enable.toolkit_constants',
               'enable.wx',
               'enable.wx.image',
               'enable.wx.base_window',
               'enable.wx.scrollbar',
               'enable.wx.quartz',
               'enable.wx.gl',
               'enable.wx.constants',
               'enable.wx.cairo',
               'kiva',
               'kiwisolver',
               'pyface',
               'pyface.image_resource',
               'pyface.ui.wx',
               'pyface.ui.wx.action',
               'pyface.ui.wx.action.action_item',
               'pyface.ui.wx.action.menu_bar_manager',
               'pyface.ui.wx.action.menu_manager',
               'pyface.ui.wx.action.status_bar_manager',
               'pyface.ui.wx.init',
               'traitsui.toolkit',
               'traitsui.wx',
               'traitsui.wx.menu',
               'traits.etsconfig.api',
               'wx',
               'reportlab',
               'reportlab.rl_settings',
               'pyface.action.action_item',
              ]

