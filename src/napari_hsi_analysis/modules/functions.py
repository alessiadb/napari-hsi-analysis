""" """

import os
import time
from bisect import bisect  # RGB

import h5py
import numpy as np
import plotly.graph_objects as go
import pywt  # DIMENSIONALITY REDUCTION
import scipy.io as spio  # RGB
import umap
from scipy.interpolate import PchipInterpolator  # RGB
from scipy.io import loadmat
from scipy.signal import medfilt2d, savgol_filter
from sklearn.decomposition import PCA


def open_file(filepath):
    """ """
    file_extension = filepath.split(".")[-1].lower()
    if file_extension not in ["mat", "h5"]:
        print(
            f"Error: file format not supported. Expected .mat o .h5, found .{file_extension}."
        )
        return None, None

    hypercube_names = [
        "data",
        "data_RIFLE",
        "Y",
        "Hyperspectrum_cube",
        "XRFdata",
        "spectra",
        "HyperMatrix",
    ]
    wls_names = [
        "WL",
        "WL_RIFLE",
        "X",
        "fr_real",
        "spectra",
        "wavelength",
        "ENERGY",
        "t",
    ]

    data = None
    wl = None

    # if .mat file
    if file_extension == "mat":
        f = loadmat(filepath)
        print("Dataset presents (MATLAB file):")
        for dataset_name in f:
            print(dataset_name)
            if dataset_name in hypercube_names:
                data = np.array(f[dataset_name])
                if dataset_name == "Hyperspectrum_cube":
                    data = data[:, :, ::-1]
                data = np.rot90(data, k=3, axes=(0, 1))
                data = data[:, ::-1, :]
            if dataset_name in wls_names:
                wl = np.array(f[dataset_name]).flatten()
                if dataset_name == "fr_real":
                    wl = 3 * 10**5 / wl
                    wl = wl[::-1]
        if data is not None and wl is not None:
            print("Data shape:", data.shape, "\nWL shape:", wl.shape)
            return data, wl
        else:
            print("ERROR: the .mat file does not contain correct datas.")
            return None, None

    # If .h5 file
    elif file_extension == "h5":
        with h5py.File(filepath, "r") as f:
            print("Dataset presents (HDF5 file):")
            for dataset_name in f:
                print(dataset_name)
                if dataset_name in hypercube_names:
                    data = np.array(f[dataset_name])
                    if dataset_name == "Hyperspectrum_cube":
                        data = data[:, :, ::-1]
                if dataset_name in wls_names:
                    wl = np.array(f[dataset_name]).flatten()
                    if dataset_name == "fr_real":
                        wl = 3 * 10**5 / wl
                        wl = wl[::-1]
        if data is not None and wl is not None:
            print("Data shape:", data.shape, "\nWL shape:", wl.shape)
            return data, wl
        else:
            print("ERROR: the .h5 file does not contain correct datas.")
            return None, None


# WE ARE USING IT?
def plotSpectra(data, label, wl):
    """ """
    dataMasked = np.einsum("ijk,jk->ijk", data, label)
    dataSum = np.sum(
        dataMasked.reshape(
            dataMasked.shape[0], dataMasked.shape[1] * dataMasked.shape[2]
        ),
        1,
    )
    print(dataSum)
    return dataSum


# %% NORMALIZATION
def normalize(channel):
    """ """
    return (channel - np.min(channel)) / (np.max(channel) - np.min(channel))


# %% CREATE RGB
def HSI2RGB(wY, HSI, ydim, xdim, d, threshold):
    """ """
    # wY: wavelengths in nm
    # Y : HSI as a (#pixels x #bands) matrix,
    # dims: x & y dimension of image
    # d: 50, 55, 65, 75, determines the illuminant used, if in doubt use d65
    # thresholdRGB : True if thesholding should be done to increase contrast
    #
    #
    # If you use this method, please cite the following paper:
    #  M. Magnusson, J. Sigurdsson, S. E. Armansson, M. O. Ulfarsson,
    #  H. Deborah and J. R. Sveinsson,
    #  "Creating RGB Images from Hyperspectral Images Using a Color Matching Function",
    #  IEEE International Geoscience and Remote Sensing Symposium, Virtual Symposium, 2020
    #
    #  @INPROCEEDINGS{hsi2rgb,
    #  author={M. {Magnusson} and J. {Sigurdsson} and S. E. {Armansson}
    #  and M. O. {Ulfarsson} and H. {Deborah} and J. R. {Sveinsson}},
    #  booktitle={IEEE International Geoscience and Remote Sensing Symposium},
    #  title={Creating {RGB} Images from Hyperspectral Images using a Color Matching Function},
    #  year={2020}, volume={}, number={}, pages={}}
    #
    # Paper is available at
    # https://www.researchgate.net/profile/Jakob_Sigurdsson

    # Load reference illuminant
    file_path = os.path.join(os.path.dirname(__file__), "D_illuminants.mat")
    D = spio.loadmat(file_path)
    # D = spio.loadmat(
    #    r"C:\Users\User\OneDrive - Politecnico di Milano\PhD\Programmi\Pyhton\ANALISI\D_illuminants.mat"
    # )
    w = D["wxyz"][:, 0]
    x = D["wxyz"][:, 1]
    y = D["wxyz"][:, 2]
    z = D["wxyz"][:, 3]
    D = D["D"]

    i = {50: 2, 55: 3, 65: 1, 75: 4}
    wI = D[:, 0]
    I_matrix = D[:, i[d]]

    # Interpolate to image wavelengths
    I_matrix = PchipInterpolator(wI, I_matrix, extrapolate=True)(
        wY
    )  # interp1(wI,I,wY,'pchip','extrap')';
    x = PchipInterpolator(w, x, extrapolate=True)(
        wY
    )  # interp1(w,x,wY,'pchip','extrap')';
    y = PchipInterpolator(w, y, extrapolate=True)(
        wY
    )  # interp1(w,y,wY,'pchip','extrap')';
    z = PchipInterpolator(w, z, extrapolate=True)(
        wY
    )  # interp1(w,z,wY,'pchip','extrap')';

    # Truncate at 780nm
    i = bisect(wY, 780)
    HSI = HSI[:, 0:i] / HSI.max()
    wY = wY[:i]
    I_matrix = I_matrix[:i]
    x = x[:i]
    y = y[:i]
    z = z[:i]

    # Compute k
    k = 1 / np.trapz(y * I_matrix, wY)

    # Compute X,Y & Z for image
    X = k * np.trapz(HSI @ np.diag(I_matrix * x), wY, axis=1)
    Z = k * np.trapz(HSI @ np.diag(I_matrix * z), wY, axis=1)
    Y = k * np.trapz(HSI @ np.diag(I_matrix * y), wY, axis=1)

    XYZ = np.array([X, Y, Z])

    # Convert to RGB
    M = np.array(
        [
            [3.2404542, -1.5371385, -0.4985314],
            [-0.9692660, 1.8760108, 0.0415560],
            [0.0556434, -0.2040259, 1.0572252],
        ]
    )
    sRGB = M @ XYZ

    # Gamma correction
    gamma_map = sRGB > 0.0031308
    sRGB[gamma_map] = 1.055 * np.power(sRGB[gamma_map], (1.0 / 2.4)) - 0.055
    sRGB[np.invert(gamma_map)] = 12.92 * sRGB[np.invert(gamma_map)]
    # Note: RL, GL or BL values less than 0 or greater than 1 are clipped to 0 and 1.
    sRGB[sRGB > 1] = 1
    sRGB[sRGB < 0] = 0

    if threshold:
        for idx in range(3):
            y = sRGB[idx, :]
            a, b = np.histogram(y, 100)
            b = b[:-1] + np.diff(b) / 2
            a = np.cumsum(a) / np.sum(a)
            th = b[0]
            i = a < threshold
            if i.any():
                th = b[i][-1]
            y = y - th
            y[y < 0] = 0

            a, b = np.histogram(y, 100)
            b = b[:-1] + np.diff(b) / 2
            a = np.cumsum(a) / np.sum(a)
            i = a > 1 - threshold
            th = b[i][0]
            y[y > th] = th
            y = y / th
            sRGB[idx, :] = y

    R = np.reshape(sRGB[0, :], [ydim, xdim])
    G = np.reshape(sRGB[1, :], [ydim, xdim])
    B = np.reshape(sRGB[2, :], [ydim, xdim])
    return np.transpose(np.array([R, G, B]), [1, 2, 0])


# %% RGB TO HEX: create a matrix with hex strings of rgb in that pixel
def RGB_to_hex(RGB_image, brightness_factor=1.1):
    """ """
    RGB_image = np.clip(RGB_image * brightness_factor, 0, 1)
    image_scaled = (RGB_image * 255).astype(int)
    hex_matrix = np.apply_along_axis(
        lambda rgb: "#{:02x}{:02x}{:02x}".format(*rgb),
        axis=2,
        arr=image_scaled,
    )
    return hex_matrix


# %% FALSE RGB:
def falseRGB(data, wl, R, G, B):
    """ """
    R = np.array(R)
    G = np.array(G)
    B = np.array(B)
    R_image = np.mean(
        data[
            :,
            :,
            (np.abs(wl - R[0])).argmin() : (np.abs(wl - R[1])).argmin() + 1,
        ],
        axis=2,
    )
    G_image = np.mean(
        data[
            :,
            :,
            (np.abs(wl - G[0])).argmin() : (np.abs(wl - G[1])).argmin() + 1,
        ],
        axis=2,
    )
    B_image = np.mean(
        data[
            :,
            :,
            (np.abs(wl - B[0])).argmin() : (np.abs(wl - B[1])).argmin() + 1,
        ],
        axis=2,
    )
    R_image = normalize(R_image)
    G_image = normalize(G_image)
    B_image = normalize(B_image)
    rgb_image = np.stack([R_image, G_image, B_image], axis=-1)
    rgb_uint8 = (rgb_image * 255).astype(np.uint8)
    return rgb_uint8


# %% PREPROCESSING
def preprocessing(
    data,
    medfilt_w,
    savgol_w,
    savgol_pol,
    medfilt_checkbox=True,
    savgol_checkbox=True,
):
    """ """
    data_processed = data
    print("Data is now data_processed")
    if savgol_checkbox:
        print(
            "Doing Savitzki-Golay filter: Window=",
            str(savgol_w),
            " Polynomial: ",
            str(savgol_pol),
        )
        data_processed = savgol_filter(
            data_processed, savgol_w, savgol_pol, axis=2
        )

    if medfilt_checkbox:
        print("Doing medfilt with window: " + str(medfilt_w))
        for i in range(data_processed.shape[2]):
            data_processed[:, :, i] = abs(
                medfilt2d(data_processed[:, :, i], medfilt_w)
            )

    return data_processed


# %% DIMENSIONALITY REDUCTION
# SPATIAL DIMENSION WITH DWT
def reduce_spatial_dimension_dwt(hsi_cube, wavelet="haar", level=1):
    """ """
    H, W, B = hsi_cube.shape
    reduced_cube = []

    for b in range(B):  # Iterations on spectral bands
        # 2D DWT ats each band
        coeffs2 = pywt.wavedec2(
            hsi_cube[:, :, b], wavelet=wavelet, level=level
        )
        LL, (LH, HL, HH) = coeffs2
        reduced_cube.append(LL)

    # The list converted in a cube
    reduced_cube = np.stack(reduced_cube, axis=-1)
    return reduced_cube


# SPECTRAL DIMENSION WITH DWT
def reduce_bands_with_dwt(hsi_data, wavelet="db1", level=2):
    """ """
    h, w, b = hsi_data.shape
    approx_bands = []

    # Iteration on spatial pixels
    for i in range(h):
        for j in range(w):
            # DWT along spectral bands
            coeffs = pywt.wavedec(
                hsi_data[i, j, :], wavelet=wavelet, level=level
            )
            approx = coeffs[0]
            approx_bands.append(approx)

    # The list converted in a cube
    approx_bands = np.array(approx_bands)
    b_reduced = approx_bands.shape[1]
    reduced_hsi = approx_bands.reshape(h, w, b_reduced) / level

    return reduced_hsi


# TOTAL DIMENSIONALITY REDUCTION
def dimensionality_reduction(
    data, spectral_dimred_checkbox, spatial_dimred_checkbox, wl
):
    """ """
    reduced_data = data
    if spatial_dimred_checkbox:
        reduced_data = reduce_spatial_dimension_dwt(reduced_data)
        reduced_data = reduced_data / 2
        dataset_reshaped = (
            np.reshape(reduced_data, [-1, reduced_data.shape[2]])
            / reduced_data.max()
        )

        reduced_rgb = HSI2RGB(
            wl,
            dataset_reshaped,
            reduced_data.shape[0],
            reduced_data.shape[1],
            65,
            False,
        )
    if spectral_dimred_checkbox:
        reduced_data = reduce_bands_with_dwt(reduced_data)
    print("Original dimensions of the hypercube:", data.shape)
    print("Reduced dimensions of the reduced hypercube:", reduced_data.shape)
    reduced_wl = np.arange(reduced_data.shape[2])
    return reduced_data, reduced_wl, reduced_rgb


# %% DERIVATIVE
def derivative(data, savgol_w=9, savgol_pol=3, deriv=1):
    """ """
    data_firstDev = np.zeros_like(data)
    print(
        "Doing Savitzki-Golay filter: Window=",
        str(savgol_w),
        " Polynomial: ",
        str(savgol_pol),
        " Derivarive: ",
        str(deriv),
    )
    data_firstDev = savgol_filter(
        data, savgol_w, savgol_pol, deriv=deriv, axis=2
    )

    return data_firstDev


# %% FUSION
def datasets_fusion(data1, data2, wl1, wl2, norm="l2"):
    """ """
    print(
        f"Dimensions of dataset 1 and 2: \nData1: {data1.shape} \nData2: {data2.shape} \n\n"
    )
    data1_reshaped = data1.reshape(-1, data1.shape[2])
    data2_reshaped = data2.reshape(-1, data2.shape[2])
    if norm == "l2":
        corr1 = np.linalg.norm(data1_reshaped, ord=None)
        corr2 = np.linalg.norm(data2_reshaped, ord=None)
        print(
            f"Norms for dataset 1 and 2: \nData1: {corr1} \nData2: {corr2} \n\n"
        )
        data1_reshaped = data1_reshaped / corr1
        data2_reshaped = data2_reshaped / corr2

    if norm == "std":
        # scaler1 = StandardScaler()
        # scaler2 = StandardScaler()
        # data1_reshaped = scaler1.fit_transform(data1_reshaped)
        # data2_reshaped = scaler2.fit_transform(data2_reshaped)
        data1_reshaped = (data1_reshaped - np.mean(data1_reshaped)) / np.std(
            data1_reshaped
        )
        data2_reshaped = (data2_reshaped - np.mean(data2_reshaped)) / np.std(
            data2_reshaped
        )
        print(np.mean(data1_reshaped).shape)

    data1 = data1_reshaped.reshape(data1.shape[0], data1.shape[1], -1)
    data2 = data2_reshaped.reshape(data2.shape[0], data2.shape[1], -1)

    wl_fused = np.concatenate((wl1, wl2))
    data_fused = np.concatenate((data1, data2), axis=2)
    fusion_point = data1.shape[2]
    print(
        f"The new dataset has the shape: {data_fused.shape} \nThe fusion point is: {fusion_point}"
    )

    return data_fused, wl_fused


# %% ----- ----- ----- ----- ANALYSIS ----- ----- ----- -----


# %% PCA
def PCA_analysis(data, n_components, points=None, variance=False):
    """ """
    if points is None:
        points = []

    data_reshaped = data.reshape(data.shape[0] * data.shape[1], -1)
    pca = PCA(n_components)

    if len(points) > 0:
        pca.fit(data_reshaped[points, :])
        H = np.zeros((data.shape[0] * data.shape[1], n_components))
        H_reduced = pca.transform(data_reshaped[points, :])
        for i in range(n_components):
            H[points, i] = H_reduced[:, i]
        H = H.reshape(data.shape[0], data.shape[1], n_components)
    else:
        pca.fit(data_reshaped)
        H = pca.transform(data_reshaped).reshape(
            data.shape[0], data.shape[1], n_components
        )
    W = pca.components_  # EIGENVECTORS
    print("W shape: ", W.shape, "H shape: ", H.shape)
    print("Variance: ", pca.explained_variance_)

    if variance:
        cum_explained_var = []
        for i in range(len(pca.explained_variance_ratio_)):
            if i == 0:
                cum_explained_var.append(pca.explained_variance_ratio_[i])
            else:
                cum_explained_var.append(
                    pca.explained_variance_ratio_[i] + cum_explained_var[i - 1]
                )
        print(cum_explained_var)

        wl = np.arange(n_components)
        line = np.zeros_like(wl)
        line = np.full(n_components, 0.95)

        plot = go.Figure()
        plot.add_trace(
            go.Scatter(
                x=wl,
                y=cum_explained_var,
                marker={"size": 5},
                mode="markers",
                showlegend=False,
            )
        )
        plot.add_trace(
            go.Scatter(
                x=wl,
                y=line,
                line={"width": 1, "color": "red"},
                marker={"size": 5},
                mode="lines",
                name="95%",
            )
        )
        plot.update_layout(
            {
                "plot_bgcolor": "rgba(0, 0, 0, 0)",
                "paper_bgcolor": "rgba(0, 0, 0, 0)",
            },
            width=1000,
            height=600,
            xaxis_title="Number of components",
            yaxis_title="Contribution to toal variance",
            yaxis_range=[0.8, 1.01],
        )

        plot.show()
        return H, W, cum_explained_var
    else:
        return H, W


# %% UMAP
def UMAP_analysis(
    data,
    downsampling=1,
    points=None,
    metric="euclidean",
    n_neighbors=20,
    min_dist=0.0,
    random_state=42,
):
    """ """
    if points is None:
        points = []
    start_time = time.time()  # Start of the timer

    if downsampling != 1:
        data = data[0::downsampling, 0::downsampling, :]
        print("Data downsampled dimesnion: ", data.shape)

    data_reshaped = data.reshape(data.shape[0] * data.shape[1], -1)
    print("Data reshaped dimension: ", data_reshaped.shape)

    fit = umap.UMAP(
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        n_components=2,
        metric=metric,
        n_jobs=-1,
    )
    # output_metric='hyperboloid',)
    if len(points) > 0:
        umap_result = fit.fit_transform(data_reshaped[points, :])
    else:
        umap_result = fit.fit_transform(data_reshaped)
    print("UMAP result dimension: ", umap_result.shape)
    elapsed_time = time.time() - start_time
    print(f"Time: {elapsed_time:.2f} seconds")

    return umap_result
