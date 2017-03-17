import os
from os import listdir
from os.path import isfile, join
import sys
import datetime
from subprocess import call
import itertools
from PIL import Image
import math
import argparse

g_time_start = datetime.datetime.now()

def prependZero(i):
    i_str = str(i)
    if i < 10:
        i_str = "0" + str(i_str)
    return i_str

def runTexturePackerWithImages(src_dir, out_dir, prefix, n, images, width, height):
    run = ["TexturePacker",
           "--size-constraints", "AnySize",
           "--texture-format", "png",
           "--algorithm", "Basic",
           "--trim-mode", "None",
           "--pack-mode", "Best",
           "--basic-sort-by", "Name",
           "--disable-rotation",
           "--width", str(width),
           "--height", str(height),
           "--max-width", "2048",
           "--max-height", "2048",
           "--extrude", "0",
           "--disable-auto-alias",
           "--png-opt-level", "0",
           "--sheet", out_dir + "/" + prefix + prependZero(n) + ".png"]
    for image in images:
        l = src_dir + "/" + image
        run.extend([l])
    call(run)

def grouper(n, iterable):
    args = [iter(iterable)] * n
    return ([e for e in t if e is not None] for t in itertools.zip_longest(*args))

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--srcdir", help="source directory")
    parser.add_argument("-o", "--outdir", help="ouput directory")
    parser.add_argument("-g", "--gamecode", help="game code")
    parser.add_argument("-p", "--prefix", help="file prefix")
    parser.add_argument("-cx", "--countx", help="image count per row")
    parser.add_argument("-cy", "--county", help="image count per column")
    parser.parse_args()
    args = parser.parse_args()
    return args

def checkArgs(args):
    if(args.srcdir is not None):
        if(not os.path.isdir(args.srcdir)):
            return "Source directory not found."
    if(args.countx is None):
        return "Missing -cx arg."
    if(args.county is None):
        return "Missing -cy arg."
    if(args.countx is not None):
        if(not str(args.countx).isdigit()):
            return "Invalid arg: cx."
    if(args.county is not None):
        if(not str(args.county).isdigit()):
            return "Invalid arg: cy."
    return None

def initVariables(args):
    src_dir = str(args.srcdir)
    out_dir = str(args.outdir)
    gamecode = args.gamecode
    prefix = args.prefix
    
    if(src_dir is None):
        src_dir = "."
    if(out_dir is None):
        out_dir = "."
    if(gamecode is None):
        gamecode = ""
    else:
        gamecode += "_"
    if(prefix is None):
        prefix = ""
    else:
        prefix += "_"

    return src_dir, out_dir, gamecode, prefix

def computePackable(imgcount, cx, cy):

    return cx * cy, cx, cy

def stampTimeStart():
    g_time_start = datetime.datetime.now()

def stampTimeEnd():
    time_finished = datetime.datetime.now()
    timedelta = time_finished - g_time_start
    print("FINISHED TIME(s): " + str(timedelta.total_seconds()))

def main(args):
    stampTimeStart()

    src_dir, out_dir, gamecode, prefix = initVariables(args)

    dir_path = os.path.dirname(os.path.realpath(__file__)) + "/" + src_dir
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    png_list = [f for f in listdir(dir_path) if isfile(join(dir_path, f)) and f.endswith('.png')]

    # sample image
    img_count = len(png_list)
    print ("Frames found: " + str(img_count) + "\n")
    if(img_count == 0):
        return;

    img = Image.open(src_dir + "/" + png_list[0])
    img_width, img_height = img.size;

    packable, packable_x, packable_y = computePackable(img_count, int(args.countx), int(args.county))
    png_groups = list(grouper(packable, png_list))

    index = 1
    for png_group in png_groups:
        runTexturePackerWithImages(src_dir, out_dir, prefix, index, png_group, packable_x * img_width, packable_y * img_height)
        index += 1

    entry = create_resource_database_entries(png_list, img_count, out_dir, gamecode, prefix, img_width, img_height,
                                             packable_x, packable_y);

    write_text_to_file('resourceDatabase.cs', entry)
    stampTimeEnd()

def write_text_to_file(file, txt):
    f = open(file, 'w+')
    f.write(txt)
    f.close()

def create_resource_database_entries(images, img_count, output_dir, gamecode, prefix, width, height, packable_x, packable_y):
    entry = ""
    group_index = 1
    for group in images:
        if group == images[-1]:
            packable_y = int(math.ceil(len(group) / packable_x))
        entry += create_resource_database_image_map(output_dir, gamecode, prefix, group_index, width, height, packable_x,
                                                    packable_y)
        group_index += 1
    entry += create_resource_database_image_map_link(output_dir, gamecode, prefix, group_index)
    entry += create_resource_database_animation(output_dir, gamecode, prefix, img_count)
    return entry

def create_resource_database_image_map(output_dir, gamecode, prefix, index, width, height, packable_x, packable_y):
    entry = "\tnew t2dImageMapDatablock(" + gamecode + prefix + prependZero(index) + "ImageMap" + ") {"
    entry += "\n\t\timageName = \"./t2dTexture/" + output_dir + "/" + prefix + prependZero(index) + ".png\";"
    entry += "\n\t\timageMode = \"CELL\";"
    entry += "\n\t\tframeCount = \"-1\";"
    entry += "\n\t\tfilterMode = \"SMOOTH\";"
    entry += "\n\t\tfilterPad = \"1\";"
    entry += "\n\t\tpreferPerf = \"1\";"
    entry += "\n\t\tcellRowOrder = \"1\";"
    entry += "\n\t\tcellOffsetX = \"0\";"
    entry += "\n\t\tcellOffsetY = \"0\";"
    entry += "\n\t\tcellStrideX = \"0\";"
    entry += "\n\t\tcellStrideY = \"0\";"
    entry += "\n\t\tcellCountX = \"" + str(packable_x) + "\";"
    entry += "\n\t\tcellCountY = \"" + str(packable_y) + "\";"
    entry += "\n\t\tcellWidth = \"" + str(width) + "\";"
    entry += "\n\t\tcellHeight = \"" + str(height) + "\";"
    entry += "\n\t\tpreload = \"1\";"
    entry += "\n\t\tallowUnload = \"0\";"
    entry += "\n\t\tforce16Bit = \"0\";"
    entry += "\n\t};"
    entry += "\n"
    return entry

def create_resource_database_image_map_link(output_dir, gamecode, prefix, total_imagemaps):
    entry = "\tnew t2dImageMapDatablock("+ gamecode + prefix + "linkImage" + ") {";
    entry += "\n\t\timageMode = \"LINK\";"
    entry += "\n\t\tframeCount = \"-1\";"
    entry += "\n\t\tfilterMode = \"SMOOTH\";"
    entry += "\n\t\tfilterPad = \"1\";"
    entry += "\n\t\tpreferPerf = \"1\";"
    entry += "\n\t\tcellRowOrder = \"1\";"
    entry += "\n\t\tcellOffsetX = \"0\";"
    entry += "\n\t\tcellOffsetY = \"0\";"
    entry += "\n\t\tcellStrideX = \"0\";"
    entry += "\n\t\tcellStrideY = \"0\";"
    entry += "\n\t\tcellCountX = \"-1\";"
    entry += "\n\t\tcellCountY = \"-1\";"
    entry += "\n\t\tcellWidth = \"0\";"
    entry += "\n\t\tcellHeight = \"0\";"

    link_image_maps = ""
    for index in range(1, total_imagemaps):
        link_image_maps += gamecode + prefix + prependZero(index) + "ImageMap" + " "
    link_image_maps = link_image_maps.rstrip()
    entry += "\n\t\tlinkImageMaps = \"" + link_image_maps + "\";"

    entry += "\n\t\tpreload = \"1\";"
    entry += "\n\t\tallowUnload = \"0\";"
    entry += "\n\t\tforce16Bit = \"0\";"
    entry += "\n\t};"
    entry += "\n"
    return entry

def create_resource_database_animation(output_dir, gamecode, prefix, img_count):
    entry = "\tnew t2dAnimationDatablock(" + gamecode + prefix + "linkImageAnimation" + ") {";
    entry += "\n\t\timageMap = \"" + gamecode + prefix + "linkImage" + "\";"

    frames = ""
    for i in range(0, img_count):
        frames += str(i) + " "
    frames = frames.rstrip()

    entry += "\n\t\tanimationFrames = \"" + frames + "\";"
    entry += "\n\t\tanimationTime = \"3.0\";"
    entry += "\n\t\tanimationCycle = \"0\";"
    entry += "\n\t\trandomStart = \"0\";"
    entry += "\n\t\tstartFrame = \"0\";"
    entry += "\n\t\tanimationPingPong = \"0\";"
    entry += "\n\t\tanimationReverse = \"0\";"
    entry += "\n\t};"
    entry += "\n"
    return entry

if __name__ == "__main__" and len(sys.argv) > 1:
    args = parseArgs()
    error = checkArgs(args)

    if(error is not None):
        print("Error: " + error)
    else:
        main(args)