""" """

import sys
from os.path import dirname

sys.path.append(dirname(dirname(__file__)))
import napari
import numpy as np
from magicgui.widgets import (
    CheckBox,
    ComboBox,
    Container,
    Label,
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
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from napari_hsi_analysis.modules.functions import (
    derivative,
    falseRGB,
)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class DataManager(QWidget):
    """ """

    def __init__(self, viewer: napari.Viewer, data, plot_widget):
        """ """
        super().__init__()
        self.viewer = viewer
        self.data = data
        self.plot_widget = plot_widget
        # Configure the scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()  # Container
        content_layout = QVBoxLayout(content_widget)  # Layout
        # Configure UI
        self.createUI(content_layout)  # Function
        # Configure principal layout
        scroll.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def createUI(self, layout):
        """Create the components for the UI"""
        layout.addWidget(self.create_open_box())
        layout.addWidget(self.create_processing_box())
        layout.addWidget(self.create_dimred_box())
        layout.addWidget(self.create_meanspec_box())
        layout.addWidget(self.create_falseRGB_box())
        layout.addStretch()

    def create_open_box(self):
        """Create box for file opening"""
        open_box = QGroupBox("Open file")
        open_layout = QVBoxLayout()

        # Elements
        self.modes_combobox = ComboBox(
            choices=self.data.modes, label="Select the imaging mode"
        )
        open_btn = PushButton(text="Open File")
        open_btn.clicked.connect(self.open_btn_f)
        rgb_btn = PushButton(text="Create RGB image")
        rgb_btn.clicked.connect(self.rgb_btn_f)
        derivareive_btn = PushButton(text="Create Derivative")
        derivareive_btn.clicked.connect(self.derivative_btn_f)

        # Add widgets to the layout
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
        return open_box

    def create_processing_box(self):
        """Preprocessing of the data"""
        processing_box = QGroupBox("Processing")
        processing_layout = QVBoxLayout()
        # Crop and mask
        crop_layout = self.create_crop_section()
        processing_layout.addLayout(crop_layout)
        # Median filter
        medfilt_layout = self.create_medfilt_section()
        processing_layout.addLayout(medfilt_layout)
        # Savitzky-Golay
        savgol_layout = self.create_savgol_section()
        processing_layout.addLayout(savgol_layout)
        # Preprocessing button
        preprocessing_btn = PushButton(text="Process data")
        preprocessing_btn.clicked.connect(self.preprocessing_btn_f)
        processing_layout.addWidget(
            Container(widgets=[preprocessing_btn]).native
        )
        processing_box.setLayout(processing_layout)
        return processing_box

    def create_crop_section(self):
        """Crop and create mask"""
        crop_layout = QHBoxLayout()
        crop_btn = PushButton(text="Crop")
        crop_btn.clicked.connect(self.crop_btn_f)
        crop_layout.addWidget(Container(widgets=[crop_btn]).native)
        mask_layout = QHBoxLayout()
        self.mask_reduced_checkbox = CheckBox(text="From reduced dataset")
        mask_btn = PushButton(text="Create Mask")
        mask_btn.clicked.connect(self.mask_btn_f)
        mask_layout.addWidget(
            Container(
                widgets=[
                    self.mask_reduced_checkbox,
                    mask_btn,
                ]
            ).native
        )
        crop_layout.addLayout(mask_layout)
        return crop_layout

    def create_medfilt_section(self):
        """Median filter"""
        medfilt_layout = QHBoxLayout()
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
        return medfilt_layout

    def create_savgol_section(self):
        """Savitzky-Golay"""
        savgol_layout = QHBoxLayout()
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
        return savgol_layout

    def create_dimred_box(self):
        """Dimensionality reduction"""
        dimred_box = QGroupBox("Dimensionality reduction")
        dimred_layout = QVBoxLayout()

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
        return dimred_box

    def create_meanspec_box(self):
        """Plot of the mean spectrum"""
        meanspec_box = QGroupBox("Plot of mean spectrum")
        meanspec_layout = QVBoxLayout()
        # Plot
        meanspec_layout_plot = self.create_meanspec_plot_section()
        meanspec_layout.addLayout(meanspec_layout_plot)
        # Export
        export_txt_layout = self.create_export_section()
        meanspec_layout.addLayout(export_txt_layout)
        meanspec_box.setLayout(meanspec_layout)
        return meanspec_box

    def create_meanspec_plot_section(self):
        """Mean spectrum"""
        meanspec_layout_plot = QVBoxLayout()

        self.meanspec_plot = FigureCanvas(Figure(figsize=(5, 3)))
        self.meanspec_plot.setMinimumSize(300, 450)
        self.meanspec_plot_toolbar = NavigationToolbar(
            self.meanspec_plot, self
        )
        self.plot_widget.customize_toolbar(self.meanspec_plot_toolbar)
        self.plot_widget.setup_plot(self.meanspec_plot)

        plot_btn = PushButton(text="Mean spectrum")
        self.dimred_checkbox = CheckBox(text="Reduced dataset")
        self.std_plot_checkbox = CheckBox(text="Plot standard deviation")
        self.norm_plot_checkbox = CheckBox(text="Normalize plot")
        self.derivative_checkbox = CheckBox(text="Plot with derivative")

        plot_btn.clicked.connect(
            lambda: self.plot_widget.show_plot(
                self.meanspec_plot,
                mode=self.modes_combobox.value,
                std_dev_flag=self.std_plot_checkbox.value,
                norm_flag=self.norm_plot_checkbox.value,
                reduced_dataset_flag=self.dimred_checkbox.value,
                derivative_flag=self.derivative_checkbox.value,
            )
        )

        meanspec_layout_plot.addWidget(
            Container(
                widgets=[
                    self.std_plot_checkbox,
                    self.norm_plot_checkbox,
                    self.derivative_checkbox,
                    self.dimred_checkbox,
                    plot_btn,
                ]
            ).native
        )
        meanspec_layout_plot.addWidget(self.meanspec_plot)
        meanspec_layout_plot.addWidget(self.meanspec_plot_toolbar)

        return meanspec_layout_plot

    def create_export_section(self):
        """Export mean spectrum"""
        export_txt_layout = QVBoxLayout()

        export_txt_btn = PushButton(text="Export spectra in .txt")
        export_txt_btn.clicked.connect(
            lambda: self.plot_widget.show_plot(
                self.meanspec_plot,
                mode=self.modes_combobox.value,
                std_dev_flag=self.std_plot_checkbox.value,
                norm_flag=self.norm_plot_checkbox.value,
                reduced_dataset_flag=self.dimred_checkbox.value,
                export_txt_flag=True,
            )
        )

        export_txt_layout.addWidget(Container(widgets=[export_txt_btn]).native)
        return export_txt_layout

    def create_falseRGB_box(self):
        """Box for false RGB"""
        falseRGB_box = QGroupBox("False RGB")
        falseRGB_layout = QVBoxLayout()

        falseRGB_layout.addSpacing(10)
        R_layout, self.R_min_spinbox, self.R_max_spinbox = (
            self.create_channel_falsergb_section([650, 700], "R")
        )
        falseRGB_layout.addLayout(R_layout)

        G_layout, self.G_min_spinbox, self.G_max_spinbox = (
            self.create_channel_falsergb_section([550, 600], "G")
        )
        falseRGB_layout.addLayout(G_layout)

        B_layout, self.B_min_spinbox, self.B_max_spinbox = (
            self.create_channel_falsergb_section([450, 500], "B")
        )
        falseRGB_layout.addLayout(B_layout)

        # self.R_rangeslider = RangeSlider(value=[630, 700], min=300, max=1000, label="R")
        # self.G_rangeslider = RangeSlider(value=[550, 600], min=300, max=1000, label="G")
        # self.B_rangeslider = RangeSlider(value=[450, 500], min=300, max=1000, label="B")

        falseRGB_btn = PushButton(text="Create False RGB")
        falseRGB_btn.clicked.connect(self.falseRGB_btn_f)

        falseRGB_layout.addWidget(
            Container(
                widgets=[
                    # self.R_rangeslider,
                    # self.G_rangeslider,
                    # self.B_rangeslider,
                    falseRGB_btn
                ]
            ).native
        )

        falseRGB_box.setLayout(falseRGB_layout)
        return falseRGB_box

    def create_channel_falsergb_section(self, value, label_name):
        """ """
        channel_layout = QHBoxLayout()
        label = Label(value=label_name)
        label.native.setFixedWidth(20)
        channel_layout.addSpacing(50)
        channel_layout.addWidget(label.native)
        min_spinbox = SpinBox(
            min=0, max=2500, step=1, value=value[0], label=label_name
        )
        max_spinbox = SpinBox(min=0, max=2500, step=1, value=value[1])
        channel_layout.addSpacing(50)
        channel_layout.addWidget(min_spinbox.native)
        channel_layout.addSpacing(50)
        channel_layout.addWidget(max_spinbox.native)

        return channel_layout, min_spinbox, max_spinbox

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def open_btn_f(self):
        """ """
        self.data.filepath, _ = QFileDialog.getOpenFileName()
        print(f"The data with path {self.data.filepath} will now be opened")
        data_mode = self.modes_combobox.value
        self.data.open_file(data_mode, self.data.filepath)
        # layer = self.viewer.add_image(
        self.viewer.add_image(
            self.data.hypercubes[data_mode].transpose(2, 0, 1),
            name=str(data_mode),
            metadata={"type": "hyperspectral_cube"},
        )
        self.crop_array = [
            0,
            0,
            self.data.hypercubes[data_mode].shape[0],
            self.data.hypercubes[data_mode].shape[1],
        ]

    def update_wl(self):
        """ """
        data_mode = self.modes_combobox.value
        wl_index = self.viewer.dims.current_step[0]
        max_index = len(self.data.wls[data_mode]) - 1
        wl_index = min(wl_index, max_index)
        self.data.wl_value = wl_index
        wl = round(self.data.wls[data_mode][wl_index], 2)
        self.viewer.text_overlay.text = (
            f"Wavelength: {wl} nm \nChannel: {self.data.wl_value}"
        )
        # print(self.data.wls[data_mode][self.data.wl_value])

    def rgb_btn_f(self):
        """ """
        data_mode = self.modes_combobox.value
        name = str(data_mode) + " RGB"
        self.data.create_rgb_image(
            self.data.hypercubes[data_mode],
            self.data.wls[data_mode],
            data_mode,
        )
        # layer = self.viewer.add_image(self.data.rgb[self.data.mode], name=name)
        self.viewer.add_image(
            self.data.rgb[data_mode],
            name=name,
            metadata={"type": "rgb"},
        )

    def derivative_btn_f(self):
        """ """
        data_mode = self.modes_combobox.value
        self.data.hypercubes[data_mode + " derivative"] = derivative(
            self.data.hypercubes[data_mode],
            savgol_w=9,
            savgol_pol=3,
            deriv=1,
        )
        # layer = self.viewer.add_image(
        self.viewer.add_image(
            self.data.hypercubes[data_mode + " derivative"].transpose(2, 0, 1),
            name=str(data_mode + " derivative"),
            metadata={"type": "hyperspectral_cube"},
        )
        self.data.wls[data_mode + " derivative"] = self.data.wls[data_mode]

    def crop_btn_f(self):
        data_mode = self.modes_combobox.value
        shape_layer = next(
            (
                rect
                for rect in self.viewer.layers
                if isinstance(rect, napari.layers.Shapes)
            ),
            None,
        )
        if not shape_layer or len(shape_layer.data) == 0:
            print("Nessuno shape selezionato.")
            return None

        shape = shape_layer.data[0]
        min_y = int(np.min(shape[:, 2]))
        max_y = int(np.max(shape[:, 2]))
        min_x = int(np.min(shape[:, 1]))
        max_x = int(np.max(shape[:, 1]))
        print("Points for cropping: ", min_x, min_y, max_x, max_y)
        self.crop_array = [min_x, min_y, max_x, max_y]

        # Crop del cubo (preserva tutte le bande spettrali)
        self.data.hypercubes[data_mode] = self.data.hypercubes[data_mode][
            min_x:max_x, min_y:max_y, :
        ]
        print(f"Cropped shape: {self.data.hypercubes[data_mode].shape}")
        self.viewer.add_image(
            self.data.hypercubes[data_mode].transpose(2, 0, 1),
            name=str(data_mode) + " cropped",
            metadata={"type": "cropped_hsi_cube"},
        )

    def mask_btn_f(self):
        """ """
        data_mode = self.modes_combobox.value
        # SELECT LABEL LAYER
        # takes all the layers but the seleciton is only in the image (WL) in which i've done it
        labels_layer = self.viewer.layers.selection.active.data
        # If coming from UMAP, we don't need to do np.sum
        labels_layer_mask = (
            labels_layer
            if "SCATTERPLOT"
            in self.viewer.layers.selection.active.name.upper()
            else np.sum(labels_layer, axis=0)
        )
        if self.mask_reduced_checkbox.value:
            self.crop_array = [
                0,
                0,
                self.data.hypercubes_red[data_mode].shape[0],
                self.data.hypercubes_red[data_mode].shape[1],
            ]
        print(labels_layer_mask, labels_layer_mask.shape)
        labels_layer_mask = labels_layer_mask[
            : self.crop_array[2] - self.crop_array[0],
            : self.crop_array[3] - self.crop_array[1],
        ]
        print(labels_layer_mask, labels_layer_mask.shape)
        self.data.create_mask(
            labels_layer_mask, self.mask_reduced_checkbox.value, data_mode
        )
        self.viewer.add_image(
            self.data.hypercubes_masked[data_mode].transpose(2, 0, 1),
            name=str(data_mode) + " masked",
            metadata={"type": "masked_hsi_cube"},
        )

        self.viewer.add_image(
            self.data.rgb_masked[data_mode],
            name=str(data_mode) + " masked - RGB",
            metadata={"type": "masked_rgb"},
        )

    def preprocessing_btn_f(self):
        """ """
        data_mode = self.modes_combobox.value
        dataset = self.data.hypercubes[data_mode]
        medfilt_checkbox = self.medfilt_checkbox.value
        savgol_checkbox = self.savgol_checkbox.value
        medfilt_w = self.medfilt_spinbox.value
        savgol_w = self.savgolw_spinbox.value
        savgol_p = self.savgolp_spinbox.value
        self.data.processing_data(
            dataset,
            data_mode,
            medfilt_checkbox,
            savgol_checkbox,
            medfilt_w,
            savgol_w,
            savgol_p,
        )
        show_info("Preprocessing completed!")

    def dimred_btn_f(self):
        """ """
        data_mode = self.modes_combobox.value
        dataset = self.data.hypercubes[data_mode]
        spectral_dimred_checkbox = self.spectral_dimred_checkbox.value
        spatial_dimred_checkbox = self.spatial_dimred_checkbox.value
        self.data.dimensionality_reduction(
            dataset,
            data_mode,
            spectral_dimred_checkbox,
            spatial_dimred_checkbox,
            self.data.wls[data_mode],
        )

        # print(self.data.hypercubes_red[data_mode].shape)
        self.viewer.add_image(
            self.data.hypercubes_red[data_mode].transpose(2, 0, 1),
            name=str(data_mode) + " - REDUCED",
            metadata={"type": "reduced_hsi_cube"},
        )
        self.viewer.add_image(
            self.data.rgb_red[data_mode],
            name=str(data_mode) + " - REDUCED RGB",
            metadata={"type": "reduced_rgb"},
        )

    def falseRGB_btn_f(self):
        """ """
        data_mode = self.modes_combobox.value
        R_values = [self.R_min_spinbox.value, self.R_max_spinbox.value]
        G_values = [self.G_min_spinbox.value, self.G_max_spinbox.value]
        B_values = [self.B_min_spinbox.value, self.B_max_spinbox.value]
        falseRGB_image = falseRGB(
            self.data.hypercubes[data_mode],
            self.data.wls[data_mode],
            R_values,
            G_values,
            B_values,
        )
        self.viewer.add_image(
            falseRGB_image,
            name=str(data_mode) + " - FALSE RGB",
            metadata={"type": "false_rgb"},
        )

    def on_layer_selected(self):
        """ """
        selected_layer = self.viewer.layers.selection.active
        if selected_layer is None:
            return
        elif selected_layer.metadata.get("type") == "hyperspectral_cube":
            print(selected_layer.name)
            self.modes_combobox.value = selected_layer.name
        elif selected_layer.metadata.get("type") == "rgb":
            print(selected_layer.name[:-4])
            self.modes_combobox.value = selected_layer.name[:-4]
        elif selected_layer.metadata.get("type") == "reduced_hsi_cube":
            print(selected_layer.name[:-10])
            self.modes_combobox.value = selected_layer.name[:-10]
        elif selected_layer.metadata.get("type") == "reduced_rgb":
            print(selected_layer.name[:-14])
            self.modes_combobox.value = selected_layer.name[:-14]
        elif selected_layer.metadata.get("type") == "cropped_hsi_cube":
            print(selected_layer.name[:-8])
            self.modes_combobox.value = selected_layer.name[:-8]
        elif selected_layer.metadata.get("type") == "masked_hsi_cube":
            print(selected_layer.name[:-7])
            self.modes_combobox.value = selected_layer.name[:-7]
        elif selected_layer.metadata.get("type") == "masked_rgb":
            print(selected_layer.name[:-13])
            self.modes_combobox.value = selected_layer.name[:-13]
