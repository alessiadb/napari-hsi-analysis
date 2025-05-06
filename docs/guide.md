# napari-hsi-analysis

napari-hsi-analysis is a Napari plugin designed for the analysis of hyperspectral imaging datasets. It allows for data visualization and processing, fusion of registered datasets from different techniques, and UMAP-based analysis.
The plugin features three main tabs: **Data Manager**, **Fusion**, and **UMAP**.

## Data Manager widget
The Data Manager widget is used to load, open and visualize hyperspectral datasets.

### How to open a file
Supported file extensions: '.mat' and '.h5'. The file must contain a hyperspectral cube (3D array) and a calibration array.
The accepted variables names are:
- for the **hyperspectral cube**: 'data', 'data_RIFLE', 'Y', 'Hyperspectrum_cube', 'XRF_data', 'spectra', 'HyperMatrix'.
- for the **calibration array**: 'WL', 'WL_RIFLE', 'X', 'fr_real', 'wavelength', 'ENERGY', 't'.

**Steps**:
1. Choose imaging mode from the dropdown.
2. Click *Open File*.

**Contrast Adjustment**: Use the *layer controls* tab. Click once for single image contrast, or continuous for automatic adjustment across the hypercube.

### Data Manager features
- **Create RGB image**: Generates an RGB image of the hypercube.
- **Create Derivative**: Computes the spectral derivative hypercube. Recommended after preprocessing.
- **Preprocessing**: Offers 2D median and Savitzky-Golay filters. Select desired options, adjust parameters, click *Process data*, and wait for the confirmation message.
- **Dimensionality reduction**: Supports spatial and spectral reduction via Discrete Wavelet Transform (DWT). Select reduction type(s) and click *Reduce data*.

### Cropping the hypercube
1. Select the *Shapes* layer.
2. Use a rectangle tool (**only rectangular shapes are supported**).
3. Click *Crop*.
4. (Optional) Delete the original layer.
**TIP**: Keep the cropping *Shapes* layer if fusing multiple datasets and reuse the same shape on a second registered dataset for identical cropping.


### Create a mask
1. Select the *Labels* layer.
2. Choose selection tool: brush, polygon, or fill bucket.
3. Click *Create Mask*.
**Note**: If you are working on a reduced dataset,enable *From reduced dataset*.


### Plot the mean spectrum
1. Select or create a Labels layer.
2. Highlight the area using a selection tool.
3. Click *Mean spectrum*.
It is possible to select other options: with standard deviation, normalized, derivative (if previously computed).
Enable *Reduced dataset* if working on reduced data.
![raw](https://github.com/alessiadb/napari-hsi-analysis/blob/main/images/MeanSpectrum_GIF.gif)

You can also export spectra as '.txt' using *Export spectra in .txt*.

### Create false RGB
Choose three bands and click *Create False RGB* to generate a false-color image.


## Fusion widget
The Fusion widget combines two or three opened datasets.

### How to fuse datasets
1. Select up to three datasets.
2. Click *Fuse the chosen datasets*. A popup will confirm when the fused dataset is ready.

**Note**: When fusing reduced datasets (recommended for UMAP), ensure all selected datasets are reduced.


## UMAP widget

### How to perform UMAP analysis
1. Enable *Apply to reduced dataset* checkbox if applicable (It is **highly recommended** to first preprocess and then reduce the datasets).

2. Check the parameters (it is recomended to keep the minimum distance at 0, but you can play with the number of neighbours). Chose the metric between euclidean and cosine.

3. Click *Run UMAP*. A popup will notify completion.

4. Click *Show UMAP scatterplot*. You can customize point size.

To select areas, use polygon selection and draw the region (double-click to close). Click the add button to finalize.
The selection creates a label layer usable for spectrum plotting or mask creation.


## Example - Mask from fused dataset
This example demonstrates how areas selected via masks can be re-analyzed with UMAP.
![raw](https://github.com/alessiadb/napari-hsi-analysis/blob/main/images/MASK_GIF.gif)
