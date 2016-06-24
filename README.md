### PreProcessing
Analytics R&D: python scripts developed to clean, mark, and quanitify biomechanical errors

####Release 1.2 (In Progress):
Body Frame Transformation (status: released) preped for anatomical calibration, X component of body frame now fixed to body part rather than gobal coordinate frame

Phase Detection, Update (status: released) now differentiates between a still foot off the ground and a still foot on the ground

Quantifying Balance CMEs, Update (status: released) now does not filter for changes beyond a threshold nor changes that exceed a time limit. Purely filters by finding phases deemed "relevant" for the specific CME

Quantifying Impact CMEs (status: code review) determines the impact angle and timing of impact differences

Execution Reporting Mechanism (status:method selected) provides a metric that quantifies the athlete's ability to execute a "good" regimen, weighted by load

Load Distribution CME, Balance Phase (stats: discovery) percent weight distribution, currently basic 100% or 50% based on phase id logic (outputs in percentage of load on left leg)

Load, Updated (status: ???) updates made with true data comparison

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
