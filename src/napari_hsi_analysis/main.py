""" """

import napari

from napari_hsi_analysis._widgets import DataManager, UMAPWidget
from napari_hsi_analysis.modules.data import Data
from napari_hsi_analysis.modules.plot_widget import PlotWidget


def run_napari_app():
    """Aggiunge i widget al viewer esistente senza creare una nuova finestra."""

    # Ottieni il viewer attuale, se esiste
    try:
        viewer = napari.current_viewer()
    except AttributeError:
        viewer = napari.Viewer()  # Se non esiste, creane uno

    # Crea gli oggetti dati e widget
    data = Data()
    plot_widget_datamanager = PlotWidget(viewer=viewer, data=data)
    plot_widget_umap = PlotWidget(viewer=viewer, data=data)
    datamanager_widget = DataManager(viewer, data, plot_widget_datamanager)
    umap_widget = UMAPWidget(viewer, data, plot_widget_umap)

    # Aggiungi i widget come dock widget nel viewer
    datamanager_dock = viewer.window.add_dock_widget(
        datamanager_widget, name="Data Manager", area="right"
    )
    umap_dock = viewer.window.add_dock_widget(
        umap_widget, name="UMAP", area="right"
    )

    # Tabifica i widget (li mette nella stessa area con schede)
    viewer.window._qt_window.tabifyDockWidget(datamanager_dock, umap_dock)
    # Abilita il text overlay nel viewer
    viewer.text_overlay.visible = True

    # Collega l'evento di cambio dimensione al metodo di aggiornamento nel widget
    viewer.dims.events.current_step.connect(datamanager_widget.update_wl)

    return None  # Non serve restituire nulla
