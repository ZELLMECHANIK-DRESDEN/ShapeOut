.. _sec_qg_batch_stats:


==============================
Batch-mode statistical summary
==============================

.. image:: scrots/qg_batch_statistics.png
    :target: _images/qg_batch_statistics.png
    :align: right
    :scale: 50%

The Statistical information of the current analysis is displayed in the
:ref:`Statistics configuration tab <sec_ui_cfg_statistics>` and can also
be exported via the `Export Data` menu.

With the statistical summary tool (accessible via the menu
*Batch* → *Statistical summary*), you may compute the statistics
for multiple measurements on disk, without loading them into an
analysis session in Shape-Out:

1. Select the filter settings to use. At the time of this writing,
   only the filter settings of a measurement in the current session can be used.

2. Click *Browse* to select an input folder that contains RT-DC measurement
   data. This folder will be recursively searched for measurements (\*.tdms
   and \*.rtdc files). The number of measurements found is then shown in
   the dropdown box below.

3. If applicable, select the flow rate and the chip region for which you
   need the statistics summary.

4. Select the features for which to compute the statistics and the
   statistical parameters to extract.

5. Click *Browse* at the bottom to select the output file and click on
   *Assemble statistical summary* to start the computation.

Note that depending on the number of measurements and on the data type
(\*.rtdc data is loaded faster than \*.tdms data), the computation may
take some time.
