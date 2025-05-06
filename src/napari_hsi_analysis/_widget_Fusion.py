""" """

import sys
from os.path import dirname

sys.path.append(dirname(dirname(__file__)))
import napari
from magicgui.widgets import (
    CheckBox,
    ComboBox,
    Container,
    PushButton,
)
from napari.utils.notifications import show_info
from qtpy.QtWidgets import (
    QGroupBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from napari_hsi_analysis.modules.functions import (
    datasets_fusion,
)


class FusionWidget(QWidget):
    """ """

    def __init__(self, viewer: napari.Viewer, data):
        """ """
        super().__init__()
        self.viewer = viewer
        self.data = data
        self.init_ui()

    def init_ui(self):
        """ """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        fusion_group = self.build_fusion_group()
        content_layout.addWidget(fusion_group)
        content_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def build_fusion_group(self):
        """ """
        fusion_box = QGroupBox("Fusion")
        fusion_layout = QVBoxLayout()

        fusion_layout.addLayout(self.create_fusion_controls())

        fusion_box.setLayout(fusion_layout)
        return fusion_box

    def create_fusion_controls(self):
        """ """
        layout = QVBoxLayout()

        self.reduced_dataset_checkbox = CheckBox(
            text="Fuse the reduced dataset (Only if you have both reduced datasets)"
        )

        self.modes_fusion = ComboBox(
            choices=["l2", "std"], label="Select fusion modality"
        )

        self.modes_combobox_1 = ComboBox(
            choices=self.data.modes, label="Select the first dataset"
        )
        self.modes_combobox_2 = ComboBox(
            choices=self.data.modes,
            label="Select the second dataset",
            value="PL",
        )
        self.modes_combobox_3 = ComboBox(
            choices=self.data.modes,
            label="Select the third dataset",
            value="-",
        )

        fusion_perform_btn = PushButton(text="Fuse the chosen datasets")
        fusion_perform_btn.clicked.connect(self.fusion_perform_btn_f)

        layout.addWidget(
            Container(
                widgets=[
                    self.reduced_dataset_checkbox,
                    self.modes_fusion,
                    self.modes_combobox_1,
                    self.modes_combobox_2,
                    self.modes_combobox_3,
                    fusion_perform_btn,
                ]
            ).native
        )
        return layout

    def fusion_perform_btn_f(self):
        """ """
        self.data.fusion_modes = []
        self.data.fusion_modes.append(self.modes_combobox_1.value)
        self.data.fusion_modes.append(self.modes_combobox_2.value)
        wl1 = self.data.wls[self.modes_combobox_1.value]
        wl2 = self.data.wls[self.modes_combobox_2.value]
        if self.modes_combobox_3.value != "-":
            self.data.fusion_modes.append(self.modes_combobox_3.value)
            wl3 = self.data.wls[self.modes_combobox_1.value]
        if self.reduced_dataset_checkbox.value:
            if (
                self.data.hypercubes_spatial_red.get(
                    self.modes_combobox_1.value
                )
                is not None
                and self.data.hypercubes_spatial_red.get(
                    self.modes_combobox_2.value
                )
                is not None
            ):
                dataset1 = self.data.hypercubes_spatial_red[
                    self.modes_combobox_1.value
                ]
                dataset2 = self.data.hypercubes_spatial_red[
                    self.modes_combobox_2.value
                ]
                (
                    self.data.hypercubes_spatial_red["Fused"],
                    self.data.wls["Fused"],
                ) = datasets_fusion(
                    dataset1, dataset2, wl1, wl2, norm=self.modes_fusion.value
                )
            else:
                dataset1 = self.data.hypercubes_red[
                    self.modes_combobox_1.value
                ]
                dataset2 = self.data.hypercubes_red[
                    self.modes_combobox_2.value
                ]

            self.data.rgb_red["Fused"] = self.data.rgb_red[
                self.modes_combobox_1.value
            ]
            self.data.hypercubes_red["Fused"], self.data.wls["Fused"] = (
                datasets_fusion(
                    dataset1, dataset2, wl1, wl2, norm=self.modes_fusion.value
                )
            )

            if self.modes_combobox_3.value != "-":
                if (
                    self.data.hypercubes_spatial_red.get(
                        self.modes_combobox_3.value
                    )
                    is not None
                ):
                    dataset3 = self.data.hypercubes_spatial_red[
                        self.modes_combobox_3.value
                    ]
                    (
                        self.data.hypercubes_spatial_red["Fused"],
                        self.data.wls["Fused"],
                    ) = datasets_fusion(
                        self.data.hypercubes_spatial_red["Fused"],
                        dataset3,
                        self.data.wls["Fused"],
                        wl3,
                        norm=self.modes_fusion.value,
                    )
                else:
                    dataset3 = self.data.hypercubes_red[
                        self.modes_combobox_3.value
                    ]
                self.data.hypercubes_red["Fused"], self.data.wls["Fused"] = (
                    datasets_fusion(
                        self.data.hypercubes_red["Fused"],
                        dataset3,
                        self.data.wls["Fused"],
                        wl3,
                        norm=self.modes_fusion.value,
                    )
                )

        else:
            dataset1 = self.data.hypercubes[self.modes_combobox_1.value]
            dataset2 = self.data.hypercubes[self.modes_combobox_2.value]
            if self.data.rgb.get(self.modes_combobox_1.value) is not None:
                self.data.rgb["Fused"] = self.data.rgb[
                    self.modes_combobox_1.value
                ]
            else:
                self.data.create_rgb_image(
                    self.data.hypercubes[self.modes_combobox_1.value],
                    self.data.wls[self.modes_combobox_1.value],
                    self.modes_combobox_1.value,
                )
                self.viewer.add_image(
                    self.data.rgb[self.modes_combobox_1.value],
                    name=str(self.modes_combobox_1.value) + " RGB",
                    metadata={"type": "rgb"},
                )
            self.data.hypercubes["Fused"], self.data.wls["Fused"] = (
                datasets_fusion(
                    dataset1, dataset2, wl1, wl2, norm=self.modes_fusion.value
                )
            )

            if self.modes_combobox_3.value != "-":
                dataset3 = self.data.hypercubes[self.modes_combobox_3.value]
                self.data.hypercubes["Fused"], self.data.wls["Fused"] = (
                    datasets_fusion(
                        self.data.hypercubes["Fused"],
                        dataset3,
                        self.data.wls["Fused"],
                        wl3,
                        norm=self.modes_fusion.value,
                    )
                )

        show_info("Fusion completed!")
