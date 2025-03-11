""" """

import napari
import numpy as np
import pyqtgraph as pg
import qtawesome as qta  # Icons
from magicgui.widgets import PushButton
from matplotlib.path import Path
from qtpy.QtWidgets import QFileDialog, QWidget


class PlotWidget(QWidget):
    """ """

    def __init__(self, viewer: napari.Viewer, data):
        """ """
        super().__init__()
        self.viewer = viewer
        self.data = data
        self.poly_roi = None
        self.drawing = False
        self.vertical_line = None
        self.viewer.dims.events.current_step.connect(self.update_line)

    def setup_plot(self, plot):  # Configure the plot aspect
        """ """
        plot.figure.patch.set_facecolor("#262930")
        self.ax = plot.figure.add_subplot(111)  # Un solo subplot
        self.ax.set_facecolor("#262930")
        self.ax.tick_params(axis="x", colors="#D3D4D5", labelsize=14)
        self.ax.tick_params(axis="y", colors="#D3D4D5", labelsize=14)
        self.ax.grid(
            True, linestyle="--", linewidth=0.5, color="#D3D4D5", alpha=0.5
        )
        for spine in self.ax.spines.values():
            spine.set_color("#D3D4D5")

    def show_plot(
        self,
        plot,
        mode,
        std_dev_checkbox=False,
        norm_checkbox=False,
        reduced_dataset=False,
        from_scatterplot=False,
        export_txt=False,
        derivative=False,
    ):
        """ """
        labels_layer = (
            self.viewer.layers.selection.active.data
        )  # prende tutti i layer ma la selection è solo nell'immagine in cui l'ho fatto: serve np.sum
        if from_scatterplot:
            labels_layer_mask = labels_layer
        else:
            labels_layer_mask = np.sum(labels_layer, axis=0)
        self.ax.clear()  # Pulisce il plot
        if hasattr(self, "ax2"):
            self.ax2.clear()
        colormap = np.array(
            self.viewer.layers.selection.active.colormap.colors
        )

        print(self.data.wls[mode].shape[0])
        spectrum = np.zeros(
            (labels_layer_mask.max(), self.data.wls[mode].shape[0])
        )
        std_dev = np.zeros(
            (labels_layer_mask.max(), self.data.wls[mode].shape[0])
        )
        spectrum_der = np.zeros_like(spectrum)
        std_dev_der = np.zeros_like(std_dev)

        if derivative:
            self.ax2 = self.ax.twinx()
            self.ax2.tick_params(
                axis="y", colors="#FFA500", labelsize=14
            )  # Secondo asse Y con colore differente
            # Imposta i colori delle spine del secondo asse Y
            self.ax2.spines["right"].set_color(
                "#FFA500"
            )  # Solo il bordo destro
            self.ax2.set_ylabel("Derivative", color="#FFA500")

        for index in range(1, labels_layer_mask.max() + 1, 1):
            points = np.array(np.where(labels_layer_mask == index))
            print(points.shape)

            if reduced_dataset:
                data_selected = self.data.hypercubes_processed_red[mode][
                    points[0], points[1], :
                ]
            elif mode not in self.data.hypercubes_processed:
                data_selected = self.data.hypercubes[mode][
                    points[0], points[1], :
                ]
            else:
                data_selected = self.data.hypercubes_processed[mode][
                    points[0], points[1], :
                ]

            spectrum[index - 1, :] = np.mean(
                data_selected, axis=0
            )  # diventa un unico array dove 0 sono i pixel e 1 le wl
            std_dev[index - 1, :] = np.std(data_selected, axis=0)

            if norm_checkbox:
                print("Performin normalization")
                spectrum[index - 1, :] = (
                    spectrum[index - 1, :] - np.min(spectrum[index - 1, :])
                ) / (
                    np.max(spectrum[index - 1, :])
                    - np.min(spectrum[index - 1, :])
                )
                std_dev[index - 1, :] = std_dev[index - 1, :] / (
                    np.max(spectrum[index - 1, :])
                    - np.min(spectrum[index - 1, :])
                )

            if derivative:
                if reduced_dataset:
                    data_selected_der = self.data.hypercubes_processed_red[
                        mode + " derivative"
                    ][points[0], points[1], :]
                elif (
                    mode + " derivative" not in self.data.hypercubes_processed
                ):
                    data_selected_der = self.data.hypercubes[
                        mode + " derivative"
                    ][points[0], points[1], :]
                else:
                    data_selected_der = self.data.hypercubes_processed[
                        mode + " derivative"
                    ][points[0], points[1], :]

                spectrum_der[index - 1, :] = np.mean(
                    data_selected_der, axis=0
                )  # diventa un unico array dove 0 sono i pixel e 1 le wl
                std_dev_der[index - 1, :] = np.std(data_selected_der, axis=0)
                self.ax2.plot(
                    self.data.wls[mode],
                    spectrum_der[index - 1, :],
                    color=colormap[index, :3],
                    linewidth=2,
                    linestyle="--",
                )
                if std_dev_checkbox:
                    self.ax2.fill_between(
                        self.data.wls[mode],
                        spectrum_der[index - 1, :] - std_dev_der[index - 1, :],
                        spectrum_der[index - 1, :] + std_dev_der[index - 1, :],
                        color=colormap[index, :3],
                        alpha=0.3,
                    )

            if std_dev_checkbox:
                self.ax.fill_between(
                    self.data.wls[mode],
                    spectrum[index - 1, :] - std_dev[index - 1, :],
                    spectrum[index - 1, :] + std_dev[index - 1, :],
                    color=colormap[index, :3],
                    alpha=0.3,
                )

            self.ax.plot(
                self.data.wls[mode],
                spectrum[index - 1, :],
                color=colormap[index, :3],
                linewidth=2,
            )

        if derivative:
            self.ax2.set_ylim(
                spectrum_der.min() - std_dev_der.min(),
                spectrum_der.max() + std_dev_der.max(),
            )

        if export_txt:
            data_to_be_saved = np.column_stack((self.data.wls[mode],))
            for i in range(spectrum.shape[0]):
                data_to_be_saved = np.column_stack(
                    (data_to_be_saved, spectrum[i, :], std_dev[i, :])
                )
            # filename = self.data.filepath[:-4]+"_"+str(mode)+"_SPECTRA.txt"
            filename, _ = QFileDialog.getSaveFileName(
                self, "Save spectra in .txt", "", "txt (*.txt)"
            )
            if filename:  # Se l'utente ha scelto un file
                np.savetxt(
                    filename,
                    data_to_be_saved,
                    fmt="%.6f",
                    delimiter="\t",
                    header="Wavelength\t"
                    + "\t".join(
                        [
                            f"Spectrum{i+1}\tStd{i+1}"
                            for i in range(spectrum.shape[0])
                        ]
                    ),
                    comments="",
                )
                print("File salvato con successo!")
                print(
                    "Colormap: ", colormap[1 : labels_layer_mask.max() + 1, :3]
                )

        else:
            plot.draw()  # Forza il refresh del plot

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
        print(self.data.wls[self.data.mode][self.data.wl_value])

    def show_scatterplot(self, plot, data, hex_reshaped):
        """ """
        if hasattr(self, "scatter") and self.scatter is not None:
            plot.removeItem(self.scatter)
        self.scatter = pg.ScatterPlotItem(
            pos=data, pen=None, symbol="o", size=1, brush=hex_reshaped
        )
        # pg.mkBrush(0, 0, 255, 150))
        plot.addItem(self.scatter)
        plot.setBackground("w")
        plot.update()
        plot.getViewBox().autoRange()

    def polygon_selection(self, plot):  # Abilita la selezione poligonale
        """ """
        self.plot = plot
        if self.poly_roi:  # Se è già stata usala la polyroi viene cancellata
            self.plot.removeItem(self.poly_roi)
        self.poly_roi = pg.PolyLineROI([], closed=True, pen="r")
        self.plot.addItem(self.poly_roi)
        self.drawing = True
        self.plot.scene().sigMouseClicked.connect(self.add_point_to_polygon)

    def add_point_to_polygon(
        self, event
    ):  # Aggiunge il poligono in base all'evento sul mouse
        """ """
        if not self.drawing:
            return
        pos = self.plot.plotItem.vb.mapSceneToView(event.scenePos())
        points = self.poly_roi.getState()["points"]
        points.append([pos.x(), pos.y()])
        self.poly_roi.setPoints(points)
        if event.double():  # Chiude il poligono con doppio clic
            self.drawing = False
            self.plot.scene().sigMouseClicked.disconnect(
                self.add_point_to_polygon
            )

    def print_selected_points(
        self, scatterdata, hsi_image, mode, hex_reshaped, plot
    ):
        """ """
        if not self.poly_roi:
            print("Nessuna selezione attiva.")
            return
        polygon = self.poly_roi.getState()["points"]
        polygon = np.array(polygon)
        path = Path(polygon)
        points_mask = path.contains_points(scatterdata)
        # selected_points = scatterdata[points_mask]
        selected_indices = [
            index for index, value in enumerate(points_mask) if value
        ]
        # print("Punti selezionati:", selected_points)
        # print("Indici selezionati:", selected_indices)
        # CREAZIONE DEL LAYER LABELS
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
            labels = (
                labels_layer.data.copy()
            )  # Copiamo i dati esistenti per aggiornarli
            new_label_value = (
                labels.max() + 1
            )  # Assegniamo un nuovo valore di label
        else:
            labels_layer = None
            new_label_value = 1  # Se non esiste, partiamo da 1

        # AGGIORNAMENTO DELLE LABELS NEI PUNTI SELEZIONATI
        for idx in selected_indices:
            row, col = divmod(
                idx, hsi_image.shape[1]
            )  # Convertiamo indice in coordinate 2D
            labels[row, col] = new_label_value
        if labels_layer:
            labels_layer.data = labels
            labels_layer.refresh()
        else:
            labels_layer = self.viewer.add_labels(
                labels, name=f"{mode} SCATTERPLOT LABELS"
            )
        """
        # AGGIORNAMENTO DELLO SCATTERPLOT CON I COLORI DELLA LABELS
        labels_flat = labels_layer.data.flatten()
        unique_labels = np.unique(labels_flat[labels_flat > 0])  # Escludiamo lo 0

        # Creiamo una mappa colore per ogni label
        colormap = {label: pg.intColor(i, len(unique_labels)) for i, label in enumerate(unique_labels)}

        # Creiamo i colori per lo scatterplot
        point_colors = [colormap[label] if label in colormap else pg.mkBrush(color)
                        for label, color in zip(labels_flat, hex_reshaped)]

        # Aggiorniamo lo scatterplot
        if hasattr(self, "scatter") and self.scatter is not None:
            plot.removeItem(self.scatter)

        self.scatter = pg.ScatterPlotItem(pos=scatterdata, pen=None, symbol='o', size=3, brush=point_colors)
        plot.addItem(self.scatter)
        plot.setBackground('w')
        plot.update()
        plot.getViewBox().autoRange()
        """

    def create_home_button(self, label):
        """ """
        btn = PushButton(text="").native  # Nessun testo
        btn.setIcon(
            qta.icon(f"{label}", color="#D3D4D5")
        )  # Icona con colore personalizzato
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
