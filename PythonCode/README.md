You should first refer to the git https://github.com/Originate/dbg-pds-tensorflow-demo in order to create folders deutsche-boerse-eurex-pds and deutsche-boerse-xetra-pds with raw options and stock intraday data.

Then you will be able to execute the main.py script which will fetch some parameters in SetUp.py.
- GetRawData is a simple code to extract 2 dataframes from mutilple DPS files : /processed/Execs_DAI.pkl and /processed/UDL_DAI.pkl
- PricingAndCalibration will calibrate the model and create parameters dataframe : /parameters/Parameters_DAI.pkl (an example of this file is provided in the Output folder)
- BuildInputs will interpolate the parameters to give clean inputs : /parameters/Inputs_DAI
