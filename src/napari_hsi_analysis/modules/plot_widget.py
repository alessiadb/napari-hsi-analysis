""" """

import napari
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
import qtawesome as qta  # Icons
from magicgui.widgets import PushButton
from matplotlib.path import Path
from napari.utils.notifications import show_warning
from qtpy import QtCore
from qtpy.QtWidgets import QFileDialog, QWidget


class PlotWidget(QWidget):
    """Class for the plots"""

    def __init__(self, viewer: napari.Viewer, data):
        """ """
        super().__init__()
        self.viewer = viewer
        self.data = data
        self.poly_roi = None
        self.drawing = False
        self.vertical_line = None
        self.viewer.dims.events.current_step.connect(self.update_line)

    def setup_plot(self, plot, fused=False):
        self.ax = self.ax2 = self.ax3 = None  # Reset of the axis
        plot.figure.patch.set_facecolor("#262930")
        if fused:
            if len(self.data.fusion_modes) > 2:
                self.ax = plot.figure.add_subplot(131)
                self.ax2 = plot.figure.add_subplot(132)
                self.ax3 = plot.figure.add_subplot(133)
            else:
                self.ax = plot.figure.add_subplot(121)
                self.ax2 = plot.figure.add_subplot(122)

        else:
            self.ax = plot.figure.add_subplot(111)
        for ax in [
            self.ax,
            getattr(self, "ax2", None),
            getattr(self, "ax3", None),
        ]:
            if ax is not None:
                ax.set_facecolor("#262930")
                ax.tick_params(axis="x", colors="#D3D4D5", labelsize=14)
                ax.tick_params(axis="y", colors="#D3D4D5", labelsize=14)
                ax.grid(
                    True,
                    linestyle="--",
                    linewidth=0.5,
                    color="#D3D4D5",
                    alpha=0.5,
                )
                for position, spine in ax.spines.items():
                    if position in ["left", "bottom"]:
                        spine.set_color(
                            "#D3D4D5"
                        )  # colore chiaro per sfondo scuro
                        spine.set_linewidth(1)
                        spine.set_visible(True)
                    else:
                        spine.set_visible(False)

    def show_plot(
        self,
        plot,
        mode,
        std_dev_flag=False,
        norm_flag=False,
        reduced_dataset_flag=False,
        from_scatterplot_flag=False,
        export_txt_flag=False,
        derivative_flag=False,
    ):

        selected_layer = self.viewer.layers.selection.active

        if not isinstance(selected_layer, napari.layers.Labels):
            show_warning(
                "⚠️ The selected layer is not a label layer. Please, select a label layer."
            )
            return

        # Clean and reset the plot
        fig = plot.figure
        fig.clf()
        # FUSED:
        self.setup_plot(plot, fused=(mode == "Fused"))
        ax_der = (
            self.ax.twinx() if derivative_flag and mode != "Fused" else None
        )
        if ax_der:  # If derivative, create new ax
            ax_der = self.ax.twinx()
            ax_der.tick_params(axis="y", colors="#FFA500", labelsize=14)
            ax_der.spines["right"].set_color("#FFA500")
            ax_der.set_ylabel("Derivative", color="#FFA500")

        # SELECT LABEL LAYER
        # takes all the layers but the seleciton is only in the image (WL) in which i've done it
        labels_layer = self.viewer.layers.selection.active.data
        # If coming from UMAP, we don't need to do np.sum
        labels_layer_mask = (
            labels_layer
            if from_scatterplot_flag
            else np.sum(labels_layer, axis=0)
        )

        # COLORMAP
        colormap = np.array(
            self.viewer.layers.selection.active.colormap.colors
        )
        num_classes = int(labels_layer_mask.max())
        wavelengths = self.data.wls[mode]

        # Compute spectra and derivatives
        spectra, stds, spectra_der, stds_der = self.compute_spectra(
            wavelengths,
            labels_layer_mask,
            mode,
            reduced_dataset_flag,
            num_classes,
            norm_flag,
            derivative_flag,
        )

        # PLOT SPECTRA
        for index in range(num_classes):

            color = colormap[index + 1, :3]
            # Fused mode
            if mode == "Fused":
                self.plot_fused(index, spectra, stds, color, std_dev_flag)
            else:
                # Plot detivative if requested
                if derivative_flag and ax_der is not None:
                    self.plot_with_std(
                        ax_der,
                        wavelengths,
                        spectra_der[index],
                        stds_der[index] if std_dev_flag else None,
                        color,
                        linestyle="--",
                    )
                self.plot_with_std(
                    self.ax,
                    wavelengths,
                    spectra[index],
                    stds[index] if std_dev_flag else None,
                    color,
                )

        if export_txt_flag:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save spectra in .txt", "", "txt (*.txt)"
            )
            if filename:
                self.export_spectra_txt(filename, wavelengths, spectra, stds)

        plot.draw()

    def compute_spectra(
        self,
        wavelengths,
        mask,
        mode,
        reduced_flag,
        num_classes,
        normalize_flag,
        derivative_flag,
    ):
        """Compute mean and std of spectra (and derivative if requested)."""
        wl_len = wavelengths.shape[0]
        spectra = np.zeros((num_classes, wl_len))
        stds = np.zeros((num_classes, wl_len))
        spectra_der = np.zeros_like(spectra)
        stds_der = np.zeros_like(stds)

        for idx in range(num_classes):
            points = np.array(np.where(mask == idx + 1))

            # Handle Fused outside
            if mode == "Fused":
                mode1, mode2 = self.data.fusion_modes[:2]
                if reduced_flag:
                    if (
                        self.data.hypercubes_spatial_red.get("Fused")
                        is not None
                    ):
                        cube = self.data.hypercubes_spatial_red
                    else:
                        cube = self.data.hypercubes_red
                else:
                    cube = self.data.hypercubes

                data1 = cube[mode1][points[0], points[1], :]
                data2 = cube[mode2][points[0], points[1], :]
                print(data1.shape)
                data_selected = np.concatenate((data1, data2), axis=1)
                print(data_selected.shape)
                if len(self.data.fusion_modes) > 2:
                    mode3 = self.data.fusion_modes[2]
                    data3 = cube[mode3][points[0], points[1], :]
                    data_selected = np.concatenate(
                        (data_selected, data3), axis=1
                    )
            else:
                if reduced_flag:
                    if self.data.hypercubes_spatial_red.get(mode) is not None:
                        cube = self.data.hypercubes_spatial_red
                    else:
                        cube = self.data.hypercubes_red
                else:
                    cube = self.data.hypercubes
                data_selected = cube[mode][points[0], points[1], :]

            mean_spec = np.mean(data_selected, axis=0)
            std_spec = np.std(data_selected, axis=0)

            if normalize_flag:
                if mode == "Fused":
                    mean_spec1 = np.mean(data1, axis=0)
                    min_val1, max_val1 = np.min(mean_spec1), np.max(mean_spec1)
                    mean_spec1 = (mean_spec1 - min_val1) / (
                        max_val1 - min_val1
                    )
                    std_spec1 = np.std(data1, axis=0) / (max_val1 - min_val1)

                    mean_spec2 = np.mean(data2, axis=0)
                    min_val2, max_val2 = np.min(mean_spec2), np.max(mean_spec2)
                    mean_spec2 = (mean_spec2 - min_val2) / (
                        max_val2 - min_val2
                    )
                    std_spec2 = np.std(data2, axis=0) / (max_val2 - min_val2)

                    mean_spec = np.concatenate((mean_spec1, mean_spec2))
                    std_spec = np.concatenate((std_spec1, std_spec2))

                    if len(self.data.fusion_modes) > 2:
                        mean_spec3 = np.mean(data3, axis=0)
                        min_val3, max_val3 = np.min(mean_spec3), np.max(
                            mean_spec3
                        )
                        mean_spec3 = (mean_spec3 - min_val3) / (
                            max_val3 - min_val3
                        )
                        std_spec3 = np.std(data3, axis=0) / (
                            max_val3 - min_val3
                        )

                        mean_spec = np.concatenate((mean_spec, mean_spec3))
                        std_spec = np.concatenate((std_spec, std_spec3))

                else:
                    min_val, max_val = np.min(mean_spec), np.max(mean_spec)
                    mean_spec = (mean_spec - min_val) / (max_val - min_val)
                    std_spec = std_spec / (max_val - min_val)

            spectra[idx] = mean_spec
            stds[idx] = std_spec

            if derivative_flag:
                if reduced_flag:
                    if (
                        self.data.hypercubes_spatial_red[mode + " derivative"]
                        is not None
                    ):
                        cube_der = self.data.hypercubes_spatial_red
                    else:
                        cube_der = self.data.hypercubes_red
                else:
                    cube_der = self.data.hypercubes
                data_der = cube_der[mode + " derivative"][
                    points[0], points[1], :
                ]
                spectra_der[idx] = np.mean(data_der, axis=0)
                stds_der[idx] = np.std(data_der, axis=0)

        return spectra, stds, spectra_der, stds_der

    def plot_with_std(self, ax, x, y, std=None, color="blue", linestyle="-"):
        """Plot with optional standard deviation shading."""
        ax.plot(x, y, color=color, linewidth=2, linestyle=linestyle)
        if std is not None:
            ax.fill_between(x, y - std, y + std, color=color, alpha=0.3)

    def plot_fused(self, index, spectra, stds, color, std_dev_checkbox):
        """Handle the plotting of fused datasets."""
        fusion_point = self.data.wls[self.data.fusion_modes[0]].shape[0]
        spectrum_1 = spectra[index, :fusion_point]
        spectrum_2 = spectra[index, fusion_point:]
        std_dev_1 = stds[index, :fusion_point]
        std_dev_2 = stds[index, fusion_point:]

        wls_1 = self.data.wls[self.data.fusion_modes[0]]
        wls_2 = self.data.wls[self.data.fusion_modes[1]]

        if len(self.data.fusion_modes) > 2:
            fusion_point2 = (
                self.data.wls[self.data.fusion_modes[0]].shape[0]
                + self.data.wls[self.data.fusion_modes[1]].shape[0]
            )
            spectrum_2 = spectra[index, fusion_point:fusion_point2]
            spectrum_3 = spectra[index, fusion_point2:]
            std_dev_2 = stds[index, fusion_point:fusion_point2]
            std_dev_3 = stds[index, fusion_point2:]
            wls_3 = self.data.wls[self.data.fusion_modes[2]]
            self.ax3.plot(wls_3, spectrum_3, color=color, linewidth=2)

        self.ax.plot(wls_1, spectrum_1, color=color, linewidth=2)
        self.ax2.plot(wls_2, spectrum_2, color=color, linewidth=2)

        if std_dev_checkbox:
            self.ax.fill_between(
                wls_1,
                spectrum_1 - std_dev_1,
                spectrum_1 + std_dev_1,
                color=color,
                alpha=0.3,
            )
            self.ax2.fill_between(
                wls_2,
                spectrum_2 - std_dev_2,
                spectrum_2 + std_dev_2,
                color=color,
                alpha=0.3,
            )
            if len(self.data.fusion_modes) > 2:
                self.ax3.fill_between(
                    wls_3,
                    spectrum_3 - std_dev_3,
                    spectrum_3 + std_dev_3,
                    color=color,
                    alpha=0.3,
                )

    def export_spectra_txt(self, filename, wavelengths, spectra, stds):
        """Export spectra and standard deviation to TXT."""
        data_to_save = np.column_stack(
            (
                wavelengths,
                *[
                    np.column_stack((spectra[i], stds[i]))
                    for i in range(spectra.shape[0])
                ],
            )
        )

        header = "Wavelength\t" + "\t".join(
            [f"Spectrum{i+1}\tStd{i+1}" for i in range(spectra.shape[0])]
        )

        np.savetxt(
            filename,
            data_to_save,
            fmt="%.6f",
            delimiter="\t",
            header=header,
            comments="",
        )
        # logging.info("Spectra exported successfully to %s", filename)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setup_scatterplot(self, plot):
        """Setup basic scatterplot appearance"""
        plot.setBackground("w")
        for axis in ("left", "bottom"):
            plot.getAxis(axis).setTicks([])
            plot.getAxis(axis).setStyle(tickLength=0)
            plot.getAxis(axis).setPen(None)
        plot.setMinimumSize(400, 400)

    def show_scatterplot(self, plot, data, hex_colors, points, size):
        """Display sctterplot"""
        if hasattr(self, "scatter") and self.scatter:
            plot.removeItem(self.scatter)
        if len(points) > 0:
            self.scatter = pg.ScatterPlotItem(
                pos=data,
                pen=None,
                symbol="o",
                size=size,
                brush=hex_colors[points],
            )
        else:
            self.scatter = pg.ScatterPlotItem(
                pos=data, pen=None, symbol="o", size=size, brush=hex_colors
            )

        plot.addItem(self.scatter)
        plot.getViewBox().autoRange()
        plot.update()

    def polygon_selection(self, plot):
        """Abilita la selezione poligonale sullo scatterplot"""
        self.plot = plot

        # Rimuove ROI esistente se presente
        if self.poly_roi:
            self.plot.removeItem(self.poly_roi)

        self.temp_points = []
        self.poly_roi = pg.PolyLineROI(
            [],
            closed=False,
            pen="r",
            handlePen=pg.mkPen("red"),
        )
        self.plot.addItem(self.poly_roi)

        self.drawing = True
        self.plot.scene().sigMouseClicked.connect(self.add_point_to_polygon)

    def add_point_to_polygon(self, event):
        """Aggiunge punti alla ROI poligonale e aggiorna le linee"""
        if not self.drawing:
            return

        if event.button() == QtCore.Qt.LeftButton:
            pos = self.plot.plotItem.vb.mapSceneToView(event.scenePos())
            point = (pos.x(), pos.y())

            self.temp_points.append(point)
            self.poly_roi.setPoints(self.temp_points)  # aggiorna visivamente

            if event.double():  # chiusura con doppio click
                self.drawing = False
                self.poly_roi.closed = True
                self.poly_roi.setPoints(
                    self.temp_points
                )  # richiude visivamente
                self.plot.scene().sigMouseClicked.disconnect(
                    self.add_point_to_polygon
                )

    """
    def polygon_selection(self, plot):
        self.plot = plot
        if self.poly_roi:  # If polyroi selected, cancel it
            self.plot.removeItem(self.poly_roi)
        self.poly_roi = pg.PolyLineROI(
            [],
            closed=True,
            pen="r",
            handlePen=pg.mkPen("red"),
        )
        self.plot.addItem(self.poly_roi)
        self.drawing = True
        self.plot.scene().sigMouseClicked.connect(self.add_point_to_polygon)

    def add_point_to_polygon(self, event):
        if not self.drawing:
            return
        pos = self.plot.plotItem.vb.mapSceneToView(event.scenePos())
        points = self.poly_roi.getState()["points"]
        points.append([pos.x(), pos.y()])
        self.poly_roi.setPoints(points)
        if event.double():  # Close polygon with double click
            self.drawing = False
            self.plot.scene().sigMouseClicked.disconnect(
                self.add_point_to_polygon
            )
    """

    def show_selected_points(self, scatterdata, hsi_image, mode, points):
        """ """
        if not self.poly_roi:
            print("No active selection!")
            return
        polygon = self.poly_roi.getState()["points"]
        polygon = np.array(polygon)
        path = Path(polygon)
        points_mask = path.contains_points(scatterdata)
        # selected_points = scatterdata[points_mask]
        selected_indices = [
            index for index, value in enumerate(points_mask) if value
        ]
        if len(points) > 0:
            selected_indices = points[selected_indices]

        # print("Punti selezionati:", selected_points)
        # print("Indici selezionati:", selected_indices)
        # CREATION OF LAYER LABELS
        labels = np.zeros(
            (hsi_image.shape[0], hsi_image.shape[1]), dtype=np.int32
        )
        existing_layers = [
            layer
            for layer in self.viewer.layers
            if layer.name == f"{mode} SCATTERPLOT LABELS"
        ]
        if existing_layers:
            labels_layer = existing_layers[0]
            labels = labels_layer.data.copy()
            new_label_value = labels.max() + 1
        else:
            labels_layer = None
            new_label_value = 1

        # LABELS IN THE SELCTED POINTS
        for idx in selected_indices:
            row, col = divmod(idx, hsi_image.shape[1])  # Converted in 2D
            labels[row, col] = new_label_value
        if labels_layer:
            labels_layer.data = labels
            labels_layer.refresh()
        else:
            labels_layer = self.viewer.add_labels(
                labels, name=f"{mode} SCATTERPLOT LABELS"
            )

    def save_image_button(self, plot):
        """ """
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save UMAP image", "", "png (*.png)"
        )
        if filename:
            exporter = pg.exporters.ImageExporter(plot.getPlotItem())
            exporter.parameters()["width"] = 2000
            exporter.parameters()["height"] = 2000
            exporter.export(filename)
            print("Image saved!")

    def create_button(self, icon_name):
        """Create styled icon button"""
        btn = PushButton(text="").native
        btn.setIcon(qta.icon(f"{icon_name}", color="#D3D4D5"))  # Icon
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: #262930; /* Grigio scuro */
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #3E3F40; /* Più chiaro al passaggio del mouse */
            }"""
        )
        btn.setFixedSize(30, 30)  # Dimensione fissa
        return btn

    # ------ NOT USED CODE ------
    def update_line(self, event):  # NON FUNZIONA DA RIVEDERE
        """ """
        if not hasattr(self, "vertical_line") or self.vertical_line is None:
            return
        index = self.viewer.dims.current_step[0]  # Otteniamo l'indice corrente
        wl = self.data.wls[self.data.mode]
        if 0 <= index < len(wl):  # Controlla che sia dentro i limiti
            self.vertical_line.set_xdata([wl[index]])  # Sposta la linea
            self.vertical_line.figure.canvas.draw_idle()

        self.data.wl_value = self.viewer.dims.current_step[0]
        # selected_layer = viewer.layers.selection.active
        self.viewer.text_overlay.text = f"Wavelength: {round(self.data.wls[self.data.mode][self.data.wl_value], 2)} nm \nChannel: {self.data.wl_value}"
        # if "REDUCED" in selected_layer.name:
        #    wl_selected = self.data.wls_red
        #    viewer.text_overlay.text = f"Channel: {round(wl_selected[self.data.mode][self.data.wl_value], 2)}"
        # else:
        #    wl_selected = self.data.wls
        #    viewer.text_overlay.text = f"Wavelength: {round(wl_selected[self.data.mode][self.data.wl_value], 2)} nm"
        # print(self.data.wls[self.data.mode][self.data.wl_value])

    def normalize(channel):
        """ """
        return (channel - np.min(channel)) / (
            np.max(channel) - np.min(channel)
        )

    def customize_toolbar(self, toolbar):
        """Personalizza la toolbar matplotlib: sfondo scuro + icone bianche"""
        # Cambia sfondo della toolbar
        toolbar.setStyleSheet("background-color: #262930; border: none;")

        # Mappa nome azione → nome file icona
        icon_map = {
            "Home": "fa5s.home",
            "Back": "fa5s.arrow-left",
            "Forward": "fa5s.arrow-right",
            "Pan": "fa5s.expand-arrows-alt",
            "Zoom": "ei.zoom-in",
            "Subplots": "msc.settings",
            "Customize": "mdi.chart-scatter-plot",
            "Save": "fa5.save",
        }

        for action in toolbar.actions():
            text = action.text()
            if text in icon_map:
                action.setIcon(qta.icon(f"{icon_map[text]}", color="#D3D4D5"))
