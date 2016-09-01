from Station import Station


class Train(object):
    ghost_lines = ("ghost", "train", "--", "no")

    def __new__(cls, src=None, dst=None, line=None, time=None):
        # Make into station objects if not already
        if isinstance(src, (str, unicode)):
            src = Station(cls.fix_farragut(src, line))
        if isinstance(dst, (str, unicode)):
            dst = Station(cls.fix_farragut(dst, line))

        # Check that specified line is one serviced by specified station (if not a ghost line)
        if line and line.lower() not in Train.ghost_lines and line not in src.lines:
            raise SrcLineError

        # Check that specified line is one serviced by specified destination (if not a ghost line)
        if dst:
            if line and line.lower() not in Train.ghost_lines and line not in dst.lines:
                raise DstLineError

            # Check that src and dst stations connect
            line_intersect = list(set(src.lines) & set(dst.lines))
            if not line_intersect:
                raise StationIntersectionError

            # Check that src and dst stations aren't the same
            if src.name == dst.name:
                raise SameStationError

        # If supplied parameters pass all checks, Create an instance of Train
        return super(Train, cls).__new__(cls)

    def __init__(self, src=None, dst=None, line=None, time=None):
        self.line = line
        self.src = Station(self.fix_farragut(src, line)) if isinstance(src, (str, unicode)) else src
        self.dst = Station(self.fix_farragut(dst, line)) if isinstance(dst, (str, unicode)) else dst
        self.time = time
        self.direction = self.calculate_trajectory()
        self.stops_left = self.calculate_stops_left()

    @staticmethod
    def fix_farragut(station_name, line):
        if "farragut" in station_name:
            if line == "red":
                station_name = "farragut north"
            elif line in ("blue", "orange", "silver"):
                station_name = "farragut west"
            else:
                station_name = "unknown"
        return station_name

    def calculate_trajectory(self):
        if self.dst is None:
            return None
        elif self.line in Train.ghost_lines:
            return "any"
        else:
            src_index, dst_index = self.calc_indices()
            trajectory = dst_index - src_index

            if trajectory == 0:
                return "no_movement"
            elif trajectory > 0:
                return "positive"
            else:
                return "negative"

    def calculate_stops_left(self):
        if self.dst is None:
            return None
        elif self.line in Train.ghost_lines:
            return "ghost"
        else:
            src_index, dst_index = self.calc_indices()
            stops_left = abs(src_index-dst_index)
        return stops_left

    def calc_indices(self):
        if self.line:
            src_index = int(self.src.line_index(self.line))
            dst_index = int(self.dst.line_index(self.line))
        else:
            src_index = int(self.src.line_index(self.src.lines[0]))
            dst_index = int(self.dst.line_index(self.dst.lines[0]))
        return src_index, dst_index


class StationIntersectionError(ValueError):
    pass


class SrcLineError(ValueError):
    pass


class DstLineError(ValueError):
    pass


class SameStationError(ValueError):
    pass
