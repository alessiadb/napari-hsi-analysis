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
)

print("here: ", dirname(dirname(__file__)))


class Data:
    """ """

    def __init__(self):
        """ """
        self.filepath = ""
        self.hypercubes = {}
        self.wls = {}
        self.rgb = {}
        self.rgb_red = {}
        self.hypercubes_processed = {}
        self.hypercubes_processed_red = {}
        self.wls_red = {}
        self.pca_maps = {}
        self.umap_maps = {}
        self.modes = [
            "Reflectance",
            "PL",
            "Reflectance derivative",
        ]  # per i fused: self.modes.append
        self.mode = None
        self.wl_value = 0

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
        self.hypercubes_processed[mode] = preprocessing(
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
            self.hypercubes_processed_red[mode],
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

    def umap_analysis(
        self, dataset, mode, downsampling, metric, n_neighbors, min_dist
    ):
        """ """
        self.umap_maps[mode] = UMAP_analysis(
            dataset,
            downsampling=downsampling,
            points=[],
            metric=metric,
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            random_state=42,
        )
        print(self.umap_maps[mode].shape)

    def pca_analysis(self, dataset, mode, n_components):
        """ """
        self.pca_maps[mode], W = PCA_analysis(dataset, n_components)
        print(self.pca_maps[mode].shape)
