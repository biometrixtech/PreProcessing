### PreProcessing
Analytics R&D: python scripts developed to clean, mark, and quanitify biomechanical errors

####Release 1.2 (expected - 7/8/16):
Anatomical Calibration (status: updating) reviewing rotation methods for 100% accuracy, improving anatomical fixes

Phase ID (status: updating) merging balance and impact phase methods, improving accuracy of boundaries

Constructive/Destructive Load: (status: method selected) ready to be coded up

Symmetry Score (status: discovery) defining method very similar to execution score

fatigue Score (status: discovery) we will see... mechE or signal processing method for quantifying decay

####Release 1.2 (6/29/16):
Body Frame Transformation (status: released) prepped for anatomical calibration, X component of body frame now fixed to body part rather than gobal coordinate frame

Anatomical Calibration (status: released) Separate module used to find quaternions that represent two necessary rotations and one orientation per sensor

Phase Detection, Update (status: released) now differentiates between a still foot off the ground and a still foot on the ground

Quantifying Balance CMEs, Update (status: released) now does not filter for changes beyond a threshold nor changes that exceed a time limit. Purely filters by finding phases deemed "relevant" for the specific CME. Also provides a "continuous" stream of normalized and raw cme values, instead of discretized.

Quantifying Impact CMEs (status: released) determines the impact angle and timing of impact differences

Execution Reporting Mechanism (status: released) provides a metric that quantifies the athlete's ability to execute a "good" regimen, weighted by load

Load Distribution CME, Balance Phase (stats: released) percent weight distribution, currently basic 100% or 50% based on phase id logic (outputs in percentage of load on left leg)

Load, Updated (status: released) updated data structure of output

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

- Load calculation for Impact phase
- Distribution of Load for balance phace
- Anterior Pelvic Tilt
- Correct CMEs of sensor placement off center at hips and inside/outside heel


#####(Statuses: discovery, method selected, testing, code review, released)
