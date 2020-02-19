# Copyright 2019 Pascal Audet
#
# This file is part of RfPy.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""

Module containing the main utility functions used in the `RfPy` scripts
that accompany this package.

"""

# -*- coding: utf-8 -*-
from obspy import UTCDateTime
from numpy import nan, isnan
from obspy.core import Stream, read


def get_calc_options():
    """
    Get Options from :class:`~optparse.OptionParser` objects.

    This function is used for data processing on-the-fly (requires web connection)

    """

    from optparse import OptionParser, OptionGroup
    from os.path import exists as exist
    from obspy import UTCDateTime
    from numpy import nan

    parser = OptionParser(
        usage="Usage: %prog [options] <station database>",
        description="Script used to download and pre-process " +
        "three-component (Z, N, and E), seismograms for individual " +
        "events and calculate teleseismic P-wave receiver functions" +
        "This version requests data on the fly for a given date " +
        "range. Data are requested from the internet using the " +
        "client services framework. The stations are processed one " +
        "by one and the data are stored to disk.")

    # General Settings
    parser.add_option(
        "--keys",
        action="store",
        type=str,
        dest="stkeys",
        default="",
        help="Specify a comma separated list of station keys for " +
        "which to perform the analysis. These must be " +
        "contained within the station database. Partial keys will " +
        "be used to match against those in the dictionary. For " +
        "instance, providing IU will match with all stations in " +
        "the IU network [Default processes all stations in the database]")
    parser.add_option(
        "-v", "-V", "--verbose",
        action="store_true",
        dest="verb",
        default=False,
        help="Specify to increase verbosity.")
    parser.add_option(
        "-O", "--overwrite",
        action="store_true",
        dest="ovr",
        default=False,
        help="Force the overwriting of pre-existing data. " +
        "[Default False]")

    # Server Settings
    ServerGroup = OptionGroup(
        parser,
        title="Server Settings",
        description="Settings associated with which "
        "datacenter to log into.")
    ServerGroup.add_option(
        "-S", "--Server",
        action="store",
        type=str,
        dest="Server",
        default="IRIS",
        help="Specify the server to connect to. Options include: " +
        "BGR, ETH, GEONET, GFZ, INGV, IPGP, IRIS, KOERI, " +
        "LMU, NCEDC, NEIP, NERIES, ODC, ORFEUS, RESIF, SCEDC, USGS, USP. " +
        "[Default IRIS]")
    ServerGroup.add_option(
        "-U", "--User-Auth",
        action="store",
        type=str,
        dest="UserAuth",
        default="",
        help="Enter your IRIS Authentification Username and Password " +
        "(--User-Auth='username:authpassword') to " +
        "access and download restricted data. " +
        "[Default no user and password]")

    # Database Settings
    DataGroup = OptionGroup(
        parser,
        title="Local Data Settings",
        description="Settings associated with defining " +
        "and using a local data base of pre-downloaded " +
        "day-long SAC files.")
    DataGroup.add_option(
        "--local-data",
        action="store",
        type=str,
        dest="localdata",
        default=None,
        help="Specify a comma separated list of paths containing " +
        "day-long sac files of data already downloaded. " +
        "If data exists for a seismogram is already present on disk, " +
        "it is selected preferentially over downloading " +
        "the data using the Client interface")
    DataGroup.add_option(
        "--no-data-zero",
        action="store_true",
        dest="ndval",
        default=False,
        help="Specify to force missing data to be set as zero, rather " +
        "than default behaviour which sets to nan.")
    DataGroup.add_option(
        "--no-local-net",
        action="store_false",
        dest="useNet",
        default=True,
        help="Specify to prevent using the Network code in the " +
        "search for local data (sometimes for CN stations " +
        "the dictionary name for a station may disagree with that " +
        "in the filename. [Default Network used]")

    # Event Selection Criteria
    EventGroup = OptionGroup(
        parser,
        title="Event Settings",
        description="Settings associated with refining " +
        "the events to include in matching event-station pairs")
    EventGroup.add_option(
        "--start",
        action="store",
        type=str,
        dest="startT",
        default="",
        help="Specify a UTCDateTime compatible string representing " +
        "the start time for the event search. This will override any " +
        "station start times. [Default start date of station]")
    EventGroup.add_option(
        "--end",
        action="store",
        type=str,
        dest="endT",
        default="",
        help="Specify a UTCDateTime compatible string representing " +
        "the end time for the event search. This will override any " +
        "station end times [Default end date of station]")
    EventGroup.add_option(
        "--reverse", "-R",
        action="store_true",
        dest="reverse",
        default=False,
        help="Reverse order of events. Default behaviour starts at " +
        "oldest event and works towards most recent. Specify reverse " +
        "order and instead the program will start with the most recent " +
        "events and work towards older")
    EventGroup.add_option(
        "--minmag",
        action="store",
        type=float,
        dest="minmag",
        default=6.0,
        help="Specify the minimum magnitude of event for which to search. " +
        "[Default 6.0]")
    EventGroup.add_option(
        "--maxmag",
        action="store",
        type=float,
        dest="maxmag",
        default=9.0,
        help="Specify the maximum magnitude of event for which to search. " +
        "[Default None, i.e. no limit]")

    # Geometry Settings
    PhaseGroup = OptionGroup(
        parser,
        title="Geometry Settings",
        description="Settings associatd with the "
        "event-station geometries for the specified phase")
    PhaseGroup.add_option(
        "--phase",
        action="store",
        type=str,
        dest="phase",
        default='P',
        help="Specify the phase name to use. Be careful with the distance. "+
        "setting. Options are 'P' or 'PP'. [Default 'P']")
    PhaseGroup.add_option(
        "--mindist",
        action="store",
        type=float,
        dest="mindist",
        default=30.,
        help="Specify the minimum great circle distance (degrees) between " +
        "the station and event. [Default 30.]")
    PhaseGroup.add_option(
        "--maxdist",
        action="store",
        type=float,
        dest="maxdist",
        default=90.,
        help="Specify the maximum great circle distance (degrees) between " +
        "the station and event. [Default 90.]")

    # Constants Settings
    ConstGroup = OptionGroup(
        parser,
        title='Parameter Settings',
        description="Miscellaneous default values and settings")
    ConstGroup.add_option(
        "--sampling-rate",
        action="store",
        type=float,
        dest="new_sampling_rate",
        default=5.,
        help="Specify new sampling rate in Hz. [Default 5.]")
    ConstGroup.add_option(
        "--dts",
        action="store",
        type=float,
        dest="dts",
        default=150.,
        help="Specify the window length in sec (symmetric about arrival " +
        "time). [Default 150.]")
    ConstGroup.add_option(
        "--align",
        action="store",
        type=str,
        dest="align",
        default=None,
        help="Specify component alignment key. Can be either " +
        "ZRT, LQT, or PVH. [Default ZRT]")
    ConstGroup.add_option(
        "--vp",
        action="store",
        type=float,
        dest="vp",
        default=6.0,
        help="Specify near-surface Vp to use with --align=PVH (km/s). "+
        "[Default 6.0]")
    ConstGroup.add_option(
        "--vs",
        action="store",
        type=float,
        dest="vs",
        default=3.5,
        help="Specify near-surface Vs to use with --align=PVH (km/s). "+
        "[Default 3.5]")
    ConstGroup.add_option(
        "--dt-snr",
        action="store",
        type=float,
        dest="dt_snr",
        default=30.,
        help="Specify the window length over which to calculate " +
        "the SNR in sec. [Default 30.]")
    ConstGroup.add_option(
        "--fmin",
        action="store",
        type=float,
        dest="fmin",
        default=0.05,
        help="Specify the minimum frequency corner for SNR and CC " +
        "filter (Hz). [Default 0.05]")
    ConstGroup.add_option(
        "--fmax",
        action="store",
        type=float,
        dest="fmax",
        default=1.0,
        help="Specify the maximum frequency corner for SNR and CC " +
        "filter (Hz). [Default 1.0]")

    # Constants Settings
    DeconGroup = OptionGroup(
        parser,
        title='Deconvolution Settings',
        description="Parameters for deconvolution")
    DeconGroup.add_option(
        "--method",
        action="store",
        dest="method",
        type=str,
        default="wiener",
        help="Specify the deconvolution method. Available methods " +
        "include 'wiener', 'water' and 'multitaper'. [Default 'wiener']")
    DeconGroup.add_option(
        "--gfilt",
        action="store",
        dest="gfilt",
        type=float,
        default=None,
        help="Specify the Gaussian filter width in Hz. " +
        "[Default None]")
    DeconGroup.add_option(
        "--wlevel",
        action="store",
        dest="wlevel",
        type=float,
        default=0.01,
        help="Specify the water level, used in the 'water' method. "+
        "[Default 0.01]")



    parser.add_option_group(ServerGroup)
    parser.add_option_group(DataGroup)
    parser.add_option_group(EventGroup)
    parser.add_option_group(PhaseGroup)
    parser.add_option_group(ConstGroup)
    parser.add_option_group(DeconGroup)

    (opts, args) = parser.parse_args()

    # Check inputs
    if len(args) != 1:
        parser.error("Need station database file")
    indb = args[0]
    if not exist(indb):
        parser.error("Input file " + indb + " does not exist")

    # create station key list
    if len(opts.stkeys) > 0:
        opts.stkeys = opts.stkeys.split(',')

    # construct start time
    if len(opts.startT) > 0:
        try:
            opts.startT = UTCDateTime(opts.startT)
        except:
            parser.error(
                "Cannot construct UTCDateTime from start time: " +
                opts.startT)
    else:
        opts.startT = None

    # construct end time
    if len(opts.endT) > 0:
        try:
            opts.endT = UTCDateTime(opts.endT)
        except:
            parser.error(
                "Cannot construct UTCDateTime from end time: " +
                opts.endT)
    else:
        opts.endT = None

    # Parse User Authentification
    if not len(opts.UserAuth) == 0:
        tt = opts.UserAuth.split(':')
        if not len(tt) == 2:
            parser.error(
                "Error: Incorrect Username and Password " +
                "Strings for User Authentification")
        else:
            opts.UserAuth = tt
    else:
        opts.UserAuth = []

    # Parse Local Data directories
    if opts.localdata is not None:
        opts.localdata = opts.localdata.split(',')
    else:
        opts.localdata = []

    # Check NoData Value
    if opts.ndval:
        opts.ndval = 0.0
    else:
        opts.ndval = nan

    # Check distances for selected phase
    if opts.phase not in ['P', 'PP']:
        parser.error(
            "Error: choose between 'P' and 'PP'.")
    if opts.phase == 'P':
        if opts.mindist < 30. or opts.maxdist > 100.:
            parser.error(
                "Distances should be between 30 and 100 deg. for "+
                "teleseismic 'P' waves.")
    elif opts.phase == 'PP':
        if opts.mindist < 100. or opts.maxdist > 180.:
            parser.error(
                "Distances should be between 100 and 180 deg. for "+
                "teleseismic 'PP' waves.")

    # Check alignment options
    if opts.align is None:
        opts.align = 'ZRT'
    elif opts.align not in ['ZRT', 'LQT', 'PVH']:
        parser.error(
            "Error: Incorrect alignment specifier. Should be " +
            "either 'ZRT', 'LQT', or 'PVH'.")

    if opts.dt_snr > opts.dts:
        opts.dt_snr = opts.dts - 10.
        print("SNR window > data window. Defaulting to data " +
              "window minus 10 sec.")

    if opts.method not in ['wiener', 'water', 'multitaper']:
        parser.error(
            "Error: 'method' should be either 'wiener', 'water' or " +
            "'multitaper'")

    return (opts, indb)


def get_recalc_options():
    """
    Get Options from :class:`~optparse.OptionParser` objects.

    This function is used for data processing on-the-fly (requires web connection)

    """

    from optparse import OptionParser, OptionGroup
    from os.path import exists as exist
    from obspy import UTCDateTime
    from numpy import nan

    parser = OptionParser(
        usage="Usage: %prog [options] <station database>",
        description="Script used to download and pre-process " +
        "three-component (Z, N, and E), seismograms for individual " +
        "events and calculate teleseismic P-wave receiver functions" +
        "This version requests data on the fly for a given date " +
        "range. Data are requested from the internet using the " +
        "client services framework. The stations are processed one " +
        "by one and the data are stored to disk.")

    # General Settings
    parser.add_option(
        "--keys",
        action="store",
        type=str,
        dest="stkeys",
        default="",
        help="Specify a comma separated list of station keys for " +
        "which to perform the analysis. These must be " +
        "contained within the station database. Partial keys will " +
        "be used to match against those in the dictionary. For " +
        "instance, providing IU will match with all stations in " +
        "the IU network [Default processes all stations in the database]")

    # Constants Settings
    ConstGroup = OptionGroup(
        parser,
        title='Parameter Settings',
        description="Miscellaneous default values and settings")
    ConstGroup.add_option(
        "--align",
        action="store",
        type=str,
        dest="align",
        default=None,
        help="Specify component alignment key. Can be either " +
        "ZRT, LQT, or PVH. [Default ZRT]")
    ConstGroup.add_option(
        "--vp",
        action="store",
        type=float,
        dest="vp",
        default=6.0,
        help="Specify near-surface Vp to use with --align=PVH (km/s). "+
        "[Default 6.0]")
    ConstGroup.add_option(
        "--vs",
        action="store",
        type=float,
        dest="vs",
        default=3.5,
        help="Specify near-surface Vs to use with --align=PVH (km/s). "+
        "[Default 3.5]")
    ConstGroup.add_option(
        "--dt-snr",
        action="store",
        type=float,
        dest="dt_snr",
        default=30.,
        help="Specify the window length over which to calculate " +
        "the SNR in sec. [Default 30.]")
    ConstGroup.add_option(
        "--fmin",
        action="store",
        type=float,
        dest="fmin",
        default=0.05,
        help="Specify the minimum frequency corner for SNR " +
        "filter (Hz). [Default 0.05]")
    ConstGroup.add_option(
        "--fmax",
        action="store",
        type=float,
        dest="fmax",
        default=1.0,
        help="Specify the maximum frequency corner for SNR " +
        "filter (Hz). [Default 1.0]")

    # Constants Settings
    DeconGroup = OptionGroup(
        parser,
        title='Deconvolution Settings',
        description="Parameters for deconvolution")
    DeconGroup.add_option(
        "--method",
        action="store",
        dest="method",
        type=str,
        default="wiener",
        help="Specify the deconvolution method. Available methods " +
        "include 'wiener', 'water' and 'multitaper'. [Default 'wiener']")
    DeconGroup.add_option(
        "--gfilt",
        action="store",
        dest="gfilt",
        type=float,
        default=None,
        help="Specify the Gaussian filter width in Hz. " +
        "[Default None]")
    DeconGroup.add_option(
        "--wlevel",
        action="store",
        dest="wlevel",
        type=float,
        default=0.01,
        help="Specify the water level, used in the 'water' method. "+
        "[Default 0.01]")

    parser.add_option_group(ConstGroup)
    parser.add_option_group(DeconGroup)

    (opts, args) = parser.parse_args()

    # Check inputs
    if len(args) != 1:
        parser.error("Need station database file")
    indb = args[0]
    if not exist(indb):
        parser.error("Input file " + indb + " does not exist")

    # create station key list
    if len(opts.stkeys) > 0:
        opts.stkeys = opts.stkeys.split(',')

    if opts.align is None:
        opts.align = 'ZRT'
    elif opts.align not in ['ZRT', 'LQT', 'PVH']:
        parser.error(
            "Error: Incorrect alignment specifier. Should be " +
            "either 'ZRT', 'LQT', or 'PVH'.")

    if opts.method not in ['wiener', 'water', 'multitaper']:
        parser.error(
            "Error: 'method' should be either 'wiener', 'water' or " +
            "'multitaper'")

    return (opts, indb)


def get_hk_options():
    """
    Get Options from :class:`~optparse.OptionParser` objects.

    This function is used for data processing on-the-fly (requires web connection)

    """

    from optparse import OptionParser, OptionGroup
    from os.path import exists as exist
    from obspy import UTCDateTime
    from numpy import nan

    parser = OptionParser(
        usage="Usage: %prog [options] <station database>",
        description="Script used to process receiver function data " +
        "for H-k stacking.")

    # General Settings
    parser.add_option(
        "--keys",
        action="store",
        type=str,
        dest="stkeys",
        default="",
        help="Specify a comma separated list of station keys for " +
        "which to perform the analysis. These must be " +
        "contained within the station database. Partial keys will " +
        "be used to match against those in the dictionary. For " +
        "instance, providing IU will match with all stations in " +
        "the IU network [Default processes all stations in the database]")
    parser.add_option(
        "-v", "-V", "--verbose",
        action="store_true",
        dest="verb",
        default=False,
        help="Specify to increase verbosity.")
    parser.add_option(
        "-O", "--overwrite",
        action="store_true",
        dest="ovr",
        default=False,
        help="Force the overwriting of pre-existing data. " +
        "[Default False]")

    # Event Selection Criteria
    TimeGroup = OptionGroup(
        parser,
        title="Time Settings",
        description="Settings associated with refining " +
        "the times to include in searching for receiver function data")
    TimeGroup.add_option(
        "--start",
        action="store",
        type=str,
        dest="startT",
        default="",
        help="Specify a UTCDateTime compatible string representing " +
        "the start time for the search. This will override any " +
        "station start times. [Default start date of station]")
    TimeGroup.add_option(
        "--end",
        action="store",
        type=str,
        dest="endT",
        default="",
        help="Specify a UTCDateTime compatible string representing " +
        "the end time for the search. This will override any " +
        "station end times [Default end date of station]")

    PreGroup = OptionGroup(
        parser,
        title='Pre-processing Settings',
        description="Options for pre-processing of receiver function " +
        "data prior to H-k stacking")
    PreGroup.add_option(
        "--freqs",
        action="store",
        type=str,
        dest="freqs",
        default=None,
        help="Specify a list of two floats with the minimum and maximum " +
        "frequency corner for the bandpass filter (Hz). [Default [0.05, 0.5]]")
    PreGroup.add_option(
        "--nbaz",
        action="store",
        dest="nbaz",
        type=int,
        default=36,
        help="Specify integer number of back-azimuth bins to consider. " +
        "[Default 36]")
    PreGroup.add_option(
        "--nslow",
        action="store",
        dest="nslow",
        type=int,
        default=40,
        help="Specify integer number of slowness bins to consider. " +
        "[Default 40]")
    PreGroup.add_option(
        "--snr",
        action="store",
        type=float,
        dest="snr",
        default=5.,
        help="Specify the SNR threshold for extracting receiver functions. " +
        "[Default 5.]")

## JMG ##
    PreGroup.add_option(
        "--snrh",
        action="store",
        type=float,
        dest="snrh",
        default=5.,
        help="Specify the horizontal component SNR threshold for extracting receiver functions. " +
        "[Default 5.]")

    PreGroup.add_option(
        "--cc",
        action="store",
        type=float,
        dest="cc",
        default=0.5,
        help="Specify the CC threshold for extracting receiver functions. " +
        "[Default 0.5]")
## JMG ##

    PreGroup.add_option(
        "--copy",
        action="store_true",
        dest="copy",
        default=False,
        help="Set this option to use a copy of the radial component " +
        "filtered at different corners for the Pps and Pss phases. " +
        "[Default False]")
    PreGroup.add_option(
        "--freqs_copy",
        action="store",
        dest="freqs_copy",
        type=str,
        default=None,
        help="Specify a list of two floats with minimum and maximum" +
        "frequency for the copies stream (Hz). [Default [0.05, 0.35]]")

    HKGroup = OptionGroup(
        parser,
        title='Settings for H-k Stacking',
        description="Specify parameters of H-k search, including" +
        "bounds on search, weights, type of stacking, etc.")
    HKGroup.add_option(
        "--hbound",
        action="store",
        type=str,
        dest="hbound",
        default=None,
        help="Specify a list of two floats with minimum and maximum" +
        "bounds on Moho depth (H, in km). [Default [20., 50.]]")
    HKGroup.add_option(
        "--dh",
        action="store",
        type=float,
        dest="dh",
        default=0.5,
        help="Specify search interval for H (km). [Default 0.5]")
    HKGroup.add_option(
        "--kbound",
        action="store",
        type=str,
        dest="kbound",
        default=None,
        help="Specify a list of two floats with minimum and maximum" +
        "bounds on Vp/Vs (k). [Default [1.56, 2.1]]")
    HKGroup.add_option(
        "--dk",
        action="store",
        type=float,
        dest="dk",
        default=0.02,
        help="Specify search interval for k. [Default 0.02]")
    HKGroup.add_option(
        "--weights",
        action="store",
        type=str,
        dest="weights",
        default=None,
        help="Specify a list of three floats with for Ps, Pps and Pass " +
        "weights in final stack. [Default [0.5, 2., -1.]]")
    HKGroup.add_option(
        "--type",
        action="store",
        type=str,
        dest="typ",
        default="sum",
        help="Specify type of final stacking. Options are: 'sum' for " +
        "a weighted average (using weights), or 'prod' for the product " +
        "of positive values in stacks. [Default 'sum']")
    HKGroup.add_option(
        "--save",
        action="store_true",
        dest="save",
        default=False,
        help="Set this option to save the HkStack object to file. "+
        "[Default doesn't save]")

    # Constants Settings
    ModelGroup = OptionGroup(
        parser,
        title='Model Settings',
        description="Miscellaneous default values and settings")
    ModelGroup.add_option(
        "--vp",
        action="store",
        type=float,
        dest="vp",
        default=6.0,
        help="Specify mean crustal Vp (km/s). [Default 6.0]")
    ModelGroup.add_option(
        "--strike",
        action="store",
        type=float,
        dest="strike",
        default=None,
        help="Specify the strike of dipping Moho. [Default None]")
    ModelGroup.add_option(
        "--dip",
        action="store",
        type=float,
        dest="dip",
        default=None,
        help="Specify the dip of dipping Moho. [Default None]")

    PlotGroup = OptionGroup(
        parser,
        title='Settings for plotting results',
        description="Specify parameters for plotting the H-k stacks.")
    PlotGroup.add_option(
        "--plot",
        action="store_true",
        dest="plot",
        default=False,
        help="Set this option to produce a plot of the stacks [Default " +
        "does not produce plot]")
    PlotGroup.add_option(
        "--save-plot",
        action="store_true",
        dest="save_plot",
        default=False,
        help="Set this option to save the plot [Default doesn't save]")
    PlotGroup.add_option(
        "--title",
        action="store",
        type=str,
        dest="title",
        default="",
        help="Specify plot title [Default has no title]")
    PlotGroup.add_option(
        "--format",
        action="store",
        type=str,
        dest="form",
        default="png",
        help="Specify format of figure. Can be any one of the valid" +
        "matplotlib formats: 'png', 'jpg', 'eps', 'pdf'. [Default 'png']")

    parser.add_option_group(TimeGroup)
    parser.add_option_group(PreGroup)
    parser.add_option_group(HKGroup)
    parser.add_option_group(ModelGroup)
    parser.add_option_group(PlotGroup)

    (opts, args) = parser.parse_args()

    # Check inputs
    if len(args) != 1:
        parser.error("Need station database file")
    indb = args[0]
    if not exist(indb):
        parser.error("Input file " + indb + " does not exist")

    # create station key list
    if len(opts.stkeys) > 0:
        opts.stkeys = opts.stkeys.split(',')

    # construct start time
    if len(opts.startT) > 0:
        try:
            opts.startT = UTCDateTime(opts.startT)
        except:
            parser.error(
                "Cannot construct UTCDateTime from start time: " +
                opts.startT)
    else:
        opts.startT = None

    # construct end time
    if len(opts.endT) > 0:
        try:
            opts.endT = UTCDateTime(opts.endT)
        except:
            parser.error(
                "Cannot construct UTCDateTime from end time: " +
                opts.endT)
    else:
        opts.endT = None

    if opts.strike is None and opts.dip is None:
        opts.calc_dip = False
        opts.nbaz = None
    elif opts.strike is None or opts.dip is None:
        parser.error("Specify both strike and dip for this type " +
                     "of analysis")
    else:
        opts.calc_dip = True

    if opts.freqs is None:
        opts.freqs = [0.05, 0.5]
    else:
        opts.freqs = [float(val) for val in opts.freqs.split(',')]
        opts.freqs = sorted(opts.freqs)
        if (len(opts.freqs)) != 2:
            parser.error(
                "Error: --freqs should contain 2 " +
                "comma-separated floats")

    if opts.copy:
        if opts.freqs_copy is None:
            opts.freqs_copy = [0.05, 0.35]
        else:
            opts.freqs_copy = [float(val)
                               for val in opts.freqs_copy.split(',')]
            opts.freqs_copy = sorted(opts.freqs_copy)
            if (len(opts.freqs_copy)) != 2:
                parser.error(
                    "Error: --freqs_copy should contain 2 " +
                    "comma-separated floats")

    if opts.hbound is None:
        opts.hbound = [20., 50.]
    else:
        opts.hbound = [float(val) for val in opts.hbound.split(',')]
        opts.hbound = sorted(opts.hbound)
        if (len(opts.hbound)) != 2:
            parser.error(
                "Error: --hbound should contain 2 " +
                "comma-separated floats")

    if opts.kbound is None:
        opts.kbound = [1.56, 2.1]
    else:
        opts.kbound = [float(val) for val in opts.kbound.split(',')]
        opts.kbound = sorted(opts.kbound)
        if (len(opts.kbound)) != 2:
            parser.error(
                "Error: --kbound should contain 2 " +
                "comma-separated floats")

    if opts.weights is None:
        opts.weights = [0.5, 2.0, -1.0]
    else:
        opts.weights = [float(val) for val in opts.weights.split(',')]
        opts.weights = sorted(opts.weights)
        if (len(opts.weights)) != 3:
            parser.error(
                "Error: --weights should contain 3 " +
                "comma-separated floats")

    return (opts, indb)


def get_harmonics_options():
    """
    Get Options from :class:`~optparse.OptionParser` objects.

    This function is used for data processing on-the-fly (requires web connection)

    """

    from optparse import OptionParser, OptionGroup
    from os.path import exists as exist
    from obspy import UTCDateTime
    from numpy import nan

    parser = OptionParser(
        usage="Usage: %prog [options] <station database>",
        description="Script used to process receiver function data " +
        "for harmonic decomposition.")

    # General Settings
    parser.add_option(
        "--keys",
        action="store",
        type=str,
        dest="stkeys",
        default="",
        help="Specify a comma separated list of station keys for " +
        "which to perform the analysis. These must be " +
        "contained within the station database. Partial keys will " +
        "be used to match against those in the dictionary. For " +
        "instance, providing IU will match with all stations in " +
        "the IU network [Default processes all stations in the database]")
    parser.add_option(
        "-v", "-V", "--verbose",
        action="store_true",
        dest="verb",
        default=False,
        help="Specify to increase verbosity.")
    parser.add_option(
        "-O", "--overwrite",
        action="store_true",
        dest="ovr",
        default=False,
        help="Force the overwriting of pre-existing data. " +
        "[Default False]")

    # Event Selection Criteria
    TimeGroup = OptionGroup(
        parser,
        title="Time Settings",
        description="Settings associated with refining " +
        "the times to include in searching for receiver function data")
    TimeGroup.add_option(
        "--start",
        action="store",
        type=str,
        dest="startT",
        default="",
        help="Specify a UTCDateTime compatible string representing " +
        "the start time for the search. This will override any " +
        "station start times. [Default start date of station]")
    TimeGroup.add_option(
        "--end",
        action="store",
        type=str,
        dest="endT",
        default="",
        help="Specify a UTCDateTime compatible string representing " +
        "the end time for the search. This will override any " +
        "station end times [Default end date of station]")

    PreGroup = OptionGroup(
        parser,
        title='Pre-processing Settings',
        description="Options for pre-processing of receiver function " +
        "data prior to harmonic decomposition")
    PreGroup.add_option(
        "--freqs",
        action="store",
        type=str,
        dest="freqs",
        default=None,
        help="Specify a list of two floats with the minimum and maximum " +
        "frequency corner for the bandpass filter (Hz). [Default [0.05, 0.5]]")
    PreGroup.add_option(
        "--bin",
        action="store",
        dest="nbin",
        type=int,
        default=None,
        help="Specify integer number of back-azimuth bins to consider " +
        "(typically 36 or 72). [Default does not bin data]")
    PreGroup.add_option(
        "--snr",
        action="store",
        type=float,
        dest="snr",
        default=5.,
        help="Specify the SNR threshold for extracting receiver functions. " +
        "[Default 5.]")

    HarmonicGroup = OptionGroup(
        parser,
        title='Settings for harmonic decomposition',
        description="Specify parameters for the decomposition, e.g. " +
        "a fixed azimuth, depth range for finding the optimal azimuth, etc.")
    HarmonicGroup.add_option(
        "--azim",
        action="store",
        type=float,
        dest="azim",
        default=None,
        help="Specify the azimuth angle along with to perform the " +
        "decomposition. [Default 0.]")
    HarmonicGroup.add_option(
        "--find-azim",
        action="store_true",
        dest="find_azim",
        default=False,
        help="Set this option to calculate the optimal azimuth. [Default " +
        "uses the '--azim' value]")
    HarmonicGroup.add_option(
        "--trange",
        action="store",
        type=str,
        dest="trange",
        default=None,
        help="Specify a list of two floats with minimum and maximum" +
        "bounds on time range for finding the optimal azimuth (sec). " +
        "[Default [0., 10.] when '--find-azim' is set]")
    HarmonicGroup.add_option(
        "--save",
        action="store_true",
        dest="save",
        default=False,
        help="Set this option to save the Harmonics object " +
        "to a pickled file. [Default does not save object]")

    PlotGroup = OptionGroup(
        parser,
        title='Settings for plotting results',
        description="Specify parameters for plotting the back-azimuth " +
        "harmonics.")
    PlotGroup.add_option(
        "--plot",
        action="store_true",
        dest="plot",
        default=False,
        help="Set this option to produce a plot of the back-azimuth harmonics")
    PlotGroup.add_option(
        "--ymax",
        action="store",
        type=float,
        dest="ymax",
        default=30.,
        help="Specify the maximum y axis value for the plot in units of the" +
        "dependent variable (e.g., sec). [Default 30.]")
    PlotGroup.add_option(
        "--scale",
        action="store",
        type=float,
        dest="scale",
        default=30.,
        help="Specify the scaling value that multiplies the amplitude " +
        "of the harmonic components. [Default 10.]")
    PlotGroup.add_option(
        "--save-plot",
        action="store_true",
        dest="save_plot",
        default=False,
        help="Set this option to save the plot [Default doesn't save]")
    PlotGroup.add_option(
        "--title",
        action="store",
        type=str,
        dest="title",
        default="",
        help="Specify plot title [Default has no title]")
    PlotGroup.add_option(
        "--format",
        action="store",
        type=str,
        dest="form",
        default="png",
        help="Specify format of figure. Can be any one of the valid" +
        "matplotlib formats: 'png', 'jpg', 'eps', 'pdf'. [Default 'png']")

    parser.add_option_group(TimeGroup)
    parser.add_option_group(PreGroup)
    parser.add_option_group(HarmonicGroup)
    parser.add_option_group(PlotGroup)

    (opts, args) = parser.parse_args()

    # Check inputs
    if len(args) != 1:
        parser.error("Need station database file")
    indb = args[0]
    if not exist(indb):
        parser.error("Input file " + indb + " does not exist")

    # create station key list
    if len(opts.stkeys) > 0:
        opts.stkeys = opts.stkeys.split(',')

    # construct start time
    if len(opts.startT) > 0:
        try:
            opts.startT = UTCDateTime(opts.startT)
        except:
            parser.error(
                "Cannot construct UTCDateTime from start time: " +
                opts.startT)
    else:
        opts.startT = None

    # construct end time
    if len(opts.endT) > 0:
        try:
            opts.endT = UTCDateTime(opts.endT)
        except:
            parser.error(
                "Cannot construct UTCDateTime from end time: " +
                opts.endT)
    else:
        opts.endT = None

    if opts.freqs is None:
        opts.freqs = [0.05, 0.5]
    else:
        opts.freqs = [float(val) for val in opts.freqs.split(',')]
        opts.freqs = sorted(opts.freqs)
        if (len(opts.freqs)) != 2:
            parser.error(
                "Error: --freqs should contain 2 " +
                "comma-separated floats")

    if opts.azim is not None and opts.find_azim:
        print("Warning: Setting both '--azim' and '--find-azim' is " +
              "conflictual. Ignoring '--find-azim'")
        opts.find_azim = False
    elif opts.azim is None and not opts.find_azim:
        opts.azim = 0.
    if opts.find_azim:
        if opts.trange is None:
            opts.trange = [0., 10.]
        else:
            print(opts.trange.split(','))
            opts.trange = [float(val) for val in opts.trange.split(',')]
            opts.trange = sorted(opts.trange)
            if (len(opts.trange)) != 2:
                parser.error(
                    "Error: --trange should contain 2 " +
                    "comma-separated floats")

    return (opts, indb)


def get_ccp_options():
    """
    Get Options from :class:`~optparse.OptionParser` objects.

    This function is used for data processing on-the-fly (requires web connection)

    """

    from optparse import OptionParser, OptionGroup
    from os.path import exists as exist
    from obspy import UTCDateTime
    from numpy import nan

    parser = OptionParser(
        usage="Usage: %prog [options] <station database>",
        description="Script used to process receiver function data " +
        "for common-conversion-point (CCP) imaging.")

    # General Settings
    parser.add_option(
        "--keys",
        action="store",
        type=str,
        dest="stkeys",
        default="",
        help="Specify a comma separated list of station keys for " +
        "which to perform the analysis. These must be " +
        "contained within the station database. Partial keys will " +
        "be used to match against those in the dictionary. For " +
        "instance, providing IU will match with all stations in " +
        "the IU network [Default processes all stations in the database]")
    parser.add_option(
        "-v", "-V", "--verbose",
        action="store_true",
        dest="verb",
        default=False,
        help="Specify to increase verbosity.")
    parser.add_option(
        "-O", "--overwrite",
        action="store_true",
        dest="ovr",
        default=False,
        help="Force the overwriting of pre-existing data. " +
        "[Default False]")

    LineGroup = OptionGroup(
        parser,
        title='Line Geometry Settings',
        description="Options for defining the line along which to " +
        "produce the CCP image")
    LineGroup.add_option(
        "--start",
        action="store",
        type=str,
        dest="coord_start",
        default=None,
        help="Specify a list of two floats with the latitude and longitude " +
        "of the start point, in this respective order. [Exception raised " +
        "if not specified]")
    LineGroup.add_option(
        "--end",
        action="store",
        dest="coord_end",
        type=str,
        default=None,
        help="Specify a list of two floats with the latitude and longitude" +
        "of the end point, in this respective order. [Exception raised " +
        "if not specified]")
    LineGroup.add_option(
        "--dz",
        action="store",
        dest="dz",
        type=int,
        default=1.,
        help="Specify vertical cell size in km. " +
        "[Default 1.]")
    LineGroup.add_option(
        "--dx",
        action="store",
        dest="dx",
        type=float,
        default=2.5,
        help="Specify horizontal cell size in km. " +
        "[Default 2.5]")

    PreGroup = OptionGroup(
        parser,
        title='Pre-processing Settings',
        description="Options for pre-processing of receiver function " +
        "data for CCP stacking")
    PreGroup.add_option(
        "--snr",
        action="store",
        type=float,
        dest="snr",
        default=5.,
        help="Specify the SNR threshold for extracting receiver functions. " +
        "[Default 5.]")
    PreGroup.add_option(
        "--f1",
        action="store",
        type=float,
        dest="f1",
        default=0.05,
        help="Specify the low frequency corner for the bandpass filter " +
        "for all phases (Hz). [Default [0.05]]")
    PreGroup.add_option(
        "--f2ps",
        action="store",
        type=float,
        dest="f2ps",
        default=0.75,
        help="Specify the high frequency corner for the bandpass filter " +
        "for the Ps phase (Hz). [Default [0.75]]")
    PreGroup.add_option(
        "--f2pps",
        action="store",
        type=float,
        dest="f2pps",
        default=0.36,
        help="Specify the high frequency corner for the bandpass filter " +
        "for the Pps phase (Hz). [Default [0.36]]")
    PreGroup.add_option(
        "--f2pss",
        action="store",
        type=float,
        dest="f2pss",
        default=0.3,
        help="Specify the high frequency corner for the bandpass filter " +
        "for the Pss phase (Hz). [Default [0.3]]")
    PreGroup.add_option(
        "--nbaz",
        action="store",
        dest="nbaz",
        type=int,
        default=36,
        help="Specify integer number of back-azimuth bins to consider. " +
        "[Default 36]")
    PreGroup.add_option(
        "--nslow",
        action="store",
        dest="nslow",
        type=int,
        default=40,
        help="Specify integer number of slowness bins to consider. " +
        "[Default 40]")
    PreGroup.add_option(
        "--wlen",
        action="store",
        dest="wlen",
        type=float,
        default=35.,
        help="Specify wavelength of P-wave as sensitivity (km). " +
        "[Default 35.]")

    CCPGroup = OptionGroup(
        parser,
        title='CCP Settings',
        description="Options for specifying the type of CCP stacking " +
        "to perform")
    CCPGroup.add_option(
        "--load",
        action="store_true",
        dest="load",
        default=False,
        help="Step 1. Set this option to load rfstreams into CCPimage "+
        "object. [Default False]")
    CCPGroup.add_option(
        "--prep",
        action="store_true",
        dest="prep",
        default=False,
        help="Step 2. Set this option to prepare CCPimage before "+
        "pre-stacking. [Default False]")
    CCPGroup.add_option(
        "--prestack",
        action="store_true",
        dest="prestack",
        default=False,
        help="Step 3. Set this option to prestack all phases before "+
        "CCP averaging. [Default False]")
    CCPGroup.add_option(
        "--ccp",
        action="store_true",
        dest="ccp",
        default=False,
        help="Step 4a. Set this option for standard CCP stacking with "+
        "multiples. [Default False]")
    CCPGroup.add_option(
        "--gccp",
        action="store_true",
        dest="gccp",
        default=False,
        help="Step 4b. Set this option for Gaussian-weighted "+
        "CCP stacking with multiples. [Default False]")
    CCPGroup.add_option(
        "--linear",
        action="store_true",
        dest="linear",
        default=False,
        help="Step 5a. Set this option to produce a linear, weighted "+
        "stack for the final [G]CCP image. [Default True unless "+
        "--phase is set]")
    CCPGroup.add_option(
        "--phase",
        action="store_true",
        dest="phase",
        default=False,
        help="Step 5b. Set this option to produce a phase weighted stack "+
        "for the final [G]CCP image. [Default False]")

    FigGroup = OptionGroup(
        parser,
        title='Figure Settings',
        description="Options for specifying the settings for the final figure")
    FigGroup.add_option(
        "--figure",
        action="store_true",
        dest="ccp_figure",
        default=False,
        help="Set this option to plot the final [G]CCP figure. " +
        "[Default False]")
    FigGroup.add_option(
        "--cbound",
        action="store",
        dest="cbound",
        type=float,
        default=None,
        help="Set the maximum value for the color palette. "+
        "[Default 0.05 for --ccp or 0.015 for --gccp]")
    FigGroup.add_option(
        "--save-fig",
        action="store_true",
        dest="save_figure",
        default=False,
        help="Set this option to save the final [G]CCP figure. "+
        "This option can only be set if --figure is also set." +
        "[Default False]")
    FigGroup.add_option(
        "--title",
        action="store",
        dest="title",
        type=str,
        default="",
        help="Set Figure title. [Default None]")
    FigGroup.add_option(
        "--format",
        action="store",
        dest="fmt",
        type=str,
        default='png',
        help="Set format of figure. You can choose among "+
        "'png', 'jpg', 'eps', 'pdf'. [Default 'png']")

    parser.add_option_group(LineGroup)
    parser.add_option_group(PreGroup)
    parser.add_option_group(CCPGroup)
    parser.add_option_group(FigGroup)

    (opts, args) = parser.parse_args()

    # Check inputs
    if len(args) != 1:
        parser.error("Need station database file")
    indb = args[0]
    if not exist(indb):
        parser.error("Input file " + indb + " does not exist")

    # create station key list
    if len(opts.stkeys) > 0:
        opts.stkeys = opts.stkeys.split(',')

    if opts.load and opts.coord_start is None:
        parser.error("--start=lon,lat is required")
    elif opts.load and opts.coord_start is not None:
        opts.coord_start = [float(val) for val in opts.coord_start.split(',')]
        if (len(opts.coord_start)) != 2:
            parser.error(
                "Error: --start should contain 2 " +
                "comma-separated floats")

    if opts.load and opts.coord_end is None:
        parser.error("--end=lon,lat is required")
    elif opts.load and opts.coord_end is not None:
        opts.coord_end = [float(val) for val in opts.coord_end.split(',')]
        if (len(opts.coord_end)) != 2:
            parser.error(
                "Error: --end should contain 2 " +
                "comma-separated floats")

    if not (opts.load or opts.prep or opts.prestack or opts.ccp
            or opts.gccp):
        parser.error(
            "Error: needs at least one CCP Setting (--load, --prep, " +
            "--prestack, --ccp or --gccp")

    if opts.linear and opts.phase:
        parser.error(
            "Error: cannot use --linear and --phase at the same time")

    if opts.ccp and not opts.linear and not opts.phase:
        opts.linear = True
    if opts.gccp and not opts.linear and not opts.phase:
        opts.phase = True

    if (opts.save_figure or opts.cbound or opts.fmt) and not opts.ccp_figure:
        print("Warning: Figure will not be produced since --figure "+
            "has not been set.")

    if opts.ccp_figure and not (opts.ccp or opts.gccp):
        parser.error(
            "Error: Cannot produce Figure without specifying the "+
            "type of stacking [--ccp or --gccp].")

    if not opts.cbound and opts.gccp:
        opts.cbound = 0.015
    elif not opts.cbound and opts.ccp:
        opts.cbound = 0.05

    return (opts, indb)


def get_plot_options():
    """
    Get Options from :class:`~optparse.OptionParser` objects.

    This function is used for data processing on-the-fly (requires web connection)

    """

    from optparse import OptionParser, OptionGroup
    from os.path import exists as exist
    from obspy import UTCDateTime
    from numpy import nan

    parser = OptionParser(
        usage="Usage: %prog [options] <station database>",
        description="Script used to plot receiver function data ")

    # General Settings
    parser.add_option(
        "--keys",
        action="store",
        type=str,
        dest="stkeys",
        default="",
        help="Specify a comma separated list of station keys for " +
        "which to perform the analysis. These must be " +
        "contained within the station database. Partial keys will " +
        "be used to match against those in the dictionary. For " +
        "instance, providing IU will match with all stations in " +
        "the IU network [Default processes all stations in the database]")
    parser.add_option(
        "-v", "-V", "--verbose",
        action="store_true",
        dest="verb",
        default=False,
        help="Specify to increase verbosity.")
    parser.add_option(
        "-O", "--overwrite",
        action="store_true",
        dest="ovr",
        default=False,
        help="Force the overwriting of pre-existing figures. " +
        "[Default False]")

    PreGroup = OptionGroup(
        parser,
        title='Pre-processing Settings',
        description="Options for pre-processing of receiver function " +
        "data before plotting")
    PreGroup.add_option(
        "--snr",
        action="store",
        type=float,
        dest="snr",
        default=5.,
        help="Specify the SNR threshold for extracting receiver functions. " +
        "[Default 5.]")

## JMG
    PreGroup.add_option(
        "--snrh",
        action="store",
        type=float,
        dest="snrh",
        default=5.,
        help="Specify the horizontal component SNR threshold for extracting receiver functions. " +
        "[Default 5.]")
## JMG

    PreGroup.add_option(
        "--cc",
        action="store",
        type=float,
        dest="cc",
        default=0.5,
        help="Specify the CC threshold for extracting receiver functions. " +
        "[Default 0.5]")
    PreGroup.add_option(
        "--fmin",
        action="store",
        type=float,
        dest="fmin",
        default=0.05,
        help="Specify the low frequency corner for the bandpass filter. " +
        "[Default [0.05]]")
    PreGroup.add_option(
        "--fmax",
        action="store",
        type=float,
        dest="fmax",
        default=0.5,
        help="Specify the high frequency corner for the bandpass filter. " +
        "[Default [0.5]]")
    PreGroup.add_option(
        "--nbaz",
        action="store",
        dest="nbaz",
        type=int,
        default=None,
        help="Specify integer number of back-azimuth bins to consider " +
        "(typically 36 or 72). If not None, the plot will show receiver " +
        "functions sorted by back-azimuth values. [Default None]")
    PreGroup.add_option(
        "--nslow",
        action="store",
        dest="nslow",
        type=int,
        default=None,
        help="Specify integer number of slowness bins to consider " +
        "(typically 20 or 40). If not None, the plot will show receiver " +
        "functions sorted by slowness values. [Default None]")
## JMG ##
    PreGroup.add_option(
        "--slowbound",
        action="store",
        dest="slowbound",
        type=str,
        default=None,
        help="Specify a list of two floats with minimum and maximum" +
        "bounds on slowness (s/km). [Default [0.04, 0.08]]")
    PreGroup.add_option(
        "--bazbound",
        action="store",
        dest="bazbound",
        type=str,
        default=None,
        help="Specify a list of two floats with minimum and maximum" +
        "bounds on back azimuth (degrees). [Default [0, 360]]")
    PreGroup.add_option(
        "--phase",
        action="store",
        type=str,
        dest="phase",
        default=None,
        help="Specify the phase name to plot.  "+
        "Options are 'P' or 'PP'. [Default Both]")
## JMG ##

    PlotGroup = OptionGroup(
        parser,
        title='Plot Settings',
        description="Options for plot format")
    PlotGroup.add_option(
        "--scale",
        action="store",
        dest="scale",
        default=None,
        type=float,
        help="Specify the scaling factor for the amplitude of the "+
        "receiver functions in the wiggle plots. [Default 100. for "+
        "a back-azimuth plot, 0.02 for a slowness plot]")
    PlotGroup.add_option(
        "--tmax",
        action="store",
        default=30.,
        type=float,
        dest="tmax",
        help="Specify the maximum time on the x-axis for plotting (sec). "+
        "[Default 30.]")
    PlotGroup.add_option(
        "--stacked",
        action="store_true",
        dest="stacked",
        default=False,
        help="Set this option to plot a stack of all traces in top panel. "+
        "[Default does not plot stacked traces]")
    PlotGroup.add_option(
        "--save",
        action="store_true",
        dest="saveplot",
        default=False,
        help="Set this option if you wish to save the figure. [Default " +
        "does not save figure]")
    PlotGroup.add_option(
        "--title",
        action="store",
        dest="titleplot",
        type=str,
        default='',
        help="Specify title of figure. [Default None]")
    PlotGroup.add_option(
        "--format",
        action="store",
        type=str,
        dest="form",
        default="png",
        help="Specify format of figure. Can be any one of the valid" +
        "matplotlib formats: 'png', 'jpg', 'eps', 'pdf'. [Default 'png']")

    parser.add_option_group(PreGroup)
    parser.add_option_group(PlotGroup)

    (opts, args) = parser.parse_args()

    # Check inputs
    if len(args) != 1:
        parser.error("Need station database file")
    indb = args[0]
    if not exist(indb):
        parser.error("Input file " + indb + " does not exist")


## JMG ##
    if opts.slowbound is None:
        opts.slowbound = [0.04, 0.08]
    else:
        opts.slowbound = [float(val) for val in opts.slowbound.split(',')]
        opts.slowbound = sorted(opts.slowbound)
        if (len(opts.slowbound)) != 2:
            parser.error(
                "Error: --slowbound should contain 2 " +
                "comma-separated floats")
    
    if opts.bazbound is None:
        opts.bazbound = [0.0, 360.0]
    else:
        opts.bazbound = [float(val) for val in opts.bazbound.split(',')]
        opts.bazbound = sorted(opts.bazbound)
        if (len(opts.bazbound)) != 2:
            parser.error(
                "Error: --bazbound should contain 2 " +
                "comma-separated floats")
## JMG ##


    # create station key list
    if len(opts.stkeys) > 0:
        opts.stkeys = opts.stkeys.split(',')

    if opts.nbaz is None and opts.nslow is None:
        parser.error("Specify at least one of --nbaz or --nslow")
    elif opts.nbaz is not None and opts.nslow is not None:
        parser.error("Specify only one of --nbaz or --nslow")

    return (opts, indb)


def list_local_data_stn(lcldrs=list, sta=None, net=None, altnet=[]):
    """
    Function to take the list of local directories and recursively 
    find all data that matches the station name

    Parameters
    ----------
    lcldrs : List
        List of local directories
    sta : Dict
        Station metadata from :mod:`~StDb`
    net : str
        Network name
    altnet : List
        List of alternative networks

    Returns
    -------
    fpathmatch : List
        Sorted list of matched directories

    """
    from fnmatch import filter
    from os import walk
    from os.path import join

    if sta is None:
        return []
    else:
        if net is None:
            sstrings = ['*.{0:s}.*.SAC'.format(sta)]
        else:
            sstrings = ['*.{0:s}.{1:s}.*.SAC'.format(net, sta)]
            if len(altnet) > 0:
                for anet in altnet:
                    sstrings.append('*.{0:s}.{1:s}.*.SAC'.format(anet, sta))

    fpathmatch = []
    # Loop over all local data directories
    for lcldr in lcldrs:
        # Recursiely walk through directory
        for root, dirnames, filenames in walk(lcldr):
            # Keep paths only for those matching the station
            for sstring in sstrings:
                for filename in filter(filenames, sstring):
                    fpathmatch.append(join(root, filename))

    fpathmatch.sort()

    return fpathmatch


def parse_localdata_for_comp(comp='Z', stdata=[], sta=None,
                             start=UTCDateTime, end=UTCDateTime, ndval=nan):
    """
    Function to determine the path to data for a given component and alternate network

    Parameters
    ----------
    comp : str
        Channel for seismogram (one letter only)
    stdata : List
        Station list
    sta : Dict
        Station metadata from :mod:`~StDb` data base
    start : :class:`~obspy.core.utcdatetime.UTCDateTime`
        Start time for request
    end : :class:`~obspy.core.utcdatetime.UTCDateTime`
        End time for request
    ndval : float or nan
        Default value for missing data

    Returns
    -------
    err : bool
        Boolean for error handling (`False` is associated with success)
    st : :class:`~obspy.core.Stream`
        Stream containing North, East and Vertical components of motion

    """

    from fnmatch import filter

    # Get start and end parameters
    styr = start.strftime("%Y")
    stjd = start.strftime("%j")
    edyr = end.strftime("%Y")
    edjd = end.strftime("%j")

    # Intialize to default positive error
    erd = True

    print(
        ("*          {0:2s}{1:1s} - Checking Disk".format(sta.channel.upper(),
                                                          comp.upper())))

    # Time Window Spans Single Day
    if stjd == edjd:
        # Format 1
        lclfiles = list(filter(
            stdata,
            '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.{4:2s}{5:1s}.SAC'.format(
                styr, stjd, sta.network.upper(
                ), sta.station.upper(), sta.channel.upper()[0:2],
                comp.upper())))
        # Format 2
        if len(lclfiles) == 0:
            lclfiles = list(filter(
                stdata,
                '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.*{4:1s}.SAC'.format(
                    styr, stjd, sta.network.upper(), sta.station.upper(),
                    comp.upper())))

        # Alternate Nets (for CN/PO issues) Format 1
        if len(lclfiles) == 0:
            lclfiles = []
            for anet in sta.altnet:
                lclfiles.extend(
                    list(
                        filter(
                            stdata,
                            '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.' +
                            '{4:2s}{5:1s}.SAC'.format(
                                styr, stjd, anet.upper(), sta.station.upper(),
                                sta.channel.upper()[0:2], comp.upper()))))

        # Alternate Nets (for CN/PO issues) Format 2
        if len(lclfiles) == 0:
            # Check Alternate Networks
            lclfiles = []
            for anet in sta.altnet:
                lclfiles.extend(
                    list(
                        filter(
                            stdata,
                            '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.*' +
                            '{4:1s}.SAC'.format(
                                styr, stjd, sta.network.upper(),
                                sta.station.upper(), comp.upper()))))

        # If still no Local files stop
        if len(lclfiles) == 0:
            print("*              - Data Unavailable")
            return erd, None

        # Process the local Files
        for sacfile in lclfiles:
            # Read File
            st = read(sacfile)
            # st = read(sacfile, format="SAC")

            # Should only be one component, otherwise keep reading If more
            # than 1 component, error
            if len(st) != 1:
                pass

            else:
                # Check for NoData and convert to NaN
                stnd = st[0].stats.sac['user9']
                eddt = False
                if (not stnd == 0.0) and (not stnd == -12345.0):
                    st[0].data[st[0].data == stnd] = ndval
                    eddt = True

                # Check start/end times in range
                if (st[0].stats.starttime <= start and
                        st[0].stats.endtime >= end):
                    st.trim(starttime=start, endtime=end)

                    # Check for Nan in stream
                    if True in isnan(st[0].data):
                        print(
                            "*          !!! Missing Data Present !!! " +
                            "Skipping (NaNs)")
                    else:
                        if eddt and (ndval == 0.0):
                            if any(st[0].data == 0.0):
                                print(
                                    "*          !!! Missing Data Present " +
                                    "!!! (Set to Zero)")

                        st[0].stats.update()
                        tloc = st[0].stats.location
                        if len(tloc) == 0:
                            tloc = "--"

                        # Processed succesfully...Finish
                        print(("*          {1:3s}.{2:2s}  - From Disk".format(
                            st[0].stats.station, st[0].stats.channel.upper(),
                            tloc)))
                        return False, st

    # Time Window spans Multiple days
    else:
        # Day 1 Format 1
        lclfiles1 = list(
            filter(stdata,
                   '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.{4:2s}{5:1s}.SAC'.format(
                       styr, stjd, sta.network.upper(), sta.station.upper(),
                       sta.channel.upper()[0:2], comp.upper())))
        # Day 1 Format 2
        if len(lclfiles1) == 0:
            lclfiles1 = list(
                filter(stdata,
                       '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.*{4:1s}.SAC'.format(
                           styr, stjd, sta.network.upper(),
                           sta.station.upper(), comp.upper())))
        # Day 1 Alternate Nets (for CN/PO issues) Format 1
        if len(lclfiles1) == 0:
            lclfiles1 = []
            for anet in sta.altnet:
                lclfiles1.extend(
                    list(
                        filter(
                            stdata,
                            '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.' +
                            '{4:2s}{5:1s}.SAC'.format(
                                styr, stjd, anet.upper(), sta.station.upper(
                                ), sta.channel.upper()[0:2],
                                comp.upper()))))
        # Day 1 Alternate Nets (for CN/PO issues) Format 2
        if len(lclfiles1) == 0:
            lclfiles1 = []
            for anet in sta.altnet:
                lclfiles1.extend(
                    list(
                        filter(
                            stdata,
                            '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.*{4:1s}.SAC'.format(
                                styr, stjd, anet.upper(),
                                sta.station.upper(), comp.upper()))))

        # Day 2 Format 1
        lclfiles2 = list(
            filter(stdata,
                   '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.{4:2s}{5:1s}.SAC'.format(
                       edyr, edjd, sta.network.upper(
                       ), sta.station.upper(), sta.channel.upper()[0:2],
                       comp.upper())))
        # Day 2 Format 2
        if len(lclfiles2) == 0:
            lclfiles2 = list(
                filter(stdata,
                       '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.*' +
                       '{4:1s}.SAC'.format(
                           edyr, edjd, sta.network.upper(),
                           sta.station.upper(),
                           comp.upper())))
        # Day 2 Alternate Nets (for CN/PO issues) Format 1
        if len(lclfiles2) == 0:
            lclfiles2 = []
            for anet in sta.altnet:
                lclfiles2.extend(
                    list(
                        filter(
                            stdata,
                            '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.' +
                            '{4:2s}{5:1s}.SAC'.format(
                                edyr, edjd, anet.upper(), sta.station.upper(),
                                sta.channel.upper()[0:2], comp.upper()))))
        # Day 2 Alternate Nets (for CN/PO issues) Format 2
        if len(lclfiles2) == 0:
            lclfiles2 = []
            for anet in sta.altnet:
                lclfiles2.extend(
                    list(
                        filter(
                            stdata,
                            '*/{0:4s}.{1:3s}.{2:s}.{3:s}.*.*{4:1s}.SAC'.format(
                                edyr, edjd, anet.upper(), sta.station.upper(),
                                comp.upper()))))

        # If still no Local files stop
        if len(lclfiles1) == 0 and len(lclfiles2) == 0:
            print("*              - Data Unavailable")
            return erd, None

        # Now try to merge the two separate day files
        if len(lclfiles1) > 0 and len(lclfiles2) > 0:
            # Loop over first day file options
            for sacf1 in lclfiles1:
                st1 = read(sacf1, format='SAC')
                # Loop over second day file options
                for sacf2 in lclfiles2:
                    st2 = read(sacf2, format='SAC')

                    # Check time overlap of the two files.
                    if st1[0].stats.endtime >= \
                            st2[0].stats.starttime-st2[0].stats.delta:
                        # Check for NoData and convert to NaN
                        st1nd = st1[0].stats.sac['user9']
                        st2nd = st2[0].stats.sac['user9']
                        eddt1 = False
                        eddt2 = False
                        if (not st1nd == 0.0) and (not st1nd == -12345.0):
                            st1[0].data[st1[0].data == st1nd] = ndval
                            eddt1 = True
                        if (not st2nd == 0.0) and (not st2nd == -12345.0):
                            st2[0].data[st2[0].data == st2nd] = ndval
                            eddt2 = True

                        st = st1 + st2
                        # Need to work on this HERE (AJS OCT 2015).
                        # If Calibration factors are different,
                        try:
                                # then the traces cannot be merged.
                            st.merge()

                            # Should only be one component, otherwise keep
                            # reading If more than 1 component, error
                            if len(st) != 1:
                                print(st)
                                print("merge failed?")

                            else:
                                if (st[0].stats.starttime <= start and
                                        st[0].stats.endtime >= end):
                                    st.trim(starttime=start, endtime=end)

                                    # Check for Nan in stream
                                    if True in isnan(st[0].data):
                                        print(
                                            "*          !!! Missing Data " +
                                            "Present !!! Skipping (NaNs)")
                                    else:
                                        if (eddt1 or eddt2) and (ndval == 0.0):
                                            if any(st[0].data == 0.0):
                                                print(
                                                    "*          !!! Missing " +
                                                    "Data Present !!! (Set " +
                                                    "to Zero)")

                                        st[0].stats.update()
                                        tloc = st[0].stats.location
                                        if len(tloc) == 0:
                                            tloc = "--"

                                        # Processed succesfully...Finish
                                        print(("*          {1:3s}.{2:2s}  - " +
                                               "From Disk".format(
                                                   st[0].stats.station,
                                                   st[0].stats.channel.upper(),
                                                   tloc)))
                                        return False, st

                        except:
                            pass
                    else:
                        print(("*                 - Merge Failed: No " +
                               "Overlap {0:s} - {1:s}".format(
                                   st1[0].stats.endtime,
                                   st2[0].stats.starttime -
                                   st2[0].stats.delta)))

    # If we got here, we did not get the data.
    print("*              - Data Unavailable")
    return erd, None


def download_data(client=None, sta=None, start=UTCDateTime, end=UTCDateTime,
                  stdata=[], ndval=nan, new_sr=0.):
    """
    Function to build a stream object for a seismogram in a given time window either
    by downloading data from the client object or alternatively first checking if the
    given data is already available locally.

    Note 
    ----
    Currently only supports NEZ Components!

    Parameters
    ----------
    client : :class:`~obspy.client.fdsn.Client`
        Client object
    sta : Dict
        Station metadata from :mod:`~StDb` data base
    start : :class:`~obspy.core.utcdatetime.UTCDateTime`
        Start time for request
    end : :class:`~obspy.core.utcdatetime.UTCDateTime`
        End time for request
    stdata : List
        Station list
    ndval : float or nan
        Default value for missing data

    Returns
    -------
    err : bool
        Boolean for error handling (`False` is associated with success)
    trN : :class:`~obspy.core.Trace`
        Trace of North component of motion
    trE : :class:`~obspy.core.Trace`
        Trace of East component of motion
    trZ : :class:`~obspy.core.Trace` 
        Trace of Vertical component of motion

    """

    from fnmatch import filter
    from obspy import read, Stream
    from os.path import dirname, join, exists
    from numpy import any

    # Output
    print(("*     {0:s}.{1:2s} - ZNE:".format(sta.station,
                                              sta.channel.upper())))

    # Set Error Default to True
    erd = True

    # Check if there is local data
    if len(stdata) > 0:
        # Only a single day: Search for local data
        # Get Z localdata
        errZ, stZ = parse_localdata_for_comp(
            comp='Z', stdata=stdata, sta=sta, start=start, end=end,
            ndval=ndval)
        # Get N localdata
        errN, stN = parse_localdata_for_comp(
            comp='N', stdata=stdata, sta=sta, start=start, end=end,
            ndval=ndval)
        # Get E localdata
        errE, stE = parse_localdata_for_comp(
            comp='E', stdata=stdata, sta=sta, start=start, end=end,
            ndval=ndval)
        # Retreived Succesfully?
        erd = errZ or errN or errE
        if not erd:
            # Combine Data
            st = stZ + stN + stE

    # No local data? Request using client
    if erd:
        erd = False

        for loc in sta.location:
            tloc = loc
            # Construct location name
            if len(tloc) == 0:
                tloc = "--"
            # Construct Channel List
            channelsZNE = sta.channel.upper() + 'Z,' + sta.channel.upper() + \
                'N,' + sta.channel.upper() + 'E'
            print(("*          {1:2s}[ZNE].{2:2s} - Checking Network".format(
                sta.station, sta.channel.upper(), tloc)))

            try:
                st = client.get_waveforms(
                    network=sta.network,
                    station=sta.station, location=loc,
                    channel=channelsZNE, starttime=start,
                    endtime=end, attach_response=False)
                if len(st) == 3:
                    print("*              - ZNE Data Downloaded")

                # it's possible if len(st)==1 that data is Z12
                else:
                    # Construct Channel List
                    channelsZ12 = sta.channel.upper() + 'Z,' + \
                        sta.channel.upper() + '1,' + \
                        sta.channel.upper() + '2'
                    msg = "*          {1:2s}[Z12].{2:2s} - Checking Network".format(
                        sta.station, sta.channel.upper(), tloc)
                    print(msg)
                    try:
                        st = client.get_waveforms(
                            network=sta.network,
                            station=sta.station, location=loc,
                            channel=channelsZ12, starttime=start,
                            endtime=end, attach_response=False)
                        if len(st) == 3:
                            print("*              - Z12 Data Downloaded")
                        else:
                            st = None
                    except:
                        st = None
            except:
                st = None

            # Break if we successfully obtained 3 components in st
            if not erd:

                break

    # Check the correct 3 components exist
    if st is None:
        print("* Error retrieving waveforms")
        print("**************************************************")
        return True, None

    # Three components successfully retrieved
    else:

        try:
            st.trim(start, end, pad=True, fill_value=0.)
        except:
            try:
                st.trim(start, end)
            except:
                return True, None

        trA = st[0].copy()
        trB = st[1].copy()
        trC = st[2].copy()

        # Check trace lengths
        lenA = len(trA.data)
        lenB = len(trB.data)
        lenC = len(trC.data)

        if not (lenA == lenB and lenA == lenC):
            print("* Lengths are incompatible: ", lenA, lenB, lenC)
            print("* -> Aborting")
            print("**************************************************")
            return True, None

        else:
            print("* Waveforms Retrieved...")
            return False, st
