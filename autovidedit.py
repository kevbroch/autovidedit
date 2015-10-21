#!/usr/bin/env python
import argparse
import logging
import sys

from moviepy.editor import *

def time2secs(time):
    """Converts hrs:mins:secs to secs."""
    alist = list(int(x) for x in time.split(':'))
    return alist[0] * 3600 + alist[1] * 60 + alist[2]

def parse_args():
    parser = argparse.ArgumentParser(description='Auto Cut Video with MoviePy')
    parser.add_argument('-i', '--infile',)
    parser.add_argument('-s', '--start',)
    parser.add_argument('-d', '--duration',)
    parser.add_argument('-t', '--text',)
    args = vars(parser.parse_args())
    return args

def main():
    args = parse_args()

    start_secs = time2secs(args['start'])
    dur_secs = int(args['duration'])
    end_secs = start_secs + dur_secs

    video = VideoFileClip(args['infile']).subclip(start_secs, end_secs)
    txt_clip = (TextClip(args['text'], fontsize=60, color='white')
                .set_position('center')
                .set_duration(dur_secs))

    result = CompositeVideoClip([video,txt_clip])
    result.write_videofile("test.webm",fps=25)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0);
