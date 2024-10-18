# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ReservoirAndBasinAnalysis
                                 A QGIS plugin
 This plugin offers some analysis tools for reservoirs.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-07-13
        copyright            : (C) 2024 by João Vitor Pimenta
        email                : jvpjoaopimenta@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'João Vitor Pimenta'
__date__ = '2024-07-13'
__copyright__ = '(C) 2024 by João Vitor Pimenta'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingException,
                       QgsProcessingParameterPoint,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterNumber)
from numpy import savetxt
from .algorithms.algorithmGraph import executePluginForArea, executePluginForCoord
import os


class createAreaHeightVolumeGraphAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_DEM = 'INPUT_DEM'
    DRAINAGE_AREA = 'DRAINAGE_AREA'
    INPUT_COORDINATES = 'INPUT_COORDINATES'
    VERTICAL_SPACING = 'VERTICAL_SPACING (m)'
    CSV = 'CSV'
    GRAPH = 'GRAPH'


    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DEM,
                self.tr('DEM'),
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.DRAINAGE_AREA,
                self.tr('Drainage Area'),
                defaultValue=None,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterPoint(
                self.INPUT_COORDINATES,
                'Outlet point coordinates (format: x,y)',
                defaultValue=None,
                optional = True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.VERTICAL_SPACING,
                'Vertical step (in meters):',
                type=QgsProcessingParameterNumber.Double,
                defaultValue='0.00'
            )
        )


        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.CSV,
                self.tr('Data'),
                fileFilter='CSV files (*.csv)'
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.GRAPH,
                self.tr('Graph'),
                fileFilter='HTML files (*.html)'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        demLayer = self.parameterAsRasterLayer(
                                             parameters,
                                             self.INPUT_DEM,
                                             context
                                             )
        coordinates = self.parameterAsPoint(
                                            parameters,
                                            self.INPUT_COORDINATES,
                                            context
                                            )
        drainageAreaInput = self.parameterAsVectorLayer(
                                                        parameters,
                                                        self.DRAINAGE_AREA,
                                                        context
                                                        )
        verticalSpacingInput = self.parameterAsDouble(
                                                        parameters,
                                                        self.VERTICAL_SPACING,
                                                        context
                                                        )
        # Compute the number of steps to display within the progress bar and
        # get features from source
        if verticalSpacingInput <0:
            raise QgsProcessingException(
                'Vertical spacing needs be positive!'
                                         )
        demLayerExt = demLayer.extent()

        if drainageAreaInput is not None:
            AHV, graph = executePluginForArea(demLayer,
                                        drainageAreaInput,
                                        verticalSpacingInput)
        if not coordinates.isEmpty():
            if demLayerExt.contains(coordinates) is False:
                raise QgsProcessingException(
                "The point coordinates must be in the DEM extension!"
                )
            x = coordinates.x()
            y = coordinates.y()
            AHV, graph = executePluginForCoord(demLayer,
                                                x,y,
                                                verticalSpacingInput)


        (AHVdata) = self.parameterAsFileOutput(parameters, self.CSV,
                context)

        savetxt(
                AHVdata,
                AHV,
                delimiter=',',
                header='Area (m2),Height (m),Volume (m3)',
                comments='',
                fmt='%s'
                )


        graphOutput = self.parameterAsFileOutput(parameters, self.GRAPH,
                context)
        graph.write_html(graphOutput)




        return {self.CSV:AHVdata,
                self.GRAPH:graphOutput}



    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Create a graph'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Reservoir tools'

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QIcon(os.path.join(os.path.dirname(__file__), "icons", "icon.png"))

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return createAreaHeightVolumeGraphAlgorithm()
