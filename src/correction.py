"""
paper: Advancing Dynamic-Time Warp Techniques for Correcting Eye Tracking Data
    in Reading Source Code

Author: Naser Al Madi
email: nsalmadi@colby.edu or nsalmadi@seas.harvard.edu
"""
# This file contains functions to generate synthetic eye tracking data and
# new algorithms for correcting real and synthetic eye tracking data.
#
# some functions are copied from the Eye Movement in Programming Toolkit
# https://github.com/nalmadi/EMIP-Toolkit

import random
from . import driftAlgorithms as algo
from PIL import ImageFont, ImageDraw, Image
from matplotlib import pyplot as plt
import numpy as np


def generate_fixations_center(aois_with_tokens):
    """
    function to generate fixations at the center of each word

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """

    fixations = []

    for index, row in aois_with_tokens.iterrows():
        x, y, width, height = row["x"], row["y"], row["width"], row["height"]

        fixation_x = x + width / 2
        fixation_y = y + height / 2

        fixations.append([fixation_x, fixation_y])

    return fixations


def generate_fixations_left(aois_with_tokens):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """

    fixations = []

    for index, row in aois_with_tokens.iterrows():
        x, y, width, height, token = (
            row["x"],
            row["y"],
            row["width"],
            row["height"],
            row["token"],
        )

        fixation_x = x + width / 3
        fixation_y = y + height / 2

        fixations.append([fixation_x, fixation_y, len(token) * 50])

    return fixations


def generate_fixations_left_skip(aois_with_tokens):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word, also skips short words with a fixed 
    probability of 0.3

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """
        
    fixations = []
    word_count = 0
    skip_count = 0

    for index, row in aois_with_tokens.iterrows():
        x, y, width, height, token = (
            row["x"],
            row["y"],
            row["width"],
            row["height"],
            row["token"],
        )

        word_count += 1

        fixation_x = x + width / 3
        fixation_y = y + height / 2

        if len(token) < 4 and random.random() > 0.7:
            skip_count += 1
        else:
            fixations.append([fixation_x, fixation_y])

    print(skip_count / word_count)
    return fixations


def generate_fixations_left_skip(aois_with_tokens, skip_probability):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word, also skips short words with a probability
    defined by the user

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    skip_probability : float
        probability of skipping a word

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """

    fixations = []
    word_count = 0
    skip_count = 0

    for index, row in aois_with_tokens.iterrows():
        x, y, width, height, token = (
            row["x"],
            row["y"],
            row["width"],
            row["height"],
            row["token"],
        )

        word_count += 1

        fixation_x = x + width / 3
        fixation_y = y + height / 2

        if random.random() < skip_probability:
            skip_count += 1 
        else:
            fixations.append([fixation_x, fixation_y])

    # print(skip_count / word_count)
    return fixations


def get_duration_from_length(token):
    return 100 + len(token) * 40


def generate_fixations_left_skip_regression(aois_with_tokens):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word, also skips short words with a fixed
    probability and simulates regressions with a fixed probability of 0.04

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """

    fixations = []
    regress_count = 0

    aoi_list = aois_with_tokens.values.tolist()

    index = 0

    while index < len(aoi_list):
        # x, y, width, height, token = (
        x, y, width, height = (
            aoi_list[index][2],
            aoi_list[index][3],
            aoi_list[index][4],
            aoi_list[index][5],
            # aoi_list[index][7],
        )

        fixation_x = x + width / 3 + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)

        # skipping: 2-3 letter words are only fixated around 25% of the time (Rayner, 1998)
        if (width) < 55 and random.random() > 0.25 and last_skipped == False:
            last_skipped = True
        else:
            #duration = get_duration_from_length(token)
            duration = 100 + (width/15) * 40
            fixations.append([fixation_x, fixation_y, duration])
            last_skipped = False
        
        # regressions: 10-15% of the saccades are regressions (Rayner, 1998)
        # if  random.random() > 0.95:
        #     index -= random.randint(1, 10)

        #     if index < 0:
        #         index = 0

        #     regress_count += 1
        
        index += 1
    
    return fixations


def generate_fixations_left_regression(aois_with_tokens, regression_probability):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word, also simulates regressions with a 
    probability defined by the user

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    regression_probability : float
        probability of regression

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """

    fixations = []
    word_count = 0
    regress_count = 0

    aoi_list = aois_with_tokens.values.tolist()

    index = 0

    while index < len(aoi_list):
        # x, y, width, height, token = (
        x, y, width, height = (
            aoi_list[index][2],
            aoi_list[index][3],
            aoi_list[index][4],
            aoi_list[index][5],
            # aoi_list[index][7],
        )

        word_count += 1

        fixation_x = x + width / 3 + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)
        #duration = get_duration_from_length(token)
        duration = 100 + (width/15) * 40

        fixations.append([fixation_x, fixation_y, duration])

        if random.random() < regression_probability / 5:
            index -= random.randint(1, 10)
            if index < 0:
                index = 0
            regress_count += 1

        index += 1

    return fixations


def within_line_regression(aois_with_tokens, regression_probability):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word, also simulates WITHIN-line regressions
    with a probability defined by the user

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    regression_probability : float
        probability of regression

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """
        
    fixations = []

    aoi_list = aois_with_tokens.values.tolist()

    # pick regression indexes
    regression_indexes = []
    for index, row in aois_with_tokens.iterrows():
        if index > 2 and random.random() < regression_probability / 10:
            regression_indexes.append(index)

    # pick at least one regression index if probability is not 0
    if len(regression_indexes) == 0 and regression_probability > 0:
        regression_indexes.append(random.randint(2, len(aoi_list)-1))


    index = 0
    while index < len(aoi_list):
        # x, y, width, height, token = (
        x, y, width, height = (
                                aoi_list[index][2],
                                aoi_list[index][3],
                                aoi_list[index][4],
                                aoi_list[index][5],
                                #aoi_list[index][7],
                                )

        line = int(str(aoi_list[index][1]).split(" ")[1])

        fixation_x = x + width / 3 + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)
        duration = 100 + (width/15) * 40

        fixations.append([fixation_x, fixation_y, duration])

        if index in regression_indexes:
            regression_indexes.remove(index)
            rand_index = random.randint(index-10, index-1)

            attempts = 0

            # keep trying to find a word on a different line
            while (
                int(str(aoi_list[rand_index][1]).split(" ")[1]) != line
                and attempts < 10
            ):
                rand_index = random.randint(0, index-1)
                attempts += 1

            if attempts != 10:
                index = rand_index

        index += 1

    return fixations


def between_line_regression(aois_with_tokens, regression_probability):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word, also simulates BETWEEN-line regressions
    with a probability defined by the user

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    regression_probability : float
        probability of regression

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """
        
    fixations = []

    aoi_list = aois_with_tokens.values.tolist()

    # pick regression indexes
    regression_indexes = []
    for index, row in aois_with_tokens.iterrows():
        if index > 2 and random.random() < regression_probability / 10:
            regression_indexes.append(index)

    # pick at least one regression index if probability is not 0
    if len(regression_indexes) == 0 and regression_probability > 0:
        regression_indexes.append(random.randint(2, len(aoi_list)-1))


    index = 0
    while index < len(aoi_list):
        # x, y, width, height, token = (
        x, y, width, height = (
                                aoi_list[index][2],
                                aoi_list[index][3],
                                aoi_list[index][4],
                                aoi_list[index][5],
                                #aoi_list[index][7],
                                )

        line = int(str(aoi_list[index][1]).split(" ")[1])

        fixation_x = x + width / 3 + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)
        duration = 100 + (width/15) * 40

        fixations.append([fixation_x, fixation_y, duration])

        if index in regression_indexes:
            regression_indexes.remove(index)
            rand_index = random.randint(0, index-1)

            attempts = 0

            # keep trying to find a word on a different line
            while (
                int(str(aoi_list[rand_index][1]).split(" ")[1]) == line
                and attempts < 10
            ):
                rand_index = random.randint(0, index-1)
                attempts += 1

            if attempts != 10:
                index = rand_index

        index += 1

    return fixations


def error_offset(x_offset, y_offset, fixations):
    """
    Introduces an offset distortion to the fixations

    Parameters
    ----------
    x_offset : int
        offset in the x direction

    y_offset : int
        offset in the y direction

    fixations : list
        a list of fixations

    Returns
    ----------
    fixations : list
        a list of distorted fixations
    """

    results = []

    for fix in fixations:
        x, y = fix[0], fix[1]
        results.append([x + x_offset, y + y_offset, fix[2]])

    return results


def error_noise(y_noise, fixations):
    """
    Introduces a noise distortion to the fixations

    Parameters
    ----------
    y_noise :  int
        noise in the y direction

    fixations : list
        a list of fixations
    
    Returns
    ----------
    fixations : list
        a list of distorted fixations
    """

    results = []

    for fix in fixations:
        x, y, duration = fix[0], fix[1], fix[2]

        distorted_d = y + np.random.normal(0, y_noise)
        results.append([x, distorted_d, duration])

    return results


def error_shift(y_shift_factor, line_ys, fixations):
    """
    Introduces a shift distortion to the fixations

    Parameters
    ----------
    y_shift_factor : float
        shift factor

    line_ys : list
        a list of line Ys
        
    fixations : list
        a list of fixations

    Returns
    ----------
    fixations : list
        a list of distorted fixations
    """

    results = []

    line_height = line_ys[1] - line_ys[0]

    for fix in fixations:
        x, y = fix[0], fix[1]

        distance_from_first_line = abs(y - line_ys[0])

        results.append(
            [x, y + ((distance_from_first_line/line_height*2) * y_shift_factor/2), fix[2]]
        )


    return results



def error_droop(droop_factor, fixations):
    """
    Introduces a slope/droop distortion to the fixations

    Parameters
    ----------
    droop_factor : float
        droop factor
        
    fixations : list
        a list of fixations

    Returns
    ----------
    fixations : list
        a list of distorted fixations
    """

    results = []

    first_x = fixations[0][0]

    for fix in fixations:
        x, y = fix[0], fix[1]

        results.append([x, y + ((x - first_x) / 100 * droop_factor), fix[2]])

    return results


def draw_fixation(Image_file, fixations):
    """
    Private method that draws the fixation, also allow user to draw eye movement order

    Parameters
    ----------
    draw : PIL.ImageDraw.Draw
        a Draw object imposed on the image

    draw_number : bool
        whether user wants to draw the eye movement number
    """

    im = Image.open(Image_file)
    draw = ImageDraw.Draw(im, "RGBA")

    if len(fixations[0]) == 3:
        x0, y0, duration = fixations[0]
    else:
        x0, y0 = fixations[0]

    for fixation in fixations:
        if len(fixations[0]) == 3:
            duration = fixation[2]
            if 5 * (duration / 100) < 5:
                r = 3
            else:
                r = 5 * (duration / 100)
        else:
            r = 8
        x = fixation[0]
        y = fixation[1]

        bound = (x - r, y - r, x + r, y + r)
        outline_color = (50, 255, 0, 0)
        fill_color = (50, 255, 0, 220)
        draw.ellipse(bound, fill=fill_color, outline=outline_color)

        bound = (x0, y0, x, y)
        line_color = (255, 155, 0, 155)
        penwidth = 2
        draw.line(bound, fill=line_color, width=5)

        x0, y0 = x, y

    plt.figure(figsize=(17, 15))
    plt.imshow(np.asarray(im), interpolation="nearest")


def draw_correction(Image_file, fixations, match_list):
    """Private method that draws the fixation, also allow user to draw eye movement order

    Parameters
    ----------
    draw : PIL.ImageDraw.Draw
        a Draw object imposed on the image

    fixations : list
        a list of fixations

    match_list : list
        a list of matches (1) and mismatches (0)
    """

    im = Image.open(Image_file)
    draw = ImageDraw.Draw(im, "RGBA")

    if len(fixations[0]) == 3:
        x0, y0, duration = fixations[0]
    else:
        x0, y0 = fixations[0]

    for index, fixation in enumerate(fixations):
        if len(fixations[0]) == 3:
            duration = fixation[2]
            if 5 * (duration / 100) < 5:
                r = 3
            else:
                r = 5 * (duration / 100)
        else:
            r = 8

        x = fixation[0]
        y = fixation[1]

        bound = (x - r, y - r, x + r, y + r)
        outline_color = (50, 255, 0, 0)

        if match_list[index] == 1:
            fill_color = (50, 255, 0, 220)
        else:
            fill_color = (255, 55, 0, 220)

        draw.ellipse(bound, fill=fill_color, outline=outline_color)

        bound = (x0, y0, x, y)
        line_color = (255, 155, 0, 155)
        penwidth = 2
        draw.line(bound, fill=line_color, width=5)
        x0, y0 = x, y

    plt.figure(figsize=(17, 15))
    plt.imshow(np.asarray(im), interpolation="nearest")


def find_lines_Y(aois):
    """
    returns a lost of line Ys

    Parameters
    ----------
    aois : pandas.DataFrame
        a dataframe containing the AOIs

    Returns
    ----------
    results : list
        a list of line Ys
    """

    results = []

    for index, row in aois.iterrows():
        y, height = row["y"], row["height"]

        if y + height / 2 not in results:
            results.append(y + height / 2)

    return results


def find_word_centers(aois):
    """
    returns a list of word centers

    Parameters
    ----------
    aois : pandas.DataFrame
        a dataframe containing the AOIs

    Returns
    ----------
    results : list
        a list of word center coordinates
    """

    results = []

    for index, row in aois.iterrows():
        x, y, height, width = row["x"], row["y"], row["height"], row["width"]

        center = [int(x + width // 2), int(y + height // 2)]

        if center not in results:
            results.append(center)

    return results


def find_word_centers_and_duration(aois):
    """
    returns a list of word centers along with synthetic durations for each
    word based on the length of the word

    Parameters
    ----------
    aois : pandas.DataFrame
        a dataframe containing the AOIs

    Returns
    ----------
    results : list
        a list of word center coordinates and durations
    """

    results = []

    for index, row in aois.iterrows():
        x, y, height, width, token = (
            row["x"],
            row["y"],
            row["height"],
            row["width"],
            row["word"],
        )

        duration = get_duration_from_length(token)

        center = [int(x + width // 2), int(y + height // 2), duration]

        if center not in results:
            results.append(center)

    return results


def find_word_centers_and_duration_MET(aois):
    """
    returns a list of word centers along with synthetic durations for each
    word based on the width of the word

    Parameters
    ----------
    aois : pandas.DataFrame
        a dataframe containing the AOIs

    Returns
    ----------
    results : list
        a list of word center coordinates and durations
    """

    results = []

    for index, row in aois.iterrows():
        x, y, height, width = row["x"], row["y"], row["height"], row["width"]

        center = [int(x + width // 2), int(y + height // 2), width * 10]

        if center not in results:
            results.append(center)

    return results


def find_word_centers_and_EZ_duration(aois):
    """
    returns a list of word centers along with durations for each
    word based on the EZ Reader model

    Parameters
    ----------
    aois : pandas.DataFrame
        a dataframe containing the AOIs

    Returns
    ----------
    results : list
        a list of word center coordinates and EZ reader durations
    """

    results = []

    for index, row in aois.iterrows():
        x, y, height, width = row["x"], row["y"], row["height"], row["width"]

        duration = row["FFD"]

        center = [int(x + width // 2), int(y + height // 2), int(duration)]

        if center not in results:
            results.append(center)

    return results


def overlap(fix, AOI):
    """
    Checks if a fixation is within an AOI

    Parameters
    ----------
    fix : list
        a fixation

    aois : pandas.DataFrame
        a dataframe containing a single AOI

    Returns
    ----------
    results : bool
        True if the fixation is within the AOI, False otherwise
    """
    
    box_x = AOI.x
    box_y = AOI.y
    box_w = AOI.width
    box_h = AOI.height

    if fix[0] >= box_x and fix[0] <= box_x + box_w \
    and fix[1] >= box_y and fix[1] <= box_y + box_h:
        return True

    else:
        
        return False
    

def distance(fix1, fix2):

    return ((fix1[0] - fix2[0])**2 + (fix1[1] - fix2[1])**2)**0.5


def correction_quality(aois, original_fixations, corrected_fixations):
    """
    returns the correction quality by comparing the original fixations to the
    corrected fixations

    Parameters
    ----------
    aois : pandas.DataFrame
        a dataframe containing the AOIs

    original_fixations : list
        a list of original fixations

    corrected_fixations : list
        a list of corrected fixations

    Returns
    ----------
    quality : float
        the correction quality as a percentage

    results : list
        a list where 1 indicates a match and 0 indicates a mismatch
    """
        
    match = 0
    total_fixations = len(original_fixations)
    results = [0] * total_fixations

    for index, fix in enumerate(original_fixations):
        for _, row in aois.iterrows():
            if ((overlap(fix, row) and overlap(corrected_fixations[index], row)) 
                or distance(fix, corrected_fixations[index]) < 11):
                match += 1
                results[index] = 1
                break

    quality = match / total_fixations

    return quality, results


def get_fixation_line(fixation, aoi):
    """
    returns the line number of the fixation, or None

    Parameters
    ----------
    fixation : list
        a fixation

    aois : pandas.DataFrame
        a dataframe containing the AOIs

    Returns
    ----------
         : int
        the line number of the fixuation or None
    """

    for index, row in aoi.iterrows():
        aoi_y = row['y']
        aoi_height = row['height']
        if fixation[1] > aoi_y and fixation[1] < aoi_y + aoi_height:
            return int(row['name'].split(' ')[1])
        
    return None


def correction_quality_line(aois, original_fixations, corrected_fixations):
    """
    returns the correction quality by comparing the line of the original 
    fixations to the line of the corrected fixations

    Parameters
    ----------
    aois : pandas.DataFrame
        a dataframe containing the AOIs

    original_fixations : list
        a list of original fixations

    corrected_fixations : list
        a list of corrected fixations

    Returns
    ----------
    quality : float
        the correction quality as a percentage

    results : list
        a list where 1 indicates a match and 0 indicates a mismatch
    """
        
    match = 0
    total_fixations = len(original_fixations)
    results = [0] * total_fixations

    for index, fix in enumerate(original_fixations):
        if get_fixation_line(fix, aois) == get_fixation_line(corrected_fixations[index], aois):
            match += 1
            results[index] = 1


    quality = match / total_fixations

    return quality, results


def slice_regressions(fixation_list, line_ys):
    """
    splits regressions from the rest of the fixations

    Parameters
    ----------
    fixation_list : list
        a list of fixations

    line_ys : list
        a list of line Ys

    Returns
    ----------
    only_regressions : list
        a list of fixations that are regressions
    
    without_regressions : list
        a list of fixations that are not regressions
    
    regs_index : list
        a list of indices of the regressions
    """

    in_regression = False
    fixation_before_regression = fixation_list[0]

    only_regressions = []
    regs_index = []
    without_regressions = []

    # find line height
    line_height = 50

    # if len(line_ys) > 2:
    #     line_height = line_ys[2] - line_ys[1]
    # elif len(line_ys) > 1:
    #     line_height = line_ys[1] - line_ys[0]

    # calculate mean line height
    line_heights = []
    for i in range(len(line_ys)-1):
        line_heights.append(line_ys[i+1] - line_ys[i])

    if len(line_heights) > 0:
        line_height = sum(line_heights)/len(line_heights)
    else:
        line_height = 50


    # record last fixation
    last_fixation = fixation_list[0]

    for index, fixation in enumerate(fixation_list):
        x, y = fixation[0], fixation[1]
        last_x, last_y = last_fixation[0], last_fixation[1]

        # regression found
        if not in_regression and (
            (y < last_y - line_height )#/ 2)
            or (x < last_x - line_height / 2 and y <= last_y + line_height / 2)
        ):
            in_regression = True
            fixation_before_regression = last_fixation

        # not in regression any more
        if in_regression and (
            (y > fixation_before_regression[1] + line_height / 2)
            or (x > fixation_before_regression[0] and y >= fixation_before_regression[1])
        ):
            in_regression = False

            only_regressions.pop()
            regs_index.pop()
            without_regressions.append(last_fixation)

        if in_regression:
            only_regressions.append(fixation)
            regs_index.append(index)
        else:
            without_regressions.append(fixation)

        last_fixation = fixation

    return only_regressions, without_regressions, regs_index


def slice_regressions_arabic(fixation_list, line_ys):
    """
    splits regressions from the rest of the fixations in reading from right 
    to left

    Parameters
    ----------
    fixation_list : list
        a list of fixations

    line_ys : list
        a list of line Ys

    Returns
    ----------
    only_regressions : list
        a list of fixations that are regressions
    
    without_regressions : list
        a list of fixations that are not regressions
    
    regs_index : list
        a list of indices of the regressions
    """

    in_regression = False
    fixation_before_regression = fixation_list[0]

    only_regressions = []
    regs_index = []
    without_regressions = []

    # find line height
    # find line height
    line_height = 50

    if len(line_ys) > 2:
        line_height = line_ys[2] - line_ys[1]
    elif len(line_ys) > 1:
        line_height = line_ys[1] - line_ys[0]

    # record last fixation
    last_fixation = fixation_list[0]

    for index, fixation in enumerate(fixation_list):
        x, y = fixation[0], fixation[1]
        last_x, last_y = last_fixation[0], last_fixation[1]

        # regression found
        if not in_regression and (
            (y < last_y - line_height / 2)
            or (x > last_x + line_height / 2 and y <= last_y + line_height / 2)
        ):
            in_regression = True
            fixation_before_regression = last_fixation

        # not in regression any more
        if in_regression and (
            (y > fixation_before_regression[1] + line_height / 2)
            or (
                x < fixation_before_regression[0] and y >= fixation_before_regression[1]
            )
        ):
            in_regression = False

            only_regressions.pop()
            regs_index.pop()
            without_regressions.append(last_fixation)

        if in_regression:
            only_regressions.append(fixation)
            regs_index.append(index)
        else:
            without_regressions.append(fixation)

        last_fixation = fixation

    return only_regressions, without_regressions, regs_index


def add_regs(corrected, regs, regs_indexs):
    """
    reattach regressions to a list of fixations

    Parameters
    ----------
    corrected : list
        a list of fixations

    regs : list
        a list of fixations that are regressions

    regs_indexs : list
        a list of indices of the regressions

    Returns
    ----------
    results : list
        a list of fixations with regressions reattached
    """
        
    results = corrected.copy()

    count = 0

    for index in regs_indexs:
        results.insert(index, regs[count])
        count += 1

    return results


def warp_regs(error_test, line_ys, word_centers, algorithm):
    """
    hybrid(warp+chain) algorithm that applies warp to non-regressions then chain

    Parameters
    ----------
    error_test : list
        a list of fixations

    line_ys : list
        a list of line Ys

    word_centers : list
        a list of word centers

    algorithm : function
        a function that takes a list of fixations and a list of line Ys and
        returns a list of corrected fixations

    Returns
    ----------
    results : list
        a list of corrected fixations
    """

    # remove regressions    
    only_regressions, without_regressions, regs_index = slice_regressions(error_test, line_ys)
    
    # apply basic warp
    np_array = np.array(without_regressions.copy(), dtype=int)        
    warp_correction = algo.warp(np_array, word_centers)
    warp_correction = warp_correction.tolist()

    # combine warp correction with regression
    combined = add_regs(warp_correction, only_regressions, regs_index)
    
    # apply regress to regressions
    np_array = np.array(combined.copy(), dtype=int)
    
    #if len(only_regressions) > 0:
    result = algorithm(np_array, line_ys)
    
    return result


def warp_regs_chain(error_test, line_ys, word_centers):
    """
    hybrid(warp+chain) algorithm that applies warp to non-regressions then chain

    Parameters
    ----------
    error_test : list
        a list of fixations

    line_ys : list
        a list of line Ys

    word_centers : list
        a list of word centers

    Returns
    ----------
    results : list
        a list of corrected fixations
    """
        
    # remove regressions
    only_regressions, without_regressions, regs_index = slice_regressions(
        error_test, line_ys
    )

    # apply basic warp to non-regressions
    np_array = np.array(without_regressions.copy(), dtype=int)
    warp_correction = algo.warp(np_array, word_centers)
    warp_correction = warp_correction.tolist()

    # combine warp correction with regression
    combined = add_regs(warp_correction, only_regressions, regs_index)

    # apply chain
    np_array = np.array(combined.copy(), dtype=int)
    result = algo.chain(np_array, line_ys)

    return result


def warp_regs_chain_arabic(error_test, line_ys, word_centers):
    """
    hybrid(warp+chain) algorithm that applies warp to non-regressions then chain
    for reading from right to left

    Parameters
    ----------
    error_test : list
        a list of fixations

    line_ys : list
        a list of line Ys

    word_centers : list
        a list of word centers

    Returns
    ----------
    results : list
        a list of corrected fixations
    """
        
    # split regressions
    only_regressions, without_regressions, regs_index = slice_regressions_arabic(
        error_test, line_ys
    )

    # apply basic warp to non-regressions
    np_array = np.array(without_regressions.copy(), dtype=int)
    warp_correction = algo.warp(np_array, word_centers)
    warp_correction = warp_correction.tolist()

    # combine warp correction with regression
    combined = add_regs(warp_correction, only_regressions, regs_index)

    # apply chain to combined
    np_array = np.array(combined.copy(), dtype=int)
    result = algo.chain(np_array, line_ys)

    return result


def warp_regs_regress(error_test, line_ys, word_centers):
    """
    hybrid(warp+regress) algorithm that applies warp to non-regressions and 
    regress to the regression

    Parameters
    ----------
    error_test : list
        a list of fixations

    line_ys : list
        a list of line Ys

    word_centers : list
        a list of word centers

    Returns
    ----------
    results : list
        a list of corrected fixations
    """
        
    only_regressions, without_regressions, regs_index = slice_regressions(
        error_test, line_ys
    )

    # apply basic warp
    np_array = np.array(without_regressions.copy(), dtype=int)
    warp_correction = algo.warp(np_array, word_centers)
    warp_correction = warp_correction.tolist()

    # apply regress to regressions
    np_array = np.array(only_regressions.copy(), dtype=int)

    if len(only_regressions) > 0:
        only_regressions = algo.regress(np_array, line_ys)

    # add regression back to warp_correction
    result = add_regs(warp_correction, only_regressions, regs_index)

    return result


def warp_regs_regress_arabic(error_test, line_ys, word_centers):
    """
    hybrid(warp+regress) algorithm that applies warp to non-regressions and 
    regress to the regression for reading from right to left

    Parameters
    ----------
    error_test : list
        a list of fixations

    line_ys : list
        a list of line Ys

    word_centers : list
        a list of word centers

    Returns
    ----------
    results : list
        a list of corrected fixations
    """
        
    only_regressions, without_regressions, regs_index = slice_regressions_arabic(
        error_test, line_ys
    )

    # apply basic warp
    np_array = np.array(without_regressions.copy(), dtype=int)
    warp_correction = algo.warp(np_array, word_centers)
    warp_correction = warp_correction.tolist()

    # apply regress to regressions
    np_array = np.array(only_regressions.copy(), dtype=int)

    if len(only_regressions) > 0:
        only_regressions = algo.regress(np_array, line_ys)

    # add regression back to warp_correction
    result = add_regs(warp_correction, only_regressions, regs_index)

    return result


def detect_regressions(fixation_list, line_ys):
    """
    detects if a list of fixations contains regressions

    Parameters
    ----------
    fixation_list : list
        a list of fixations

    line_ys : list
        a list of line Ys

    Returns
    ----------
     : int
        returns 1 for between line regression, 
        2 for within line regression, 
        0 for no regression
    """

    # find line height
    line_height = 50

    line_heights = []
    for i in range(len(line_ys)-1):
        line_heights.append(line_ys[i+1] - line_ys[i])
    line_height = sum(line_heights)/len(line_heights)

    # record last fixation
    last_fixation = fixation_list[0]

    for index, fixation in enumerate(fixation_list):
        if index == 0:
            continue

        x, y = fixation[0], fixation[1]
        last_x, last_y = last_fixation[0], last_fixation[1]

        # between line regression
        if y < last_y - line_height:
            return 1

        # within line regression
        if (x < last_x - line_height / 2 and y <= last_y - line_height / 2):
            return 2

        last_fixation = fixation

    return 0


def detect_between_regressions(fixation_list, line_ys):
    """
    Detects between-line regressions

    Parameters
    ----------
    fixation_list : list
        a list of fixations

    line_ys : list
        a list of line Ys

    Returns
    ----------
     : bool
        returns True if there is a between-line regression, False otherwise
    """

    # find line height
    line_height = 50

    if len(line_ys) > 2:
        line_height = line_ys[2] - line_ys[1]
    elif len(line_ys) > 1:
        line_height = line_ys[1] - line_ys[0]

    # record last fixation
    last_fixation = fixation_list[0]

    for index, fixation in enumerate(fixation_list):
        if index == 0:
            continue

        x, y = fixation[0], fixation[1]
        last_x, last_y = last_fixation[0], last_fixation[1]

        if y < last_y - line_height:  # between line regression
            return True

        last_fixation = fixation

    return False


def detect_within_regressions(fixation_list, line_ys):
    """
    Detects within-line regressions

    Parameters
    ----------
    fixation_list : list
        a list of fixations

    line_ys : list
        a list of line Ys

    Returns
    ----------
     : bool
        returns True if there is a within-line regression, False otherwise
    """

    # find line height
    line_height = 50

    if len(line_ys) > 2:
        line_height = line_ys[2] - line_ys[1]
    elif len(line_ys) > 1:
        line_height = line_ys[1] - line_ys[0]

    # record last fixation
    last_fixation = fixation_list[0]

    for index, fixation in enumerate(fixation_list):
        if index == 0:
            continue

        x, y = fixation[0], fixation[1]
        last_x, last_y = last_fixation[0], last_fixation[1]

        if (
            x < last_x - line_height / 2 and y <= last_y + line_height / 2
        ):  # within line regression
            return True

        last_fixation = fixation

    return False


def detect_within_regressions_arabic(fixation_list, line_ys):
    """
    Detects within-line regressions in reading from right to left

    Parameters
    ----------
    fixation_list : list
        a list of fixations

    line_ys : list
        a list of line Ys

    Returns
    ----------
     : bool
        returns True if there is a within-line regression, False otherwise
    """

    # find line height
    line_height = 50

    if len(line_ys) > 2:
        line_height = line_ys[2] - line_ys[1]
    elif len(line_ys) > 1:
        line_height = line_ys[1] - line_ys[0]

    # record last fixation
    last_fixation = fixation_list[0]

    for index, fixation in enumerate(fixation_list):
        if index == 0:
            continue

        x, y = fixation[0], fixation[1]
        last_x, last_y = last_fixation[0], last_fixation[1]

        if (
            x > last_x + line_height / 2 and y <= last_y + line_height / 2
        ):  # within line regression
            return True

        last_fixation = fixation

    return False