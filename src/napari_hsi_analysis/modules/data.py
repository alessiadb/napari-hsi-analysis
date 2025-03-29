""" """

import sys
from os.path import dirname

sys.path.append(dirname(dirname(__file__)))
import numpy as np
from modules.functions import (
    HSI2RGB,
    PCA_analysis,
    UMAP_analysis,
    dimensionality_reduction,
    open_file,
    preprocessing,
    reduce_spatial_dimension_dwt,
)

# print("here: ", dirname(dirname(__file__)))    #print for the directory folder


class Data:
    """ """

    def __init__(self):
        """ """
        self.filepath = ""
        self.hypercubes = {}
        self.hypercubes_red = {}
        self.hypercubes_spatial_red = {}  # For the spectra
        self.hypercubes_masked = {}
        self.wls = {}
        self.rgb = {}  # Dictionary needed for the fusion process
        self.rgb_red = {}  # Dictionary needed for the fusion process
        self.rgb_masked = {}
        self.wls_red = {}
        self.pca_maps = {}
        self.umap_maps = {}  # valutare se da togliere.
        self.modes = [
            "Reflectance",
            "PL",
            "PL - 2",
            "Reflectance derivative",
            "Fused",
            "-",
        ]  # fused: self.modes.append
        self.mode = None  # valutare se da togliere con nuovo widget
        self.wl_value = 0
        self.fusion_modes = []

    def open_file(self, mode: str, path: str) -> None:
        """ """
        self.mode = mode
        self.hypercubes[self.mode], self.wls[self.mode] = open_file(path)
        self.hypercubes[self.mode] = np.rot90(self.hypercubes[self.mode], k=3)

    def create_rgb_image(
        self, dataset: np.array, wl: np.array, mode: str, reduced=False
    ) -> None:
        """ """
        dataset_reshaped = (
            np.reshape(dataset, [-1, dataset.shape[2]]) / dataset.max()
        )
        self.rgb[mode] = HSI2RGB(
            wl, dataset_reshaped, dataset.shape[0], dataset.shape[1], 65, False
        )

    def create_mask(self, labels_layer_mask, reduced_flag, data_mode):
        """Create mask"""
        binary_mask = np.where(labels_layer_mask == 0, np.nan, 1).astype(float)
        if reduced_flag:
            self.hypercubes_masked[data_mode] = (
                self.hypercubes_red[data_mode] * binary_mask[..., np.newaxis]
            )
            self.rgb_masked[data_mode] = (
                self.rgb_red[data_mode] * binary_mask[..., np.newaxis]
            )
        else:
            self.hypercubes_masked[data_mode] = (
                self.hypercubes[data_mode] * binary_mask[..., np.newaxis]
            )
            self.rgb_masked[data_mode] = (
                self.rgb[data_mode] * binary_mask[..., np.newaxis]
            )

    def processing_data(
        self,
        dataset: np.array,
        mode: str,
        medfilt_checkbox: bool,
        savgol_checkbox: bool,
        medfilt_w: int,
        savgol_w: int,
        savgol_p: int,
    ) -> None:
        """ """
        self.hypercubes[mode] = preprocessing(
            dataset,
            medfilt_w,
            savgol_w,
            savgol_p,
            medfilt_checkbox=medfilt_checkbox,
            savgol_checkbox=savgol_checkbox,
        )
        print(f"Processed dataset of {mode} created")

    def dimensionality_reduction(
        self,
        dataset,
        mode,
        spectral_dimred_checkbox,
        spatial_dimred_checkbox,
        wl,
    ):
        """ """
        (
            self.hypercubes_red[mode],
            self.wls_red[mode],
            self.rgb_red[mode],
        ) = dimensionality_reduction(
            dataset, spectral_dimred_checkbox, spatial_dimred_checkbox, wl
        )
        print(f"Dimensionality of dataset (Mode: {mode}) has been reduced")
        print(f"New channel array of dimension {self.wls_red[mode].shape}")
        print(
            f"New rgb matrix of reduced dataset. Dimensions: {self.rgb_red[mode].shape}"
        )
        if spatial_dimred_checkbox:
            self.hypercubes_spatial_red[mode] = reduce_spatial_dimension_dwt(
                dataset
            )

    def umap_analysis(
        self,
        dataset,
        mode,
        downsampling,
        metric,
        n_neighbors,
        min_dist,
        points,
    ):
        """ """

        self.umap_maps[mode] = UMAP_analysis(
            dataset,
            downsampling=downsampling,
            points=points,
            metric=metric,
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            random_state=42,
        )
        # print(self.umap_maps[mode].shape)

    def pca_analysis(self, dataset, mode, n_components):
        """ """
        self.pca_maps[mode], W = PCA_analysis(dataset, n_components)
        # print(self.pca_maps[mode].shape)
