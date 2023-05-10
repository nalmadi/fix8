

# function to generate fixations at the center of each word
def generate_fixations_center(aois_with_tokens):
    
    fixations = []
    
    for index, row in aois_with_tokens.iterrows():
        x, y, width, height = row['x'], row['y'], row['width'], row['height']
        
        fixation_x = x + width / 2
        fixation_y = y + height / 2
        
        fixations.append([fixation_x, fixation_y])
        
    return fixations


def generate_fixations_left(aois_with_tokens):
    
    fixations = []
    
    for index, row in aois_with_tokens.iterrows():
        x, y, width, height, token = row['x'], row['y'], row['width'], row['height'], row['token']
        
        fixation_x = x + width / 3
        fixation_y = y + height / 2
        
        fixations.append([fixation_x, fixation_y, len(token) * 50])
        
    return fixations


def generate_fixations_left_skip(aois_with_tokens):
    
    fixations = []
    word_count = 0
    skip_count = 0
    
    for index, row in aois_with_tokens.iterrows():
        x, y, width, height, token = row['x'], row['y'], row['width'], row['height'], row['token']
        
        word_count += 1
        
        fixation_x = x + width / 3
        fixation_y = y + height / 2

        if len(token) < 4 and random.random() > 0.7:
            skip_count += 1 # fixations.append([fixation_x, fixation_y])
        else:
            fixations.append([fixation_x, fixation_y])
    
    print(skip_count / word_count)
    return fixations


def generate_fixations_left_skip(aois_with_tokens, skip_probability):
    
    fixations = []
    word_count = 0
    skip_count = 0
    
    for index, row in aois_with_tokens.iterrows():
        x, y, width, height, token = row['x'], row['y'], row['width'], row['height'], row['token']
        
        word_count += 1
        
        fixation_x = x + width / 3
        fixation_y = y + height / 2

        if random.random() < skip_probability:
            skip_count += 1 # fixations.append([fixation_x, fixation_y])
        else:
            fixations.append([fixation_x, fixation_y])
    
    #print(skip_count / word_count)
    return fixations



def generate_fixations_left_skip_regression(aois_with_tokens):
    
    fixations = []
    word_count = 0
    skip_count = 0
    regress_count = 0
    
    aoi_list = aois_with_tokens.values.tolist()
    
    index = 0
    
    while index < len(aoi_list):
        x, y, width, height, token = aoi_list[index][2], aoi_list[index][3], aoi_list[index][4], aoi_list[index][5], aoi_list[index][7]
        
        word_count += 1
        
        fixation_x = x + width / 3 + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)

        last_skipped = False

        # skipping
        if len(token) < 5 and random.random() < 0.3:
            skip_count += 1 # fixations.append([fixation_x, fixation_y])
            last_skipped = True
        else:
            fixations.append([fixation_x, fixation_y, len(token) * 50])
            last_skipped = False
        
        # regressions    
        if  random.random() > 0.96:
            index -= random.randint(1, 10)

            if index < 0:
                index = 0

            regress_count += 1
        
        index += 1
            
    
    skip_probability = skip_count / word_count
    
    return fixations


def generate_fixed_regression(aois_with_tokens):
    
    fixations = [[196, 169],
    [319, 169],
    [414, 169],
    [481, 169],
    [550, 169],
    [674, 169],
    [778, 169],
    [826, 169],
    [890, 169],
    [948, 169],
    [996, 169],
    [208, 219],
    [319, 219],
    [430, 219],
    [598, 219],
    [717, 219],
    [785, 219],
    [901, 219],
    [1005, 219],
    [163, 268],
    [244, 268],
    [346, 268],
    [444, 268],
    [517, 268],
        [598, 219],
        [717, 219],
        [785, 219],
        [901, 219],
        [1005, 219],
    [565, 268],
    [666, 268],
    [798, 268],
    [881, 268],
    [945, 268],
    [1013, 268],
    [183, 318],
    [273, 318],
    [373, 318],
        [666, 268],
        [798, 268],
    [487, 318],
    [595, 318],
    [679, 318],
    [761, 318],
    [842, 318],
    [901, 318],
    [980, 318],
    [178, 368],
    [252, 368],
    [325, 368],
    [436, 368],
    [579, 368],
    [689, 368],
    [822, 368],
    [955, 368],
    [1019, 368],
    [215, 417],
    [372, 417],
    [491, 417],
        [980, 318],
        [178, 368],
    [579, 417],
    [660, 417],
    [766, 417]]
    
    
    return fixations


def generate_fixations_left_regression(aois_with_tokens, regression_probability):
    
    fixations = []
    word_count = 0
    regress_count = 0
    
    aoi_list = aois_with_tokens.values.tolist()
    
    index = 0
    
    while index < len(aoi_list):
        x, y, width, height, token = aoi_list[index][2], aoi_list[index][3], aoi_list[index][4], aoi_list[index][5], aoi_list[index][7]
        
        word_count += 1
        
        fixation_x = x + width / 3  + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)

        fixations.append([fixation_x, fixation_y, len(token) * 50])
        
        if  random.random() < regression_probability/5:
            index -= random.randint(1, 10)
            if index < 0:
            	index = 0
            regress_count += 1
        
        index += 1
    
    return fixations


def within_line_regression(aois_with_tokens, regression_probability):
    
    fixations = []
    word_count = 0
    
    aoi_list = aois_with_tokens.values.tolist()
    
    index = 0
    
    while index < len(aoi_list):
        x, y, width, height, token = aoi_list[index][2], aoi_list[index][3], aoi_list[index][4], aoi_list[index][5], aoi_list[index][7]
        
        #print(aoi_list[index][1])
        line = int(str(aoi_list[index][1]).split(' ')[1])

        word_count += 1
        
        fixation_x = x + width / 3  + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)

        fixations.append([fixation_x, fixation_y, len(token) * 50])
        
        if  random.random() < regression_probability/10:
            

            rand_index = random.randint(0, index)

            while int(str(aoi_list[rand_index][1]).split(' ')[1]) != line:
                rand_index = random.randint(0, index)


            index = rand_index
        
        index += 1
    
    return fixations


def between_line_regression(aois_with_tokens, regression_probability):
    
    fixations = []
    word_count = 0
    
    aoi_list = aois_with_tokens.values.tolist()
    
    index = 0
    
    while index < len(aoi_list):
        x, y, width, height, token = aoi_list[index][2], aoi_list[index][3], aoi_list[index][4], aoi_list[index][5], aoi_list[index][7]
        
        #print(aoi_list[index][1])
        line = int(str(aoi_list[index][1]).split(' ')[1])

        word_count += 1
        
        fixation_x = x + width / 3  + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)

        fixations.append([fixation_x, fixation_y, len(token) * 50])
        
        if  random.random() < regression_probability/10:
            

            rand_index = random.randint(0, index)

            attempts = 0

            while int(str(aoi_list[rand_index][1]).split(' ')[1]) == line and attempts < 10:
                rand_index = random.randint(0, index)
                attempts += 1

            if attempts != 10:
                index = rand_index
        
        index += 1
    
    return fixations



def error_offset(x_offset, y_offset, fixations):
    '''creates error to move fixations (shift in dissertation)'''
    
    results = []

    for fix in fixations:

        x, y = fix[0], fix[1]
        results.append([x + x_offset, y + y_offset, fix[2]])
    
    return results

# noise
import random

def error_noise(y_noise_probability, y_noise, duration_noise, fixations):
    '''creates a random error moving a percentage of fixations '''
    
    results = []
    
    for fix in fixations:

        x, y, duration = fix[0], fix[1], fix[2]

        # should be 0.1 for %10
        duration_error = int(duration * duration_noise)

        duration += random.randint(-duration_error, duration_error)

        if duration < 0:
            duration *= -1
        
        if random.random() < y_noise_probability:
            results.append([x, y + random.randint(-y_noise, y_noise), duration])
        else:
            results.append([x, y, fix[2]])
    
    return results

# shift

def error_shift(y_shift_factor, line_ys, fixations):
    '''creates error moving fixations above or below line progressively'''

    results = []
    
    for fix in fixations:

        x, y = fix[0], fix[1]
        
        distance_from_first_line = abs(y - line_ys[0])
        
        if distance_from_first_line > 40:
            results.append([x, y + ((distance_from_first_line % 55) * y_shift_factor), fix[2]])
        else:
            results.append([x, y, fix[2]])
        
    return results


# droop

def error_droop(droop_factor, fixations):
    """creates droop error"""
    
    results = []
    
    first_x = fixations[0][0]
    
    for fix in fixations:

        x, y = fix[0], fix[1]

        results.append([x , y + ((x - first_x)/100 * droop_factor), fix[2]])
        
    return results

from PIL import ImageFont, ImageDraw, Image
from matplotlib import pyplot as plt
import numpy as np


def draw_fixation(Image_file, fixations):
    """Private method that draws the fixation, also allow user to draw eye movement order

    Parameters
    ----------
    draw : PIL.ImageDraw.Draw
        a Draw object imposed on the image

    draw_number : bool
        whether user wants to draw the eye movement number
    """

    im = Image.open(Image_file)
    draw = ImageDraw.Draw(im, 'RGBA')

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
    plt.imshow(np.asarray(im), interpolation='nearest')


def draw_correction(Image_file, fixations, match_list):
    """Private method that draws the fixation, also allow user to draw eye movement order

    Parameters
    ----------
    draw : PIL.ImageDraw.Draw
        a Draw object imposed on the image

    draw_number : bool
        whether user wants to draw the eye movement number
    """

    im = Image.open(Image_file)
    draw = ImageDraw.Draw(im, 'RGBA')

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

        # text_bound = (x + random.randint(-10, 10), y + random.randint(-10, 10))
        # text_color = (0, 0, 0, 225)
        # font = ImageFont.truetype("arial.ttf", 20)
        # draw.text(text_bound, str(index), fill=text_color,font=font)

        x0, y0 = x, y

    plt.figure(figsize=(17, 15))
    plt.imshow(np.asarray(im), interpolation='nearest')


def draw_comparison(Image_file, fixations, fixations2, match_list):
    """Private method that draws the fixation, also allow user to draw eye movement order

    Parameters
    ----------
    draw : PIL.ImageDraw.Draw
        a Draw object imposed on the image

    draw_number : bool
        whether user wants to draw the eye movement number
    """

    im = Image.open(Image_file)
    draw = ImageDraw.Draw(im, 'RGBA')

    if len(fixations[0]) == 3:
        x0, y0, duration = fixations[0]
        #print("len(fixations[0])")
    else:
        x0, y0 = fixations[0]

    for index, fixation in enumerate(fixations):
        
        if len(fixations[0]) == 3:
            #print(index, "len(fixations[0]) == 3")
            duration = fixation[2]
            if 5 * (duration / 100) < 5:
                r = 3
                #print(index, "5 * (duration / 100) < 5")
            else:
                 r = 5 * (duration / 100)
                 #print(index, "r = 5 * (duration / 100)")
        else:
            r = 8

        x = fixation[0]
        
        y = fixation[1]
        

        x2 = fixations2[index][0]
        
        y2 = fixations2[index][1]
        
  
        outline_color = (50, 255, 0, 0)
        
        if match_list[index] == 1:
            # match: green
            #print("in green")
            r = 5 
            bound = (x - r, y - r, x + r, y + r)
            fill_color = (50, 255, 0, 220)
            draw.ellipse(bound, fill=fill_color, outline=outline_color)
        elif match_list[index] == 0:
            # mismatch: blue, red
            # red
            #print("in blue, red")
            fill_color = (255, 55, 0, 220)
            r = 10
            bound = (x - r, y - r, x + r, y + r)
            draw.ellipse(bound, fill=fill_color, outline=outline_color)

            # blue
            fill_color = (5, 55, 255, 220)
            bound = (x2 - r, y2 - r, x2 + r, y2 + r)
            draw.ellipse(bound, fill=fill_color, outline=outline_color)
        else: # if match_list[index] == 2
            # done fixations: light-blue, light-red
            # light-red
            #print("in blue, red")
            fill_color = (255,105,180, 220)
            r = 10
            bound = (x - r, y - r, x + r, y + r)
            draw.ellipse(bound, fill=fill_color, outline=outline_color)

            # light-blue
            fill_color = (135, 206, 250, 220)
            bound = (x2 - r, y2 - r, x2 + r, y2 + r)
            draw.ellipse(bound, fill=fill_color, outline=outline_color)



        #draw.ellipse(bound, fill=fill_color, outline=outline_color)

        bound = (x0, y0, x, y)
        line_color = (255, 155, 0, 155)
        draw.line(bound, fill=line_color, width=2)

        # text_bound = (x + random.randint(-10, 10), y + random.randint(-10, 10))
        # text_color = (0, 0, 0, 225)
        # font = ImageFont.truetype("arial.ttf", 20)
        # draw.text(text_bound, str(index), fill=text_color,font=font)

        x0, y0 = x, y

    plt.figure(figsize=(17, 15))
    plt.imshow(np.asarray(im), interpolation='nearest')


def find_lines_Y(aois):
    ''' returns a list of line Ys '''
    
    results = []
    
    for index, row in aois.iterrows():
        y, height = row['y'], row['height']
        
        if y + height / 2 not in results:
            results.append(y + height / 2)
            
    return results



def find_word_centers(aois):
    ''' returns a list of word centers '''
    
    results = []
    
    for index, row in aois.iterrows():
        x, y, height, width = row['x'], row['y'], row['height'], row['width']
        
        center = [int(x + width // 2), int(y + height // 2)]
        
        if center not in results:
            results.append(center)
            
    return results


def find_word_centers_and_duration(aois):
    ''' returns a list of word centers '''
    
    results = []
    
    for index, row in aois.iterrows():
        x, y, height, width, token = row['x'], row['y'], row['height'], row['width'], row['token']
        
        center = [int(x + width // 2), int(y + height // 2), len(token) * 50]

        if center not in results:
            results.append(center)
    
    #print(results)
    return results


def find_word_centers_and_EZ_duration(aois):
    ''' returns a list of word centers '''
    
    results = []
    
    for index, row in aois.iterrows():
        x, y, height, width = row['x'], row['y'], row['height'], row['width']
        
        duration = row['GD']

        center = [int(x + width // 2), int(y + height // 2), int(duration)]

        if center not in results:
            results.append(center)
    
    #print(results)
    return results


def overlap(fix, AOI):
    """checks if fixation is within AOI"""
    
    box_x = AOI.x
    box_y = AOI.y
    box_w = AOI.width
    box_h = AOI.height

    if fix[0] >= box_x and fix[0] <= box_x + box_w \
    and fix[1] >= box_y and fix[1] <= box_y + box_h:
        return True
    
    else:
        
        return False
 

from math import sqrt

def compare_corrections(aois, original_fixations, corrected_fixations):
    
    match = 0
    total_fixations = len(original_fixations)
    results = [0] * total_fixations
    
    for index, fix in enumerate(original_fixations):

        dist = sqrt( (corrected_fixations[index][0] - fix[0])**2 + (corrected_fixations[index][1] - fix[1])**2 )
        
        for _, row  in aois.iterrows():
            
            if overlap(fix, row) and overlap(corrected_fixations[index], row):
                match += 1
                results[index] = 1


    for index, value in enumerate(results):

        if value == 0:

            dist = sqrt( (corrected_fixations[index][0] - original_fixations[index][0])**2 + (corrected_fixations[index][1] - original_fixations[index][1])**2 )

            if dist < 10:
                match += 1
                results[index] = 1

    return match / total_fixations, results

    
def correction_quality(aois, original_fixations, corrected_fixations):
    
    match = 0
    total_fixations = len(original_fixations)
    results = [0] * total_fixations
    
    for index, fix in enumerate(original_fixations):
        
        for _, row  in aois.iterrows():
            
            if overlap(fix, row) and overlap(corrected_fixations[index], row):
                match += 1
                results[index] = 1
                
    return match / total_fixations, results


import drift_algorithms as algo


def slice_regressions(fixation_list, line_ys):
    ''' V3 of function to slice regressions '''
    
    in_regression = False
    fixation_before_regression = fixation_list[0]
    
    only_regressions = []
    regs_index = []
    without_regressions = []
    
    # find line height
    line_height = 30
    
    if len(line_ys) > 1: 
        line_height = line_ys[1] - line_ys[0]

    # record last fixation
    last_fixation = fixation_list[0]
    
    for index, fixation in enumerate(fixation_list):
        
        x, y = fixation[0], fixation[1]
        last_x, last_y = last_fixation[0], last_fixation[1]
        
        # regression found
        if ( not in_regression 
            and ((y < last_y - line_height/2) 
                 or (x < last_x - line_height/2 
                     and y <= last_y + line_height/2))):  
            in_regression = True
            fixation_before_regression = last_fixation
            #only_regressions.append(last_fixation)
            #regs_index.append(index-1)
            
        # not in regression any more
        if in_regression and ((y > fixation_before_regression[1] + line_height/2) 
                              or (x > fixation_before_regression[0] and y >= fixation_before_regression[1])):
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
    
    results = corrected.copy()

    count = 0
    
    for index in regs_indexs:
        results.insert(index, regs[count])
        count += 1
    
    return results
    

def warp_regs(error_test, line_ys, word_centers):

    # iron out fixations using regress
    # np_array = np.array(error_test, dtype=int)

    # if len(error_test[0]) > 2:
    #     # remove duration
    #     durations = np.delete(np_array, 0, 1)
    #     durations = np.delete(durations, 0, 1)
    #     np_array = np.delete(np_array, 2, 1)

    # fixations = algo.regress(np_array, line_ys)

    # results = []
    # # reattach durations
    # if len(error_test[0]) > 2:
    #     for index, fix in enumerate(fixations):
    #         results.append([fix[0], fix[1], error_test[index][2]])
    
    #     fixations = results

    # remove regressions    
    only_regressions, without_regressions, regs_index = slice_regressions(error_test, line_ys)
    
    
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
    ''' function to detect regressions in code '''
    
    # find line height
    line_height = line_ys[1] - line_ys[0]

    # record last fixation
    last_fixation = fixation_list[0]
    
    for index, fixation in enumerate(fixation_list):
        
        x, y = fixation[0], fixation[1]
        last_x, last_y = last_fixation[0], last_fixation[1]
        
        if y < last_y - line_height/2:  # between line regression
            #print("between", index)
            return True
        
        if x < last_x - line_height/2 and y <= last_y + line_height/2:  # within line regression
            #print("within", index)
            return True
        
        last_fixation = fixation
    
    return False


def adaptive(error_test, line_ys, word_centers):


    # if distances between lines are too small:
    # # iron out fixations using regress
    np_array = np.array(error_test, dtype=int)

    if len(error_test[0]) > 2:
        # remove duration
        durations = np.delete(np_array, 0, 1)
        durations = np.delete(durations, 0, 1)
        np_array = np.delete(np_array, 2, 1)

    fixations = algo.regress(np_array, line_ys)

    results = []
    # reattach durations
    if len(error_test[0]) > 2:
        for index, fix in enumerate(fixations):
            results.append([fix[0], fix[1], error_test[index][2]])
    
        fixations = results

    # REGS   = WARP+REG
    # NO-REG = WARP

    print("regression:", detect_regressions(fixations, line_ys))
    if detect_regressions(fixations, line_ys):

        return warp_regs(error_test, line_ys, word_centers)

    else:

        return algo.warp(error_test, word_centers)
