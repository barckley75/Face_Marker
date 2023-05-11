def _seconds(value, framerate):
    if isinstance(value, str):  # value seems to be a timestamp
        _zip_ft = zip((3600, 60, 1, 1/framerate), value.split(':'))
        return sum(f * float(t) for f, t in _zip_ft)
    elif isinstance(value, (int, float)):  # frames
        return value / framerate
    else:
        return 0


def _timecode(seconds, framerate):
    return '{h:02d}:{m:02d}:{s:02d}:{f:02d}' \
        .format(h=int(seconds/3600),
                m=int(seconds/60 % 60),
                s=int(seconds % 60),
                f=round((seconds-int(seconds))*framerate))


def frames_to_timecode(frames, framerate, start=None):
    return _timecode(_seconds(frames, framerate), + _seconds(start, framerate))
