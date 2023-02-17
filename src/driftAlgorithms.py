'''
This file is adopted directly and as is from:
Carr, Jon W., et al. "Algorithms for the automated correction of vertical drift
in eye-tracking data." Behavior Research Methods 54.1 (2022): 287-310.
'''


import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
from sklearn.cluster import KMeans
import math

######################################################################
# ATTACH
######################################################################

def attach(fixation_XY, line_Y):
	n = len(fixation_XY)
	for fixation_i in range(n):
		line_i = np.argmin(abs(line_Y - fixation_XY[fixation_i, 1]))
		fixation_XY[fixation_i, 1] = line_Y[line_i]
	return fixation_XY

######################################################################
# CHAIN
#
# https://github.com/sascha2schroeder/popEye/
######################################################################

def chain(fixation_XY, line_Y, x_thresh=192, y_thresh=32):
	n = len(fixation_XY)
	dist_X = abs(np.diff(fixation_XY[:, 0]))
	dist_Y = abs(np.diff(fixation_XY[:, 1]))
	end_chain_indices = list(np.where(np.logical_or(dist_X > x_thresh, dist_Y > y_thresh))[0] + 1)
	end_chain_indices.append(n)
	start_of_chain = 0
	for end_of_chain in end_chain_indices:
		mean_y = np.mean(fixation_XY[start_of_chain:end_of_chain, 1])
		line_i = np.argmin(abs(line_Y - mean_y))
		fixation_XY[start_of_chain:end_of_chain, 1] = line_Y[line_i]
		start_of_chain = end_of_chain
	return fixation_XY

######################################################################
# CLUSTER
#
# https://github.com/sascha2schroeder/popEye/
######################################################################

def cluster(fixation_XY, line_Y):
	m = len(line_Y)
	fixation_Y = fixation_XY[:, 1].reshape(-1, 1)
	clusters = KMeans(m, n_init=100, max_iter=300).fit_predict(fixation_Y)
	centers = [fixation_Y[clusters == i].mean() for i in range(m)]
	ordered_cluster_indices = np.argsort(centers)
	for fixation_i, cluster_i in enumerate(clusters):
		line_i = np.where(ordered_cluster_indices == cluster_i)[0][0]
		fixation_XY[fixation_i, 1] = line_Y[line_i]
	return fixation_XY

######################################################################
# MERGE
#
# Špakov, O., Istance, H., Hyrskykari, A., Siirtola, H., & Räihä,
#   K.-J. (2019). Improving the performance of eye trackers with
#   limited spatial accuracy and low sampling rates for reading
#   analysis by heuristic fixation-to-word mapping. Behavior Research
#   Methods, 51(6), 2661–2687.
#
# https://doi.org/10.3758/s13428-018-1120-x
# https://github.com/uta-gasp/sgwm
######################################################################

phases = [{'min_i':3, 'min_j':3, 'no_constraints':False}, # Phase 1
          {'min_i':1, 'min_j':3, 'no_constraints':False}, # Phase 2
          {'min_i':1, 'min_j':1, 'no_constraints':False}, # Phase 3
          {'min_i':1, 'min_j':1, 'no_constraints':True}]  # Phase 4

def merge(fixation_XY, line_Y, y_thresh=32, g_thresh=0.1, e_thresh=20):
	n = len(fixation_XY)
	m = len(line_Y)
	diff_X = np.diff(fixation_XY[:, 0])
	dist_Y = abs(np.diff(fixation_XY[:, 1]))
	sequence_boundaries = list(np.where(np.logical_or(diff_X < 0, dist_Y > y_thresh))[0] + 1)
	sequence_starts = [0] + sequence_boundaries
	sequence_ends = sequence_boundaries + [n]
	sequences = [list(range(start, end)) for start, end in zip(sequence_starts, sequence_ends)]
	for phase in phases:
		while len(sequences) > m:
			best_merger = None
			best_error = np.inf
			for i in range(len(sequences)-1):
				if len(sequences[i]) < phase['min_i']:
					continue # first sequence too short, skip to next i
				for j in range(i+1, len(sequences)):
					if len(sequences[j]) < phase['min_j']:
						continue # second sequence too short, skip to next j
					candidate_XY = fixation_XY[sequences[i] + sequences[j]]
					gradient, intercept = np.polyfit(candidate_XY[:, 0], candidate_XY[:, 1], 1)
					residuals = candidate_XY[:, 1] - (gradient * candidate_XY[:, 0] + intercept)
					error = np.sqrt(sum(residuals**2) / len(candidate_XY))
					if phase['no_constraints'] or (abs(gradient) < g_thresh and error < e_thresh):
						if error < best_error:
							best_merger = (i, j)
							best_error = error
			if best_merger is None:
				break # no possible mergers, break while and move to next phase
			merge_i, merge_j = best_merger
			merged_sequence = sequences[merge_i] + sequences[merge_j]
			sequences.append(merged_sequence)
			del sequences[merge_j], sequences[merge_i]
	mean_Y = [fixation_XY[sequence, 1].mean() for sequence in sequences]
	ordered_sequence_indices = np.argsort(mean_Y)
	for line_i, sequence_i in enumerate(ordered_sequence_indices):
		fixation_XY[sequences[sequence_i], 1] = line_Y[line_i]
	return fixation_XY

######################################################################
# REGRESS
#
# Cohen, A. L. (2013). Software for the automatic correction of
#   recorded eye fixation locations in reading experiments. Behavior
#   Research Methods, 45(3), 679–683.
#
# https://doi.org/10.3758/s13428-012-0280-3
# https://blogs.umass.edu/rdcl/resources/
######################################################################

def regress(fixation_XY, line_Y, k_bounds=(-0.1, 0.1), o_bounds=(-50, 50), s_bounds=(1, 20)):
	n = len(fixation_XY)
	m = len(line_Y)

	def fit_lines(params, return_line_assignments=False):
		k = k_bounds[0] + (k_bounds[1] - k_bounds[0]) * norm.cdf(params[0])
		o = o_bounds[0] + (o_bounds[1] - o_bounds[0]) * norm.cdf(params[1])
		s = s_bounds[0] + (s_bounds[1] - s_bounds[0]) * norm.cdf(params[2])
		predicted_Y_from_slope = fixation_XY[:, 0] * k
		line_Y_plus_offset = line_Y + o
		density = np.zeros((n, m))
		for line_i in range(m):
			fit_Y = predicted_Y_from_slope + line_Y_plus_offset[line_i]
			density[:, line_i] = norm.logpdf(fixation_XY[:, 1], fit_Y, s)
		if return_line_assignments:
			return density.argmax(axis=1)
		return -sum(density.max(axis=1))

	best_fit = minimize(fit_lines, [0, 0, 0])
	line_assignments = fit_lines(best_fit.x, True)
	for fixation_i, line_i in enumerate(line_assignments):
		fixation_XY[fixation_i, 1] = line_Y[line_i]
	return fixation_XY

######################################################################
# SEGMENT
#
# Abdulin, E. R., & Komogortsev, O. V. (2015). Person verification via
#   eye movement-driven text reading model, In 2015 IEEE 7th
#   International Conference on Biometrics Theory, Applications and
#   Systems. IEEE.
#
# https://doi.org/10.1109/BTAS.2015.7358786
######################################################################

def segment(fixation_XY, line_Y):
	n = len(fixation_XY)
	m = len(line_Y)
	diff_X = np.diff(fixation_XY[:, 0])
	saccades_ordered_by_length = np.argsort(diff_X)
	line_change_indices = saccades_ordered_by_length[:m-1]
	current_line_i = 0
	for fixation_i in range(n):
		fixation_XY[fixation_i, 1] = line_Y[current_line_i]
		if fixation_i in line_change_indices:
			current_line_i += 1
	return fixation_XY

######################################################################
# SPLIT
#
# Carr, J. W., Pescuma, V. N., Furlan, M., Ktori, M., & Crepaldi, D.
#   (2021). Algorithms for the automated correction of vertical drift
#   in eye-tracking data. Behavior Research Methods.
#
# https://doi.org/10.3758/s13428-021-01554-0
# https://github.com/jwcarr/drift
######################################################################

def split(fixation_XY, line_Y):
	n = len(fixation_XY)
	diff_X = np.diff(fixation_XY[:, 0])
	clusters = KMeans(2, n_init=10, max_iter=300).fit_predict(diff_X.reshape(-1, 1))
	centers = [diff_X[clusters == 0].mean(), diff_X[clusters == 1].mean()]
	sweep_marker = np.argmin(centers)
	end_line_indices = list(np.where(clusters == sweep_marker)[0] + 1)
	end_line_indices.append(n)
	start_of_line = 0
	for end_of_line in end_line_indices:
		mean_y = np.mean(fixation_XY[start_of_line:end_of_line, 1])
		line_i = np.argmin(abs(line_Y - mean_y))
		fixation_XY[start_of_line:end_of_line, 1] = line_Y[line_i]
		start_of_line = end_of_line
	return fixation_XY

######################################################################
# STRETCH
#
# Lohmeier, S. (2015). Experimental evaluation and modelling of the
#   comprehension of indirect anaphors in a programming language
#   (Master’s thesis). Technische Universität Berlin.
#
# http://www.monochromata.de/master_thesis/ma1.3.pdf
######################################################################

def stretch(fixation_XY, line_Y, scale_bounds=(0.9, 1.1), offset_bounds=(-50, 50)):
	n = len(fixation_XY)
	fixation_Y = fixation_XY[:, 1]

	def fit_lines(params, return_correction=False):
		candidate_Y = fixation_Y * params[0] + params[1]
		corrected_Y = np.zeros(n)
		for fixation_i in range(n):
			line_i = np.argmin(abs(line_Y - candidate_Y[fixation_i]))
			corrected_Y[fixation_i] = line_Y[line_i]
		if return_correction:
			return corrected_Y
		return sum(abs(candidate_Y - corrected_Y))

	best_fit = minimize(fit_lines, [1, 0], bounds=[scale_bounds, offset_bounds])
	fixation_XY[:, 1] = fit_lines(best_fit.x, return_correction=True)
	return fixation_XY


def compare(fixation_XY, word_XY, x_thresh=512, n_nearest_lines=3):
	line_Y = np.unique(word_XY[:, 1])
	n = len(fixation_XY)
	diff_X = np.diff(fixation_XY[:, 0])
	end_line_indices = list(np.where(diff_X < -x_thresh)[0] + 1)
	end_line_indices.append(n)
	start_of_line = 0
	for end_of_line in end_line_indices:
		gaze_line = fixation_XY[start_of_line:end_of_line]
		mean_y = np.mean(gaze_line[:, 1])
		lines_ordered_by_proximity = np.argsort(abs(line_Y - mean_y))
		nearest_line_I = lines_ordered_by_proximity[:n_nearest_lines]
		line_costs = np.zeros(n_nearest_lines)
		for candidate_i in range(n_nearest_lines):
			candidate_line_i = nearest_line_I[candidate_i]
			text_line = word_XY[word_XY[:, 1] == line_Y[candidate_line_i]]
			dtw_cost, _ = dynamic_time_warping(gaze_line[:, 0:1], text_line[:, 0:1])
			line_costs[candidate_i] = dtw_cost
		line_i = nearest_line_I[np.argmin(line_costs)]
		fixation_XY[start_of_line:end_of_line, 1] = line_Y[line_i]
		start_of_line = end_of_line
	return fixation_XY

######################################################################
# WARP
#
# Carr, J. W., Pescuma, V. N., Furlan, M., Ktori, M., & Crepaldi, D.
#   (2021). Algorithms for the automated correction of vertical drift
#   in eye-tracking data. Behavior Research Methods.
#
# https://doi.org/10.3758/s13428-021-01554-0
# https://github.com/jwcarr/drift
######################################################################

def warp(fixation_XY, word_XY):
	_, dtw_path = dynamic_time_warping(fixation_XY, word_XY)
	for fixation_i, words_mapped_to_fixation_i in enumerate(dtw_path):
		candidate_Y = word_XY[words_mapped_to_fixation_i, 1]
		fixation_XY[fixation_i, 1] = mode(candidate_Y)
	return fixation_XY

def mode(values):
	values = list(values)
	return max(set(values), key=values.count)

def time_warp(fixation_XY, word_XY):

    durations = np.delete(fixation_XY, 0, 1)
    durations = np.delete(durations, 0, 1)
    fixation_XY = np.delete(fixation_XY, 2, 1)

    word_durations = np.delete(word_XY, 0, 1)
    word_durations = np.delete(word_durations, 0, 1)
    word_XY = np.delete(word_XY, 2, 1)

    _, dtw_path = dynamic_time_warping(durations, word_durations)

    for fixation_i, words_mapped_to_fixation_i in enumerate(dtw_path):
        candidate_Y = word_XY[words_mapped_to_fixation_i, 1]
        fixation_XY[fixation_i, 1] = mode(candidate_Y)
    return fixation_XY


######################################################################
# Dynamic Time Warping adapted from https://github.com/talcs/simpledtw
# This is used by the COMPARE and WARP algorithms
######################################################################

def dynamic_time_warping(sequence1, sequence2):
	n1 = len(sequence1)
	n2 = len(sequence2)
	dtw_cost = np.zeros((n1+1, n2+1))
	dtw_cost[0, :] = np.inf
	dtw_cost[:, 0] = np.inf
	dtw_cost[0, 0] = 0
	for i in range(n1):
		for j in range(n2):
			this_cost = np.sqrt(sum((sequence1[i] - sequence2[j])**2))
			dtw_cost[i+1, j+1] = this_cost + min(dtw_cost[i, j+1], dtw_cost[i+1, j], dtw_cost[i, j])
	dtw_cost = dtw_cost[1:, 1:]
	dtw_path = [[] for _ in range(n1)]
	while i > 0 or j > 0:
		dtw_path[i].append(j)
		possible_moves = [np.inf, np.inf, np.inf]
		if i > 0 and j > 0:
			possible_moves[0] = dtw_cost[i-1, j-1]
		if i > 0:
			possible_moves[1] = dtw_cost[i-1, j]
		if j > 0:
			possible_moves[2] = dtw_cost[i, j-1]
		best_move = np.argmin(possible_moves)
		if best_move == 0:
			i -= 1
			j -= 1
		elif best_move == 1:
			i -= 1
		else:
			j -= 1
	dtw_path[0].append(0)
	return dtw_cost[-1, -1], dtw_path


######################################################################
# SLICE
#
# Glandorf, D., & Schroeder, S. (2021). Slice: An algorithm to assign
#   fixations in multi-line texts. Procedia Computer Science, 192,
#   2971–2979.
#
# https://doi.org/10.1016/j.procs.2021.09.069
######################################################################

def slice(fixation_XY, line_Y, x_thresh=192, y_thresh=32, w_thresh=32, n_thresh=90):
	n = len(fixation_XY)
	line_height = np.mean(np.diff(line_Y))
	proto_lines, phantom_proto_lines = {}, {}
	# 1. Segment runs
	dist_X = abs(np.diff(fixation_XY[:, 0]))
	dist_Y = abs(np.diff(fixation_XY[:, 1]))
	end_run_indices = list(np.where(np.logical_or(dist_X > x_thresh, dist_Y > y_thresh))[0] + 1)
	run_starts = [0] + end_run_indices
	run_ends = end_run_indices + [n]
	runs = [list(range(start, end)) for start, end in zip(run_starts, run_ends)]
	# 2. Determine starting run
	longest_run_i = np.argmax([fixation_XY[run[-1], 0] - fixation_XY[run[0], 0] for run in runs])
	proto_lines[0] = runs.pop(longest_run_i)
	# 3. Group runs into proto lines
	while runs:
		merger_on_this_iteration = False
		for proto_line_i, direction in [(min(proto_lines), -1), (max(proto_lines), 1)]:
			# Create new proto line above or below (depending on direction)
			proto_lines[proto_line_i + direction] = []
			# Get current proto line XY coordinates (if proto line is empty, get phanton coordinates)
			if proto_lines[proto_line_i]:
				proto_line_XY = fixation_XY[proto_lines[proto_line_i]]
			else:
				proto_line_XY = phantom_proto_lines[proto_line_i]
			# Compute differences between current proto line and all runs
			run_differences = np.zeros(len(runs))
			for run_i, run in enumerate(runs):
				print(fixation_XY[run])
				y_diffs = [y - proto_line_XY[np.argmin(abs(proto_line_XY[:, 0] - x)), 1] for x, y, z in fixation_XY[run]]
				run_differences[run_i] = np.mean(y_diffs)
			# Find runs that can be merged into this proto line
			merge_into_current = list(np.where(abs(run_differences) < w_thresh)[0])
			# Find runs that can be merged into the adjacent proto line
			merge_into_adjacent = list(np.where(np.logical_and(
				run_differences * direction >= w_thresh,
				run_differences * direction < n_thresh
			))[0])
			# Perform mergers
			for index in merge_into_current:
				proto_lines[proto_line_i].extend(runs[index])
			for index in merge_into_adjacent:
				proto_lines[proto_line_i + direction].extend(runs[index])
			# If no, mergers to the adjacent, create phantom line for the adjacent
			if not merge_into_adjacent:
				average_x, average_y, ghost = np.mean(proto_line_XY, axis=0)
				adjacent_y = average_y + line_height * direction
				phantom_proto_lines[proto_line_i + direction] = np.array([[average_x, adjacent_y]])
			# Remove all runs that were merged on this iteration
			for index in sorted(merge_into_current + merge_into_adjacent, reverse=True):
				del runs[index]
				merger_on_this_iteration = True
		# If no mergers were made, break the while loop
		if not merger_on_this_iteration:
			break
	# 4. Assign any leftover runs to the closest proto lines
	for run in runs:
		best_pl_distance = np.inf
		best_pl_assignemnt = None
		for proto_line_i in proto_lines:
			if proto_lines[proto_line_i]:
				proto_line_XY = fixation_XY[proto_lines[proto_line_i]]
			else:
				proto_line_XY = phantom_proto_lines[proto_line_i]
			y_diffs = [y - proto_line_XY[np.argmin(abs(proto_line_XY[:, 0] - x)), 1] for x, y, z in fixation_XY[run]]
			pl_distance = abs(np.mean(y_diffs))
			if pl_distance < best_pl_distance:
				best_pl_distance = pl_distance
				best_pl_assignemnt = proto_line_i
		proto_lines[best_pl_assignemnt].extend(run)
	# 5. Prune proto lines
	while len(proto_lines) > len(line_Y):
		top, bot = min(proto_lines), max(proto_lines)
		if len(proto_lines[top]) < len(proto_lines[bot]):
			proto_lines[top + 1].extend(proto_lines[top])
			del proto_lines[top]
		else:
			proto_lines[bot - 1].extend(proto_lines[bot])
			del proto_lines[bot]
	# 6. Map proto lines to text lines
	for line_i, proto_line_i in enumerate(sorted(proto_lines)):
		fixation_XY[proto_lines[proto_line_i], 1] = line_Y[line_i]
	return fixation_XY
 
    