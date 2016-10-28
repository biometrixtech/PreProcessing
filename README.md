### PreProcessing
Analytics R&D: python scripts developed to clean, mark, and quantify biomechanical errors

####Release 2.0 (10/28/2016):

Base Calibration Process:
  Reads recording of sitting feet calibration, calculates quaternions, checks for missing data, and checks for good sensor placement. If any failures, rpush error to user. Saves attempts to biometrix-specialanatomicalcalibrationprocessedcontainer.
  
  Test data sets under preProcessing/app/test/data/runBaseFeet.
  
  Run - runBaseFeet.py
  
  Input - (data, 'filename')
  
  Output - processed_filename
  
  Returns - string for 'Success' or 'Failure'

Session Calibration Process:
  Reads recording of standing calibration, calculates quaternions, checks for missing data, and checks for good sensor placement. If any failures, rpush error to user. If part of base calibration, reads unexpired successful base feet calibration attempt and uses both files to calculate offset values for general use and for current session coordinate frame transformations.
  If regular session calibration, reads unexpired general offsets from base calibration and further processes to create specific offset values for session coordinate frame transformation. Saves attempts to biometrix-anatomicalcalibrationprocessedcontainer and offset values to SessionCalibrationEvent Table.


  Test data sets under preProcessing/app/test/data/runSessionCalibration.
  
  Run - runSessionCalibration.py
  
  Input - (data, 'filename')
  
  Output - processed_filename
  
  Returns - string for 'Success' or 'Failure'

Training Process:
  Reads recording of coach performing specific exercise, calculates quaternions, and checks for missing data. Uses calibration offsets to transform orientation data to the body frame and acceleration to the adjusted inertial frame. Calculates phase. Uses hip acceleration to determine plane of motion and phase paired with hip orientation to determine stance. Plane and stance generalized to characteristic booleans describing exercise. Exercise acceleration characterized using total acceleration. Saves successful attempts to biometrix-trainingprocessedcontainer and exercise characterizations to TrainingEvent Table.
  
  Test data sets under preProcessing/app/test/data/trainingSystemExecution.
  
  Run - trainingSystemExecution.py
  
  Input - (data, 'filename')
  
  Output - processed_filename
  
  List of packages used in the above lambda processes:
  numpy '1.11.1'
  
  pandas '0.18.1'
  
  boto3 '1.4.1'
  
  psycopg2 '2.6.2'
  
  scipy '0.18.1'
  
  sklearn '0.18rc2'
  
  itertools
  
  enum
  
  datetime
  
  sys
  
  cStringIO

####Release 1.9 (TBD):
execution_v1.3.py - 'cme' object to be changed (potential to cause confusion)
runAnalytics.py - balance cme names will be changed 

####Release 1.8 (09/03/2016):
dataObject.py: Made change to line 21

setUp.py: made changes to lines 33 and 58

####Release 1.7 (08/26/2016):
anatomicalCalibration - Updated test_errors fxn to only use quaternions instead of euler angles. Added feetCheck, hipCenter, and statusChecks fxns that are used to identify errors in placement of the sensors. Added quatClose fxn that is used in the init_orientation fxn to make sure that quaternions being averaged together are "close". The init_orientation fxn now averages quaternions instead of euler angles. Finally, an adjustment to hip_orientation_fix to filter out extreme theta values.

coordinateFrameTransformation - Added clipped accel fxn to test for clipped acceleration values. Lines 143-156, clipped acceleration and bad quaternion tests.

dataChecks - Set of functions for testing bad quaternions and calculating the Euler Angles derived from the onboardCoordinateFrameTransformation

onboardCoordinateFrameTransformation - Takes the coordinate frame transform out of the cloud and onto the devices.

runAnalyticsNoTransform - Same as runAnalytics but the TransformData fxn is replaced by the fxn in dataChecks.

runAnatomical - Added many checks to make sure the sensors are placed correctly while at the same time computing the anatomical offsets for each sensor. Now has a status attribute that can be used to check if the sensors have been placed correctly. 

setUp - Added a SensCal class that now replaces the previous Anatomical class. Takes in three more variables now.

####Release 1.6 (08/26/2016):
Phase Detection - Inputs changed to ldata['AccZ'], rdata['AccZ'], sampl_rate. Also, made changes to the phase detection algorithm. Corresponding changes were made to the other functions in the phaseDetection script as well. Outputs remain the same: phase id for the left foot and the right foot. Test data sets are available in test/data/phaseDetection.

Run Analytics - incorporated changes correpsonding to the changes made to the phaseDetection script. Only made changes to the phase.combine_phase function call.

####Release Mobile App Analytics 1.0 (8/11/16):
Sensor Placement- runSensPlace is used to determine the placement of a sensor on the body

####Release 1.5 (7/29/16):
Phase Detection - made changes to the input variables to the combine_phase function. rdata/ldata['AccX'] & rdata/ldata['AccZ'] are separate numpy arrays that are being passed to the combine_phase function in the phaseDetection script. To incorporate the separation of the numpy arrays, relevant changes were made to the other functions as well.

Run Analytics - incorporated the changes corresponding to the phase detection input variables. Added rfbf.AccX & lfbf.AccX in addition to the already existing input variables.

Data Object - added a to_array() method to the abstract class. Removed redundancies regarding the row() method being in all the subclasses 

####Release 1.4 (7/22/16):
Phase Detection - developed a new algortihm to improve the accuracy of balance phase detection. Made slight changes to the impact phase algorithm to improve the detection accuracy of the starting point of an impact phase. Updated test data sets are available in the test/data/phaseDetection folder.

Sensor Placement - developed algorithm that allows for users to identify sensor placement by tapping on the sensors three times. Searches for errors in the execution of the tapping, extra movement, tapping the same sensor twice, and bad orientation of the sensor.

setUp - made some changes about how the data is parsed so that information in the column names of the original dataset can still be maintained

####Release 1.3 (7/8/16):
Anatomical Calibration - reviewing rotation methods for 100% accuracy, improving anatomical fixes

Coordinate Frame Transformation - Removed reliance on heading variable, now filters through using yaw offset from Anatomical Calibration

Phase Detection - merging balance and impact phase methods, improving accuracy of boundaries

Impact CME, Execution Score, Load Calc - updated to match changes in the Phase Detection script

####Release 1.2.1 (7/6/16):
Execution Score - Moving CME and loading calculation outside the scoring mechanism.

General - Script name changes

####Release 1.2 (6/29/16):
Coordinate Frame Transformation - prepped for anatomical calibration, X component of body frame now fixed to body part rather than gobal coordinate frame

Anatomical Calibration - Separate module used to find quaternions that represent two necessary rotations and one orientation per sensor

Phase Detection - now differentiates between a still foot off the ground and a still foot on the ground

Balance CMEs - now does not filter for changes beyond a threshold nor changes that exceed a time limit. Purely filters by finding phases deemed "relevant" for the specific CME. Also provides a "continuous" stream of normalized and raw cme values, instead of discretized.

Impact CMEs - determines the impact angle and timing of impact differences

Execution Score - provides a metric that quantifies the athlete's ability to execute a "good" regimen, weighted by load

Loading CMEs, Balance Phase - percent weight distribution, currently basic 100% or 50% based on phase id logic (outputs in percentage of load on left leg)

Load Calc - updated data structure of output

####Release 1.1 (6/17/16):
Phase Detection - identifies the impact phase, the second relevant phase

Load Calc - major variable for reporting, contextualizes CMEs

Balance CMEs - lying on top of the peak detect script, quantify max rotations for ie pronation, hip drop etc

Phase Detection, Balance - changed output values for body_phase function from [0,10,20,30] to [0,1,2,3]

####Release 1.0 (6/10/16)
Coordinate Frame Transformation - transform sensor frame to body frame

Phase Detection - id foot not moving and in contact with the ground, create id for R/L single and double 

Peak Detection - id for max and min orientation values to input into CME detection


####Future Releases

X-------Code Freeze for Alpha--------X

- Symmetry Score
- Constructive/Destructive Load
- Load calculation for Impact phase
- Distribution of Load for balance phace
- Anterior Pelvic Tilt
- Correct CMEs of sensor placement off center at hips and inside/outside heel
- Fatigue Score
