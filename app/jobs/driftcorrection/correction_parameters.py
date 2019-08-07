# Drift correction: left foot, hip, right foot
## Axl filter parameters- cutoff frequencies (Hz)
f_cut_low_foot = 11
f_cut_low_hip = 3
f_cut_high = 0.5
## FFT double peak control parameters
# FFT samples
fft_num_samples = 2 ** 10
# Threshold to discard double of fundamental frequency peak
epsilon = 0.15
# Threshold to consider max frequency valid peaks
Max_fq = 3
# Window changing rhythm enlarging factor
fac = 1
# Factor scaling on Max FFT
scaling_fac_foot = 2
scaling_fac_hip = 0.5
# Corr_points discarding thresholds, on the basis of avg axl value of the dynamic window Corr_points position
avg_troughs_max_TH_foot = 0
avg_troughs_min_TH_foot = 1.2
avg_troughs_max_TH_hip = 1.5
avg_troughs_min_TH_hip = 0.8
## Correction thresholds
# Number of troughs found after which begin to correct
corr_point_threshold = 7
# Treshold on pitch and roll to manage jumps in q_delta in rhythm changes (deg)
tilt_th_pitch = 15
tilt_th_roll = 8
yaw_th = 20
# Threshold used to discard outliers in hip
tilt_discard_th_hip = 5
## Todd Andrews input threshold
# scaling on amplitude
s_ampl_foot = 4
s_ampl_hip = 3
# scaling on number of samples
s_sampl_foot = 0.9
s_sampl_hip = 1

# Parameters lists
foot_parameters = list(
        [f_cut_low_foot, f_cut_high, fft_num_samples, epsilon, Max_fq, fac, scaling_fac_foot, avg_troughs_max_TH_foot, avg_troughs_min_TH_foot, corr_point_threshold, tilt_th_pitch,
         tilt_th_roll, s_ampl_foot, s_sampl_foot, tilt_discard_th_hip, yaw_th])
hip_parameters = list(
        [f_cut_low_hip, f_cut_high, fft_num_samples, epsilon, Max_fq, fac, scaling_fac_hip, avg_troughs_max_TH_hip, avg_troughs_min_TH_hip, corr_point_threshold, tilt_th_pitch, tilt_th_roll,
         s_ampl_hip, s_sampl_hip, tilt_discard_th_hip, yaw_th])