""" """

import sys
from os.path import dirname

import napari

sys.path.append(dirname(dirname(__file__)))
# print("here: ", dirname(dirname(__file__)))

from napari_hsi_analysis._widget_Fusion import FusionWidget
from napari_hsi_analysis._widget_Label import LabelWidget
from napari_hsi_analysis._widget_UMAP import UMAPWidget
from napari_hsi_analysis._widgets_DataManager import DataManager
from napari_hsi_analysis.modules.data import Data
from napari_hsi_analysis.modules.plot_widget import PlotWidget


class NapariApp:
    """ """

    def __init__(self):
        """ """
        self.viewer = napari.Viewer()
        self.data = Data()
        self.plot_widget_datamanager = PlotWidget(
            viewer=self.viewer, data=self.data
        )
        self.plot_widget_umap = PlotWidget(viewer=self.viewer, data=self.data)
        self.datamanager_widget = DataManager(
            self.viewer, self.data, self.plot_widget_datamanager
        )
        self.fusion_widget = FusionWidget(self.viewer, self.data)
        self.umap_widget = UMAPWidget(
            self.viewer, self.data, self.plot_widget_umap
        )
        self.label_widget = LabelWidget(
            self.viewer, self.data, self.datamanager_widget
        )

        self.setup_dock_widgets()
        self.setup_connections()

    # def create_dock_widget(self, widget, name, area="right", min_size=(400, 400)): 0
    #    """Add a dock widget to the viewer."""
    #    dock = self.viewer.window.add_dock_widget(widget, name=name, area=area)
    #    if min_size:
    #        dock.setMinimumSize(*min_size)
    #    return dock

    def setup_dock_widgets(
        self,
    ):
        """ """
        datamanager_dock = self.viewer.window.add_dock_widget(
            self.datamanager_widget, name="Data Manager", area="right"
        )
        umap_dock = self.viewer.window.add_dock_widget(
            self.umap_widget, name="UMAP", area="right"
        )
        fusion_dock = self.viewer.window.add_dock_widget(
            self.fusion_widget, name="Fusion", area="right"
        )
        label_dock = self.viewer.window.add_dock_widget(
            self.label_widget, name="Labeling", area="right"
        )
        self.viewer.window._qt_window.tabifyDockWidget(
            datamanager_dock, fusion_dock
        )
        self.viewer.window._qt_window.tabifyDockWidget(fusion_dock, umap_dock)
        self.viewer.window._qt_window.tabifyDockWidget(umap_dock, label_dock)

    def setup_connections(self):
        """ """
        self.viewer.text_overlay.visible = True
        self.viewer.dims.events.current_step.connect(
            self.datamanager_widget.update_wl
        )
        self.viewer.layers.selection.events.active.connect(
            self.datamanager_widget.on_layer_selected
        )

    def run(self):
        """ """
        napari.run()


if __name__ == "__main__":
    """ """
    app = NapariApp()
    app.run()
