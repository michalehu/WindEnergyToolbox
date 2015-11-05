# Contents of WindEnergyToolbox, [wetb](wetb)

### [hawc2](wetb/hawc2) 
- [Hawc2io](wetb/hawc2/Hawc2io.py): Read binary, ascii and flex result files
- [sel_file](wetb/hawc2/sel_file.py): Read/write *.sel (sensor list) files
- [htcfile](wetb/hawc2/htcfile.py): Read/write/manipulate htc files
- [ae_file](wetb/hawc2/ae_file.py): Read AE (aerodynamic blade layout) files
- [pc_file](wetb/hawc2/pc_file.py): Read PC (profile coefficient) files
- [shearfile](wetb/hawc2/shearfile.py): Create user defined shear file
- [at_time_file](wetb/hawc2/at_time_file.py): read at output_at_time files



### [gtsdf](wetb/gtsdf)
General Time Series Data Format, a binary hdf5 data format for storing time series data.
- [gtsdf](wetb/gtsdf/gtsdf.py): read/write/append gtsdf files
- [unix_time](wetb/gtsdf/unix_time.py): convert between datetime and unix time (seconds since 1/1/1970)


### [functions](wetb/functions)
Other functions
- [geometry](wetb/functions/geometry.py): Different kind of geometry conversion functions
- [process_exec](wetb/functions/process_exec.py): Run system command in subprocess
