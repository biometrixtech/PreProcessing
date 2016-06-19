### PreProcessing
Analytics R&D: python scripts developed to clean, mark, and quanitify biomechanical errors

####Release (In Progress):
Quantifying Impact CMEs (status: discovery) determines the impact angle and timing of impact differences

Symmetry Reporting Mechanism (status:discovery) provides a metric that describes differences in orientation, rotation, or loading between two sides of the body

Anatomical Reference for Body Frame Transformation (status: discovery) identifies a "anatomically neutral" orientation for each sensor on the athlete

Weight Shift CME, Balance Phase (status: discovery) find if weight shifts can be quantified and identified

####Release 1.1 6/17:
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
