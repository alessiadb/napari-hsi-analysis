""" """

import sys
from os.path import dirname

sys.path.append(dirname(dirname(__file__)))
import napari
import pyqtgraph as pg
from magicgui.widgets import (
    CheckBox,
    ComboBox,
    Container,
    PushButton,
    SpinBox,
)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.figure import Figure
from napari.utils.notifications import show_info
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from napari_hsi_analysis.modules.functions import RGB_to_hex, derivative

# To correctly take the dependance

print("here: ", dirname(dirname(__file__)))


class DataManager(QWidget):
    """ """

    def __init__(self, viewer: napari.Viewer, data, plot_widget):
        """ """
        super().__init__()
        self.viewer = viewer
        self.data = data
        self.plot_widget = plot_widget
        scroll = QScrollArea()  # Creiamo lo scroll area
        scroll.setWidgetResizable(True)
        content_widget = (
            QWidget()
        )  # Creiamo un widget contenitore per i nostri elementi
        content_layout = QVBoxLayout(content_widget)  # Layout per i widget
        self.createUI(content_layout)  # Aggiungiamo i widget
        scroll.setWidget(
            content_widget
        )  # Impostiamo il widget nello scroll area
        main_layout = QVBoxLayout(self)  # Layout principale della finestra
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def createUI(self, layout):
        """ """
        # - - - open file box - - -
        open_box = QGroupBox("Open file")
        open_layout = QVBoxLayout()
        self.modes_combobox = ComboBox(
            choices=self.data.modes, label="Select the imaging mode"
        )  # DROPDOWN FOR CALIBRATION
        open_btn = PushButton(text="Open File")  # OPEN BUTTON
        open_btn.clicked.connect(self.open)
        rgb_btn = PushButton(text="Create RGB image")
        rgb_btn.clicked.connect(self.create_rgb)
        derivareive_btn = PushButton(text="Create Derivative")
        derivareive_btn.clicked.connect(self.create_derivative_f)
        open_layout.addWidget(
            Container(
                widgets=[
                    self.modes_combobox,
                    open_btn,
                    rgb_btn,
                    derivareive_btn,
                ]
            ).native
        )
        open_box.setLayout(open_layout)
        layout.addWidget(open_box)
        # - - - preprocessing box - - -
        processing_box = QGroupBox("Processing")
        processing_layout = QVBoxLayout()
        medfilt_layout = QVBoxLayout()
        self.medfilt_checkbox = CheckBox(text="2D Median filter")
        self.medfilt_spinbox = SpinBox(
            min=1, max=100, value=5, step=2, name="Window"
        )
        medfilt_layout.addWidget(
            Container(widgets=[self.medfilt_checkbox]).native
        )
        medfilt_layout.addWidget(
            Container(widgets=[self.medfilt_spinbox]).native
        )
        processing_layout.addLayout(medfilt_layout)
        savgol_layout = QVBoxLayout()
        savgol_variables_layout = QHBoxLayout()
        self.savgol_checkbox = CheckBox(text="Savitzky-Golay filter")
        self.savgolw_spinbox = SpinBox(
            min=1, max=100, value=11, step=2, name="Window"
        )
        self.savgolp_spinbox = SpinBox(
            min=1, max=100, value=3, step=2, name="Polynom"
        )
        savgol_layout.addWidget(
            Container(widgets=[self.savgol_checkbox]).native
        )
        savgol_variables_layout.addWidget(
            Container(
                widgets=[self.savgolw_spinbox, self.savgolp_spinbox]
            ).native
        )
        savgol_layout.addLayout(savgol_variables_layout)
        processing_layout.addLayout(savgol_layout)
        preprocessing_btn = PushButton(text="Process data")
        preprocessing_btn.clicked.connect(self.preprocessing_btn_f)
        processing_layout.addWidget(
            Container(widgets=[preprocessing_btn]).native
        )
        processing_box.setLayout(processing_layout)
        layout.addWidget(processing_box)
        # - - - dimensionality reduction - - -
        dimred_box = QGroupBox("Dimensionality reduction")
        dimred_layout = QHBoxLayout()
        self.spectral_dimred_checkbox = CheckBox(text="Spectral Reduction")
        self.spatial_dimred_checkbox = CheckBox(text="Spatial Reduction")
        dimred_btn = PushButton(text="Reduce data")
        dimred_btn.clicked.connect(self.dimred_btn_f)
        dimred_layout.addWidget(
            Container(
                widgets=[
                    self.spectral_dimred_checkbox,
                    self.spatial_dimred_checkbox,
                    dimred_btn,
                ]
            ).native
        )
        dimred_box.setLayout(dimred_layout)
        layout.addWidget(dimred_box)
        # - - - mean spectrum plot - - -
        meanspec_box = QGroupBox("Plot of mean spectrum")
        meanspec_layout = QVBoxLayout()
        meanspec_layout_plot = QVBoxLayout()
        self.meanspec_plot = FigureCanvas(Figure(figsize=(5, 3)))
        self.meanspec_plot.setMinimumSize(300, 400)
        self.plot_widget.setup_plot(self.meanspec_plot)
        plot_btn = PushButton(text="Mean spectrum")
        self.std_plot_checkbox = CheckBox(text="Plot standard deviation")
        self.norm_plot_checkbox = CheckBox(text="Normalize plot")
        self.derivative_checkbox = CheckBox(text="Plot with derivative")
        plot_btn.clicked.connect(
            lambda: self.plot_widget.show_plot(
                self.meanspec_plot,
                mode=self.modes_combobox.value,
                std_dev_checkbox=self.std_plot_checkbox.value,
                norm_checkbox=self.norm_plot_checkbox.value,
                reduced_dataset=self.spatial_dimred_checkbox.value,
                derivative=self.derivative_checkbox.value,
            )
        )
        meanspec_layout_plot.addWidget(
            Container(
                widgets=[
                    self.std_plot_checkbox,
                    self.norm_plot_checkbox,
                    self.derivative_checkbox,
                    plot_btn,
                ]
            ).native
        )  # NOTE that we need to use the "native" attribute with magicgui objects
        meanspec_layout_plot.addWidget(self.meanspec_plot)
        export_txt_layout = QVBoxLayout()
        export_txt_btn = PushButton(text="Export spectra in .txt")
        export_txt_btn.clicked.connect(
            lambda: self.plot_widget.show_plot(
                self.meanspec_plot,
                mode=self.modes_combobox.value,
                std_dev_checkbox=self.std_plot_checkbox.value,
                norm_checkbox=self.norm_plot_checkbox.value,
                export_txt=True,
            )
        )
        export_txt_layout.addWidget(Container(widgets=[export_txt_btn]).native)
        meanspec_layout.addLayout(meanspec_layout_plot)
        meanspec_layout.addLayout(export_txt_layout)
        meanspec_box.setLayout(meanspec_layout)
        layout.addWidget(meanspec_box)

        layout.addStretch()

    def show_popup(self, message: str):
        """ """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(str(message))
        # msg.setWindowTitle("Successo")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def open(self):
        """ """
        self.data.filepath, _ = QFileDialog.getOpenFileName()
        print(f"The data with path {self.data.filepath} will now be opened")
        self.data.mode = self.modes_combobox.value
        self.data.open_file(self.data.mode, self.data.filepath)
        # layer = self.viewer.add_image(
        self.viewer.add_image(
            self.data.hypercubes[self.data.mode].transpose(2, 0, 1),
            name=str(self.data.mode),
        )

    def print_wl(self):
        """ """
        print(self.viewer.dims.current_step[0])

    def update_wl(self):
        """ """
        self.data.mode = self.modes_combobox.value
        self.data.wl_value = self.viewer.dims.current_step[0]
        self.viewer.text_overlay.text = f"Wavelength: {round(self.data.wls[self.data.mode][self.data.wl_value], 2)} nm \nChannel: {self.data.wl_value}"
        print(self.data.wls[self.data.mode][self.data.wl_value])

    def create_rgb(self):
        """ """
        self.data.mode = self.modes_combobox.value
        name = str(self.data.mode) + " RGB"
        self.data.create_rgb_image(
            self.data.hypercubes[self.data.mode],
            self.data.wls[self.data.mode],
            self.data.mode,
        )
        # layer = self.viewer.add_image(self.data.rgb[self.data.mode], name=name)
        self.viewer.add_image(self.data.rgb[self.data.mode], name=name)

    def create_derivative_f(self):
        """ """
        self.data.mode = self.modes_combobox.value
        if self.data.mode not in self.data.hypercubes_processed:
            self.data.hypercubes[self.data.mode + " derivative"] = derivative(
                self.data.hypercubes[self.data.mode],
                savgol_w=15,
                savgol_pol=2,
                deriv=1,
            )
            # layer = self.viewer.add_image(
            self.viewer.add_image(
                self.data.hypercubes[self.data.mode + " derivative"].transpose(
                    2, 0, 1
                ),
                name=str(self.data.mode + " derivative"),
            )
        else:
            self.data.hypercubes[self.data.mode + " derivative"] = derivative(
                self.data.hypercubes[self.data.mode],
                savgol_w=9,
                savgol_pol=3,
                deriv=1,
            )
            # layer = self.viewer.add_image(
            self.viewer.add_image(
                self.data.hypercubes[self.data.mode + " derivative"].transpose(
                    2, 0, 1
                ),
                name=str(self.data.mode + " derivative"),
            )
        self.data.wls[self.data.mode + " derivative"] = self.data.wls[
            self.data.mode
        ]

    def preprocessing_btn_f(self):
        """ """
        self.data.mode = self.modes_combobox.value
        dataset = self.data.hypercubes[self.data.mode]
        mode = self.data.mode
        medfilt_checkbox = self.medfilt_checkbox.value
        savgol_checkbox = self.savgol_checkbox.value
        medfilt_w = self.medfilt_spinbox.value
        savgol_w = self.savgolw_spinbox.value
        savgol_p = self.savgolp_spinbox.value
        self.data.processing_data(
            dataset,
            mode,
            medfilt_checkbox,
            savgol_checkbox,
            medfilt_w,
            savgol_w,
            savgol_p,
        )
        show_info("Preprocessing completed!")

    def dimred_btn_f(self):
        """ """
        self.data.mode = self.modes_combobox.value
        if self.data.mode not in self.data.hypercubes_processed:
            dataset = self.data.hypercubes[self.data.mode]
        else:
            dataset = self.data.hypercubes_processed[self.data.mode]
        mode = self.data.mode
        spectral_dimred_checkbox = self.spectral_dimred_checkbox.value
        spatial_dimred_checkbox = self.spatial_dimred_checkbox.value
        self.data.dimensionality_reduction(
            dataset,
            mode,
            spectral_dimred_checkbox,
            spatial_dimred_checkbox,
            self.data.wls[mode],
        )
        print(self.data.hypercubes_processed_red[self.data.mode].shape)
        # layer = self.viewer.add_image(
        self.viewer.add_image(
            self.data.hypercubes_processed_red[self.data.mode].transpose(
                2, 0, 1
            ),
            name=str(self.data.mode) + " - REDUCED",
        )
        # layer = self.viewer.add_image(
        self.viewer.add_image(
            self.data.rgb_red[self.data.mode],
            name=str(self.data.mode) + " - REDUCED RGB",
        )


class UMAPWidget(QWidget):
    """ """

    def __init__(self, viewer: napari.Viewer, data, plot_widget):
        """ """
        super().__init__()
        self.viewer = viewer
        self.data = data
        self.plot_widget = plot_widget
        scroll = QScrollArea()  # Creiamo lo scroll area
        scroll.setWidgetResizable(True)
        content_widget = (
            QWidget()
        )  # Creiamo un widget contenitore per i nostri elementi
        content_layout = QVBoxLayout(content_widget)  # Layout per i widget
        self.createUI(content_layout)  # Aggiungiamo i widget
        scroll.setWidget(
            content_widget
        )  # Impostiamo il widget nello scroll area
        main_layout = QVBoxLayout(self)  # Layout principale della finestra
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def createUI(self, layout):
        """ """
        UMAP_box = QGroupBox("UMAP")
        UMAP_main_layout = QVBoxLayout()
        # - - - pca data - - -
        UMAP_layout_data = QHBoxLayout()
        self.reduced_dataset = CheckBox(text="Apply to reduced dataset")
        self.modes_combobox = ComboBox(
            choices=self.data.modes, label="Select the imaging mode"
        )  # DROPDOWN FOR CALIBRATION
        self.downsampling_spinbox = SpinBox(
            min=1, max=6, value=1, step=1, name="Downsampling"
        )
        self.metric_dropdown = ComboBox(
            choices=["euclidean", "cosine"], label="Select the imaging mode"
        )
        self.n_neighbors_spinbox = SpinBox(
            min=5, max=500, value=20, step=5, name="N Neighbors"
        )
        self.min_dist_spinbox = SpinBox(
            min=0.0, max=1.0, value=0.0, step=0.1, name="Min dist"
        )
        UMAP_perform_btn = PushButton(text="Perform UMAP")
        UMAP_perform_btn.clicked.connect(self.UMAP_perform_btn_f)
        UMAP_layout_data.addWidget(
            Container(
                widgets=[
                    self.reduced_dataset,
                    self.modes_combobox,
                    self.downsampling_spinbox,
                    self.metric_dropdown,
                    self.n_neighbors_spinbox,
                    self.min_dist_spinbox,
                    UMAP_perform_btn,
                ]
            ).native
        )
        # - - - UMAP plot variables - - -
        UMAP_layout_plot_var = QHBoxLayout()
        UMAP_show_plot_btn = PushButton(text="Show UMAP scatterplot")
        UMAP_show_plot_btn.clicked.connect(self.UMAP_show_plot_btn_f)
        UMAP_layout_plot_var.addWidget(
            Container(widgets=[UMAP_show_plot_btn]).native
        )
        # - - - UMAP scatterplot - - -
        UMAP_layout_plot = QVBoxLayout()
        self.UMAP_plot_widget = pg.PlotWidget()
        self.UMAP_plot_widget.setMinimumSize(300, 400)
        UMAP_layout_plot_btn = QHBoxLayout()
        self.UMAP_home_btn = self.plot_widget.create_home_button(
            label="fa5s.home"
        )
        self.UMAP_home_btn.clicked.connect(
            lambda: self.UMAP_plot_widget.getViewBox().autoRange()
        )  # Crea una funzione anonima che non viene eseguita subito ma solo quando viene cliccato
        self.UMAP_select_btn = self.plot_widget.create_home_button(
            label="fa5s.draw-polygon"
        )
        self.UMAP_select_btn.clicked.connect(
            lambda: self.plot_widget.polygon_selection(self.UMAP_plot_widget)
        )
        self.UMAP_print_btn = self.plot_widget.create_home_button(
            label="mdi6.file-image-plus"
        )
        self.UMAP_print_btn.clicked.connect(
            lambda: self.plot_widget.print_selected_points(
                self.UMAP_reshaped,
                self.UMAP_dataset,
                self.modes_combobox.value,
                self.hex_reshaped,
                self.UMAP_plot_widget,
            )
        )
        UMAP_layout_plot_btn.addWidget(
            self.UMAP_home_btn, alignment=Qt.AlignLeft
        )
        UMAP_layout_plot_btn.addWidget(
            self.UMAP_select_btn, alignment=Qt.AlignLeft
        )
        UMAP_layout_plot_btn.addWidget(
            self.UMAP_print_btn, alignment=Qt.AlignLeft
        )
        UMAP_layout_plot.addLayout(UMAP_layout_plot_btn)
        UMAP_layout_plot.addWidget(self.UMAP_plot_widget)
        # - - - UMAP meanplot - - -
        # - - - mean spectrum plot - - -
        UMAP_layout_meanplot = QVBoxLayout()
        UMAP_layout_meanplot_plot = QVBoxLayout()
        UMAP_meanspec_plot = FigureCanvas(Figure(figsize=(5, 3)))
        UMAP_meanspec_plot.setMinimumSize(300, 400)
        self.plot_widget.setup_plot(UMAP_meanspec_plot)
        UMAP_meanplot_btn = PushButton(text="Mean spectrum")
        self.std_plot_checkbox = CheckBox(text="Plot standard deviation")
        self.norm_plot_checkbox = CheckBox(text="Normalize plot")
        self.derivative_checkbox = CheckBox(text="Plot with derivative")
        UMAP_meanplot_btn.clicked.connect(
            lambda: self.plot_widget.show_plot(
                UMAP_meanspec_plot,
                mode=self.modes_combobox.value,
                std_dev_checkbox=self.std_plot_checkbox.value,
                norm_checkbox=self.norm_plot_checkbox.value,
                reduced_dataset=self.reduced_dataset.value,
                from_scatterplot=True,
                derivative=self.derivative_checkbox.value,
            )
        )
        UMAP_layout_meanplot_plot.addWidget(
            Container(
                widgets=[
                    self.std_plot_checkbox,
                    self.norm_plot_checkbox,
                    self.derivative_checkbox,
                    UMAP_meanplot_btn,
                ]
            ).native
        )  # NOTE that we need to use the "native" attribute with magicgui objects
        UMAP_layout_meanplot_plot.addWidget(UMAP_meanspec_plot)
        export_txt_layout = QVBoxLayout()
        export_txt_btn = PushButton(text="Export spectra in .txt")
        export_txt_btn.clicked.connect(
            lambda: self.plot_widget.show_plot(
                UMAP_meanspec_plot,
                mode=self.modes_combobox.value,
                std_dev_checkbox=self.std_plot_checkbox.value,
                norm_checkbox=self.norm_plot_checkbox.value,
                reduced_dataset=self.reduced_dataset.value,
                export_txt=True,
                from_scatterplot=True,
            )
        )
        export_txt_layout.addWidget(Container(widgets=[export_txt_btn]).native)
        UMAP_layout_meanplot.addLayout(UMAP_layout_meanplot_plot)
        UMAP_layout_meanplot.addLayout(export_txt_layout)
        UMAP_main_layout.addLayout(UMAP_layout_data)
        UMAP_main_layout.addLayout(UMAP_layout_plot_var)
        UMAP_main_layout.addLayout(UMAP_layout_plot)
        UMAP_main_layout.addLayout(UMAP_layout_meanplot)
        UMAP_box.setLayout(UMAP_main_layout)
        layout.addWidget(UMAP_box)
        layout.addStretch()

    def UMAP_perform_btn_f(self):
        """ """
        self.data.mode = self.modes_combobox.value
        if self.reduced_dataset.value:
            self.UMAP_dataset = self.data.hypercubes_processed_red[
                self.data.mode
            ]
        elif self.data.mode not in self.data.hypercubes_processed:
            self.UMAP_dataset = self.data.hypercubes[self.data.mode]
        else:
            self.UMAP_dataset = self.data.hypercubes_processed[self.data.mode]
        downsampling = self.downsampling_spinbox.value
        metric = self.metric_dropdown.value
        n_neighbors = self.n_neighbors_spinbox.value
        min_dist = self.min_dist_spinbox.value
        self.data.umap_analysis(
            self.UMAP_dataset,
            self.data.mode,
            downsampling,
            metric,
            n_neighbors,
            min_dist,
        )
        show_info("UMAP analysis completed!")

    def UMAP_show_plot_btn_f(self):
        """ """
        self.data.mode = self.modes_combobox.value
        self.UMAP_reshaped = self.data.umap_maps[self.modes_combobox.value]
        if self.reduced_dataset.value:
            hex_values = RGB_to_hex(self.data.rgb_red[self.data.mode])
        else:
            hex_values = RGB_to_hex(self.data.rgb[self.data.mode])
        self.hex_reshaped = hex_values.reshape(-1)
        self.plot_widget.show_scatterplot(
            self.UMAP_plot_widget, self.UMAP_reshaped, self.hex_reshaped
        )
