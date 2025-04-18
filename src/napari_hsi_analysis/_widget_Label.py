""" """

import sys
from os.path import dirname

sys.path.append(dirname(dirname(__file__)))
import h5py
import napari
import numpy as np
import pandas as pd
from magicgui.widgets import (
    LineEdit,
    PushButton,
)
from napari.utils.notifications import show_warning
from qtpy.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class LabelWidget(QWidget):
    """ """

    def __init__(self, viewer: napari.Viewer, data, datamanager):
        """ """
        super().__init__()
        self.viewer = viewer
        self.data = data
        self.datamanager = datamanager
        self.init_ui()

    def init_ui(self):
        """ """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        label_group = self.build_label_group()
        content_layout.addWidget(label_group)
        content_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def build_label_group(self):
        """ """
        label_box = QGroupBox("Label")
        label_layout = QHBoxLayout()

        self.label_input = LineEdit(label="Insert the label here")

        save_label_btn = PushButton(text="Apply label and save .txt")
        save_label_btn.clicked.connect(self.save_label_btn_f)

        label_layout.addWidget(self.label_input.native)
        label_layout.addWidget(save_label_btn.native)

        save_masked_data_btn = PushButton(text="Save masked data")
        save_masked_data_btn.clicked.connect(self.save_masked_data_btn_f)
        label_layout.addWidget(save_masked_data_btn.native)

        label_box.setLayout(label_layout)
        return label_box

    def save_label_btn_f(self):
        """ """
        mode = self.datamanager.modes_combobox.value
        dataset = self.data.hypercubes[mode]

        selected_layer = self.viewer.layers.selection.active
        if not isinstance(selected_layer, napari.layers.Labels):
            show_warning(
                "⚠️ The selected layer is not a label layer. Please, select a label layer."
            )
            return
        labels_layer = self.viewer.layers.selection.active.data
        # If coming from UMAP, we don't need to do np.sum
        labels_layer_mask = np.sum(labels_layer, axis=0)
        indexes = np.array(np.where(labels_layer_mask != 0))
        points = dataset[indexes[0], indexes[1], :]
        df = pd.DataFrame(points)
        print(points.shape)
        print(df)
        df["Label"] = str(self.label_input.value)
        print(df)

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save spectra in .csv", "", "csv (*.csv)"
        )

        df.to_csv(
            filename,
            sep="\t",
            index=False,
        )

    def save_masked_data_btn_f(self):
        mode = self.datamanager.modes_combobox.value
        dataset = self.data.hypercubes_masked[mode]
        wl = self.data.wls[mode]

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save data in .h5", "", "h5 (*.h5)"
        )

        with h5py.File(filename, "w") as f:
            f.create_dataset("data", data=dataset)
            f.create_dataset("wavelength", data=wl)
