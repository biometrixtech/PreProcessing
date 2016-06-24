### PreProcessing
Analytics R&D: python scripts developed to clean, mark, and quanitify biomechanical errors

####Release 1.2 (In Progress):
Quantifying Impact CMEs (status: code review) determines the impact angle and timing of impact differences

Execution Reporting Mechanism (status:method selected) provides a metric that quantifies the athlete's ability to execute a "good" regimen, weighted by load

Anatomical Reference for Body Frame Transformation (status: code review) makes sure each sensor's body frame is now oriented close-to-forward even during dynamic activities

Phase Detection, Update (status: code review) now differentiates between a still foot off the ground and a still foot on the ground

CME_Detect, Update (status: code review) now does not filter for changes beyond a threshold nor changes that exceed a time limit. Purely filters by finding phases deemed "relevant" for the specific CME

Load Calc, Update (stats: code review) now calculates the distribution of the load for CME errors (outputs in percentage of load on left leg)

####Release 1.1 (6/17/16):
Phase Detection, Impact (status: released) identifies the impact phase, the second relevant phase

Load (status: released) major variable for reporting, contextualizes CMEs

Quantifying Balance CMEs (status: released) lying on top of the peak detect script, quantify max rotations for ie pronation, hip drop etc

Phase Detection, Balance (status: released) changed output values for body_phase function from [0,10,20,30] to [0,1,2,3]
####Release 1.0 (6/10/16)
Data Processing (status: released) transform sensor frame to body frame

Phase Detection, Balance (status: released) id foot not moving and in contact with the ground, create id for R/L single and double 

Peak Detection (status: released) id for max and min orientation values to input into CME detection

Execution (status: released) Data Processing > Phase Detection > Peak Detection

####Future Releases

X-------Code Freeze for Alpha--------X

7/1 - Fatigue Reporting Mechanism, V2 Load

7/8 - Anatomical Reference for Body Frame Trasformation, Anything needed for Firmware Update 

7/X - Execution Reporting Mechanism, Constructive/Destructive Load Reporting Mechanism


#####(Statuses: discovery, method selected, testing, code review, released)
