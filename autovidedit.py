from moviepy.editor import *
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Auto Cut Video with MoviePy')
    parser.add_argument('-i', '--infile',)
    args = vars(parser.parse_args())

    video = VideoFileClip(args['infile']).subclip(130,142)
    txt_clip = (TextClip("6yd run", fontsize=60, color='white')
                .set_position('center')
                .set_duration(2))

    result = CompositeVideoClip([video,txt_clip])
    result.write_videofile("test.webm",fps=25)
