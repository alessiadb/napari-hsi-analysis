""" """

import sys
from os.path import dirname

sys.path.append(dirname(dirname(__file__)))
import napari
import numpy as np
import pyqtgraph as pg
from magicgui.widgets import (
    CheckBox,
    ComboBox,
    Container,
    FloatSpinBox,
    PushButton,
    SpinBox,
)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from napari.utils.notifications import show_info
from qtpy.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from napari_hsi_analysis.modules.functions import RGB_to_hex


class UMAPWidget(QWidget):
    """ """

    def __init__(self, viewer: napari.Viewer, data, plot_widget):
        """ """
        super().__init__()
        self.viewer = viewer
        self.data = data
        self.plot_widget = plot_widget
        self.init_ui()

    def init_ui(self):
        """ """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        umap_group = self.build_umap_group()
        content_layout.addWidget(umap_group)
        content_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def build_umap_group(self):
        """ """
        umap_box = QGroupBox("UMAP")
        umap_layout = QVBoxLayout()

        umap_layout.addLayout(self.create_umap_controls())
        umap_layout.addLayout(self.create_scatter_plot_area())
        umap_layout.addLayout(self.create_mean_spectrum_area())

        umap_box.setLayout(umap_layout)
        return umap_box

    def create_umap_controls(self):
        """ """
        layout = QVBoxLayout()

        row1 = QHBoxLayout()
        self.reduced_dataset = CheckBox(text="Apply to reduced dataset")
        self.masked_dataset = CheckBox(text="Apply to masked dataset")
        self.modes_combobox = ComboBox(
            choices=self.data.modes, label="Select the imaging mode"
        )
        row1.addWidget(self.reduced_dataset.native)
        row1.addWidget(self.modes_combobox.native)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(self.masked_dataset.native)
        layout.addLayout(row2)

        self.downsampling_spinbox = SpinBox(
            min=1, max=6, value=1, step=1, name="Downsampling"
        )
        self.metric_dropdown = ComboBox(
            choices=["euclidean", "cosine"], label="Select the imaging mode"
        )
        self.n_neighbors_spinbox = SpinBox(
            min=5, max=500, value=20, step=5, name="N Neighbours"
        )
        self.min_dist_spinbox = FloatSpinBox(
            min=0.0, max=1.0, value=0.0, step=0.1, name="Min dist"
        )
        layout.addWidget(
            Container(
                widgets=[
                    self.downsampling_spinbox,
                    self.metric_dropdown,
                    self.n_neighbors_spinbox,
                    self.min_dist_spinbox,
                ]
            ).native
        )

        run_btn = PushButton(text="Run UMAP")
        run_btn.clicked.connect(self.run_umap)
        layout.addWidget(run_btn.native)

        show_btn = PushButton(text="Show UMAP scatterplot")
        show_btn.clicked.connect(self.show_umap_scatter)
        layout.addWidget(show_btn.native)

        return layout

    def create_scatter_plot_area(self):
        """ """
        layout = QVBoxLayout()
        self.umap_plot = pg.PlotWidget()
        self.plot_widget.setup_scatterplot(self.umap_plot)

        # Add control buttons for scatter plot interaction
        btn_layout = QHBoxLayout()

        for icon, func in [
            ("fa5s.home", lambda: self.umap_plot.getViewBox().autoRange()),
            (
                "fa5s.draw-polygon",
                lambda: self.plot_widget.polygon_selection(self.umap_plot),
            ),
            ("ri.add-box-fill", self.handle_selection),
            (
                "mdi6.image-edit",
                lambda: self.plot_widget.save_image_button(self.umap_plot),
            ),
        ]:
            btn = self.plot_widget.create_button(icon)
            btn.clicked.connect(func)
            btn_layout.addWidget(btn)

        self.point_size = SpinBox(
            min=1, max=100, value=1, step=1, name="Point size"
        )
        btn_layout.addSpacing(30)
        btn_layout.addWidget(Container(widgets=[self.point_size]).native)
        layout.addLayout(btn_layout)
        layout.addWidget(self.umap_plot)
        return layout

    def create_mean_spectrum_area(self):
        """ """
        layout = QVBoxLayout()
        self.mean_plot = FigureCanvas(Figure(figsize=(5, 3)))
        self.mean_plot.setMinimumSize(300, 450)
        self.mean_plot_toolbar = NavigationToolbar(self.mean_plot, self)
        self.plot_widget.customize_toolbar(self.mean_plot_toolbar)
        self.plot_widget.setup_plot(self.mean_plot)

        mean_btn = PushButton(text="Mean Spectrum")
        self.std_checkbox = CheckBox(text="Plot Std Dev")
        self.norm_checkbox = CheckBox(text="Normalize")
        self.derivative_checkbox = CheckBox(text="Derivative")

        mean_btn.clicked.connect(self.plot_mean_spectrum)

        controls = [
            self.std_checkbox,
            self.norm_checkbox,
            self.derivative_checkbox,
            mean_btn,
        ]
        layout.addWidget(Container(widgets=controls).native)
        layout.addWidget(self.mean_plot)
        layout.addWidget(self.mean_plot_toolbar)

        # Export button
        export_btn = PushButton(text="Export spectra as .txt")
        export_btn.clicked.connect(self.export_spectrum)
        layout.addWidget(Container(widgets=[export_btn]).native)
        return layout

    def run_umap(self):
        """Perform UMAP"""
        mode = self.modes_combobox.value
        if self.masked_dataset.value:
            dataset = self.data.hypercubes_masked[mode]
            data_reshaped = dataset.reshape(
                dataset.shape[0] * dataset.shape[1], -1
            )
            self.points = np.array(
                np.where(~np.isnan(np.mean(data_reshaped, axis=1)))
            ).flatten()
        elif self.reduced_dataset.value:
            dataset = self.data.hypercubes_red[mode]
            self.points = []
        else:
            dataset = self.data.hypercubes[mode]
            self.points = []

        self.data.umap_analysis(
            dataset,
            mode,
            self.downsampling_spinbox.value,
            self.metric_dropdown.value,
            self.n_neighbors_spinbox.value,
            self.min_dist_spinbox.value,
            self.points,
        )
        show_info("UMAP analysis completed!")

    def show_umap_scatter(self):
        """Plot UMAP scatter plot"""
        mode = self.modes_combobox.value
        self.umap_data = self.data.umap_maps[mode]
        if self.reduced_dataset.value:
            colors = RGB_to_hex(self.data.rgb_red[mode])
        elif self.masked_dataset.value:
            colors = RGB_to_hex(self.data.rgb_masked[mode])
        else:
            colors = RGB_to_hex(self.data.rgb[mode])

        print("Colors: \n", colors.reshape(-1))
        self.plot_widget.show_scatterplot(
            self.umap_plot,
            self.umap_data,
            colors.reshape(-1),
            self.points,
            self.point_size.value,
        )

    def handle_selection(self):
        """Handle polygon selection and create label layer"""
        mode = self.modes_combobox.value
        if self.reduced_dataset.value:
            dataset = self.data.hypercubes_red[mode]
            self.points = []
        elif self.masked_dataset.value:
            dataset = self.data.hypercubes_masked[mode]
            data_reshaped = dataset.reshape(
                dataset.shape[0] * dataset.shape[1], -1
            )
            self.points = np.array(
                np.where(~np.isnan(np.mean(data_reshaped, axis=1)))
            ).flatten()
        else:
            dataset = self.data.hypercubes[mode]
        self.plot_widget.show_selected_points(
            self.umap_data,
            dataset,
            mode,
            self.points,
        )

    def plot_mean_spectrum(self):
        """Plot the mean spectrum of the selected area"""

        self.plot_widget.show_plot(
            self.mean_plot,
            mode=self.modes_combobox.value,
            std_dev_flag=self.std_checkbox.value,
            norm_flag=self.norm_checkbox.value,
            reduced_dataset_flag=self.reduced_dataset.value,
            from_scatterplot_flag=True,
            derivative_flag=self.derivative_checkbox.value,
        )

    def export_spectrum(self):
        """Export the mean spectrum"""
        self.plot_widget.show_plot(
            self.mean_plot,
            mode=self.modes_combobox.value,
            std_dev_flag=self.std_checkbox.value,
            norm_flag=self.norm_checkbox.value,
            reduced_dataset_flag=self.reduced_dataset.value,
            export_txt_flag=True,
            from_scatterplot_flag=True,
        )
