""" """

import napari

from napari_hsi_analysis._widget_Fusion import FusionWidget
from napari_hsi_analysis._widget_UMAP import UMAPWidget
from napari_hsi_analysis._widgets_DataManager import DataManager
from napari_hsi_analysis.modules.data import Data
from napari_hsi_analysis.modules.plot_widget import PlotWidget


def run_napari_app():
    """Add widgets to the viewer"""
    try:
        viewer = napari.current_viewer()
    except AttributeError:
        viewer = napari.Viewer()

    # WIDGETS
    data = Data()
    plot_widget_datamanager = PlotWidget(viewer=viewer, data=data)
    plot_widget_umap = PlotWidget(viewer=viewer, data=data)
    datamanager_widget = DataManager(viewer, data, plot_widget_datamanager)
    fusion_widget = FusionWidget(viewer, data)
    umap_widget = UMAPWidget(viewer, data, plot_widget_umap)

    # Add widget as dock
    datamanager_dock = viewer.window.add_dock_widget(
        datamanager_widget, name="Data Manager", area="right"
    )
    fusion_dock = viewer.window.add_dock_widget(
        fusion_widget, name="Fusion", area="right"
    )
    umap_dock = viewer.window.add_dock_widget(
        umap_widget, name="UMAP", area="right"
    )

    # Tabify the widgets
    viewer.window._qt_window.tabifyDockWidget(datamanager_dock, fusion_dock)
    viewer.window._qt_window.tabifyDockWidget(fusion_dock, umap_dock)
    # Text overlay in the viewer
    viewer.text_overlay.visible = True

    viewer.dims.events.current_step.connect(datamanager_widget.update_wl)
    viewer.layers.selection.events.active.connect(
        datamanager_widget.on_layer_selected
    )

    return None  # Non serve restituire nulla
