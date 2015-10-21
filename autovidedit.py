#!/usr/bin/env python
import argparse
import commands
import csv
import logging
import moviepy.video.fx.all as vfx
import os
import sys
import time

from moviepy.editor import *

MOVIEPATH = "/Users/tbroch/Movies/personal"

# TODOS
# 
# - opencv coolness
#   - find duration by utilizing transitions I insert into videos as
#   - some sort of significant delta
#   - find player by number and insert slowmo / overlay to
#     identify them.  Replay, zoom-ins also cool.
# - add parse arg for raw-only (no fx) to just produce the subclips or
#   perhaps a whole separate script to merge the pieces

def parse_args():
    parser = argparse.ArgumentParser(description='Auto Cut Video with MoviePy')

    # required
    parser.add_argument('-p', '--player')
    parser.add_argument('-c', '--csv',)

    # deprecated : only if you're testing w/o csv
    parser.add_argument('-i', '--infile',)
    parser.add_argument('-s', '--start',)
    parser.add_argument('-d', '--duration',)
    parser.add_argument('-t', '--text',)
    args = vars(parser.parse_args())
    return args

def time2secs(time):
    """Converts hrs:mins:secs to secs."""
    alist = list(int(x) for x in time.split(':'))
    return alist[0] * 3600 + alist[1] * 60 + alist[2]

def csvdate2filedate(date):
    """Converts mm/dd/yyyy -> yyyy-mm-dd."""
    try:
        alist = list(int(x) for x in date.split('/'))
        rv = "%04d-%02d-%02d" % (alist[2], alist[0], alist[1])
    except ValueError,IndexError:
        rv = "NODATE"
    return rv

def find_file(division, opponent, date):
    if division.lower().startswith('j'):
        path = "%s/2015_gbjpw/%s_gbjpw_vs_%s.mp4" % \
            (MOVIEPATH,
            csvdate2filedate(date),
            opponent)
    else:
        path = "%s/2015_gbpw/%s_gbpw_vs_%s.mp4" % \
            (MOVIEPATH,
            csvdate2filedate(date),
            opponent)

    logging.debug("path:%s", path)
    if not os.path.exists(path):
        return None
    return path

# 0 - division
# 1 - opponent
# 2 - date
# 3 - youtube
# 4 - yards
# 5 - description
# 6 - player number
# 7 - Offense or Defense
# 8 - start time hr:min:sec
# 9 - duration
# 10 - url link1
# 11 - url link2
def parse_csv(infile, player_num):
    rv_list = []
    with open(infile, 'r') as fd:
        rd_list = csv.reader(fd, delimiter=',')
        base_len = 0
        for i,row in enumerate(rd_list):
            if i == 0:
                # header
                base_len = len(row)
                continue
            if len(row) != base_len:
                continue

            # valid row
            logging.debug('%d: %s', i, ','.join(row))

            if player_num != row[6]:
                continue
            
            # build description text
            txt = '#' + row[6]
            if row[7].lower().startswith('o'):
                txt += ':offense'
            elif row[7].lower().startswith('s'):
                txt += ':steams'
            else:
                txt += ':defense'

            if row[5] != '':
                txt += ":%s" % row[5]

            if row[8] == '' or row[2] == '':
                logging.warn('Skipping %s line ... date/time missing', row)
                continue

            time_idx = time.mktime(
                time.strptime("%s %s" % (csvdate2filedate(row[2]),
                row[8]), "%Y-%m-%d %H:%M:%S"))
            movie = find_file(row[0], row[1], row[2])
            logging.debug("time_idx:%d movie:%s", time_idx, movie)
            if movie is None:
                logging.warn('Unable to find movie for division:%s vs '
                    '%s on %s', row[0], row[1], row[2])
                break
            # movie, descrip, time, duration
            rv_list.append([time_idx, movie, txt, row[8], row[9]])

    return rv_list

def main():
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG)
    
    if args['csv']:
        csv_list = parse_csv(args['csv'], args['player'])
        fname_root = os.path.splitext(args['csv'])[0]
    else:
        # expect the full movie too
        if not os.path.exists(args['infile']):
            logging.fatal('Need valid -i <infile> w/ -s,-d,-t params')
            sys.exit(-1)
        csv_list = [0, args['infile'],
                    args['text'],
                    args['start'],
                    args['duration']]
        fname_root = "test"

    file_dict = dict()
    for i, (time_idx, movie, txt, start, dur) in enumerate(csv_list):
        logging.debug('movie:%s start:%s dur:%s descrip:%s',
                      movie, start, dur, txt)

        start_secs = time2secs(start)
        dur_secs = int(dur)
        #dur_secs = 5
        text_dur_secs = 3 if (dur_secs - 3) >= 0 else dur_secs
        end_secs = start_secs + dur_secs

        logging.debug('start:%d end:%d', start_secs, end_secs)
        video = VideoFileClip(movie).subclip(start_secs, end_secs)
        video = (video.fx( vfx.freeze, freeze_duration=1 )
                      #.fx( vfx.freeze, t=dur_secs, freeze_duration=1)
                 )
        video = (video.fx( vfx.fadeout, 0.75)
                 )
        txt_clip1 = (TextClip(txt, fontsize=54, color='white', kerning=4)
                    .set_position('bottom')
                    .set_duration(text_dur_secs))
        txt_clip2 = (TextClip(txt, fontsize=60, color='black')
                    .set_position('bottom')
                    .set_duration(text_dur_secs))
        clips = [video, txt_clip2, txt_clip1]

        
        fname = "%s_%d.mp4" % (fname_root, time_idx)
        if not os.path.exists(fname):
            result = CompositeVideoClip(clips)
            result.write_videofile(fname,fps=25, audio=False)
        file_dict[time_idx] = 'file %s' % fname
        #break
        
    merge = True
    if merge:
        flist_name = '%s_highlight.list' % fname_root
        with open(flist_name, 'w') as fd:
            for time_idx in sorted(file_dict):
                fd.write(file_dict[time_idx] + '\n')

        final_video = '%s_highlight.mp4' % fname_root
        if os.path.isfile(final_video):
            os.remove(final_video)

        cmd = 'ffmpeg -f concat -i %s -c copy %s_highlight.mp4' % \
            (flist_name, fname_root)
        logging.info(cmd)
        (rv, out) = commands.getstatusoutput(cmd)
        logging.info(out)
        
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0);
