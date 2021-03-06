#!/usr/bin/env python

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


# Import modules and functions
import numpy as np
import pickle
import stdb
from obspy import Stream
from rfpy import arguments, binning, plotting
from pathlib import Path


def main():

    print()
    print("#################################################")
    print("#        __                        _       _    #")
    print("#  _ __ / _|_ __  _   _      _ __ | | ___ | |_  #")
    print("# | '__| |_| '_ \| | | |    | '_ \| |/ _ \| __| #")
    print("# | |  |  _| |_) | |_| |    | |_) | | (_) | |_  #")
    print("# |_|  |_| | .__/ \__, |____| .__/|_|\___/ \__| #")
    print("#          |_|    |___/_____|_|                 #")
    print("#                                               #")
    print("#################################################")
    print()

    # Run Input Parser
    args = arguments.get_plot_arguments()

    # Load Database
    db = stdb.io.load_db(fname=indb)

    # Construct station key loop
    allkeys = db.keys()

    # Extract key subset
    if len(args.stkeys) > 0:
        stkeys = []
        for skey in args.stkeys:
            stkeys.extend([s for s in allkeys if skey in s])
    else:
        stkeys = db.keys()

    # Loop over station keys
    for stkey in list(stkeys):

        # Extract station information from dictionary
        sta = db[stkey]

        # Define path to see if it exists
        if args.phase in ['P', 'PP', 'allP']:
            datapath = Path('P_DATA') / stkey
        elif args.phase in ['S', 'SKS', 'allS']:
            datapath = Path('S_DATA') / stkey
        if not datapath.is_dir():
            print('Path to ' + str(datapath) + ' doesn`t exist - continuing')
            continue

        # Temporary print locations
        tlocs = sta.location
        if len(tlocs) == 0:
            tlocs = ['']
        for il in range(0, len(tlocs)):
            if len(tlocs[il]) == 0:
                tlocs[il] = "--"
        sta.location = tlocs

        # Update Display
        print(" ")
        print("|===============================================|")
        print("|                   {0:>8s}                    |".format(
            sta.station))
        print("|===============================================|")
        print("|  Station: {0:>2s}.{1:5s}                            |".format(
            sta.network, sta.station))
        print("|      Channel: {0:2s}; Locations: {1:15s}  |".format(
            sta.channel, ",".join(tlocs)))
        print("|      Lon: {0:7.2f}; Lat: {1:6.2f}                |".format(
            sta.longitude, sta.latitude))
        print("|-----------------------------------------------|")

        rfRstream = Stream()
        rfTstream = Stream()

        datafiles = [x for x in datapath.iterdir() if x.is_dir()]
        for folder in datafiles:

            # Skip hidden folders
            if folder.name.startswith('.'):
                continue

            # Load meta data
            filename = folder / "Meta_Data.pkl"
            if not filename.is_file():
                continue
            metafile = open(filename, 'rb')
            meta = pickle.load(metafile)
            metafile.close()

            # Skip data not in list of phases
            if meta.phase not in args.listphase:
                continue

            # QC Thresholding
            if meta.snrh < args.snrh:
                continue
            if meta.snr < args.snr:
                continue
            if meta.cc < args.cc:
                continue

            # Check bounds on data
            if meta.slow < args.slowbound[0] or meta.slow > args.slowbound[1]:
                continue
            if meta.baz < args.bazbound[0] or meta.baz > args.bazbound[1]:
                continue

            # If everything passed, load the RF data
            filename = folder / "RF_Data.pkl"
            if filename.is_file():
                file = open(filename, "rb")
                rfdata = pickle.load(file)
                if args.phase in ['P', 'PP', 'allP']:
                    Rcmp = 1
                    Tcmp = 2
                elif args.phase in ['S', 'SKS', 'allS']:
                    Rcmp = 1
                    Tcmp = 2
                rfRstream.append(rfdata[Rcmp])
                rfTstream.append(rfdata[Tcmp])
                file.close()

        if len(rfRstream) == 0:
            continue

        if args.no_outl:

            varR = []
            for i in range(len(rfRstream)):
                taxis = rfRstream[i].stats.taxis
                tselect = (taxis > args.trange[0]) & (taxis < args.trange[1])
                varR.append(np.var(rfRstream[i].data[tselect]))
            varR = np.array(varR)

            # Remove outliers wrt variance within time range
            medvarR = np.median(varR)
            madvarR = 1.4826*np.median(np.abs(varR-medvarR))
            robustR = np.abs((varR-medvarR)/madvarR)
            outliersR = np.arange(len(rfRstream))[robustR > 2.5]
            for i in outliersR[::-1]:
                rfRstream.remove(rfRstream[i])
                rfTstream.remove(rfTstream[i])

            # Do the same for transverse
            varT = []
            for i in range(len(rfRstream)):
                taxis = rfRstream[i].stats.taxis
                tselect = (taxis > args.trange[0]) & (taxis < args.trange[1])
                varT.append(np.var(rfTstream[i].data[tselect]))
            varT = np.array(varT)

            medvarT = np.median(varT)
            madvarT = 1.4826*np.median(np.abs(varT-medvarT))
            robustT = np.abs((varT-medvarT)/madvarT)
            outliersT = np.arange(len(rfTstream))[robustT > 2.5]
            for i in outliersT[::-1]:
                rfRstream.remove(rfRstream[i])
                rfTstream.remove(rfTstream[i])

        # Filter
        if args.bp:
            rfRstream.filter('bandpass', freqmin=args.bp[0],
                             freqmax=args.bp[1], corners=2,
                             zerophase=True)
            rfTstream.filter('bandpass', freqmin=args.bp[0],
                             freqmax=args.bp[1], corners=2,
                             zerophase=True)

        if args.saveplot and not Path('RF_PLOTS').is_dir():
            Path('RF_PLOTS').mkdir()

        print('')
        print("Number of radial RF data: " + str(len(rfRstream)))
        print("Number of transverse RF data: " + str(len(rfTstream)))
        print('')

        if args.nbaz:
            # Bin according to BAZ
            rf_tmp = binning.bin(rfRstream, rfTstream,
                                 typ='baz', nbin=args.nbaz+1,
                                 pws=args.pws)

        elif args.nslow:
            # Bin according to slowness
            rf_tmp = binning.bin(rfRstream, rfTstream,
                                 typ='slow', nbin=args.nslow+1,
                                 pws=args.pws)

        # Check bin counts:
        for tr in rf_tmp[0]:
            if (tr.stats.nbin < args.binlim):
                rf_tmp[0].remove(tr)
        for tr in rf_tmp[1]:
            if (tr.stats.nbin < args.binlim):
                rf_tmp[1].remove(tr)

        # Show a stacked trace on top OR normalize option specified
        if args.stacked or args.norm:
            st_tmp = binning.bin_all(rf_tmp[0], rf_tmp[1], pws=args.pws)
            tr1 = st_tmp[0]
            tr2 = st_tmp[1]
            # Find normalization constant
            normR = np.amax(np.abs(
                tr1.data[(taxis > args.trange[0]) & (taxis < args.trange[1])]))
            normT = np.amax(np.abs(
                tr2.data[(taxis > args.trange[0]) & (taxis < args.trange[1])]))
            norm = np.max([normR, normT])
        else:
            norm = None
            tr1 = None
            tr2 = None

        # Now plot
        if args.nbaz:
            plotting.wiggle_bins(rf_tmp[0], rf_tmp[1], tr1=tr1, tr2=tr2,
                                 btyp='baz', scale=args.scale,
                                 tmin=args.trange[0], tmax=args.trange[1],
                                 norm=norm, save=args.saveplot,
                                 title=args.titleplot, form=args.form)
        elif args.nslow:
            plotting.wiggle_bins(rf_tmp[0], rf_tmp[1], tr1=tr1, tr2=tr2,
                                 btyp='slow', scale=args.scale,
                                 tmin=args.trange[0], tmax=args.trange[1],
                                 norm=norm, save=args.saveplot,
                                 title=args.titleplot, form=args.form)

        # Event distribution
        if args.plot_event_dist:
            plotting.event_dist(rfRstream, phase=args.phase, save=args.saveplot,
                                title=args.titleplot, form=args.form)

if __name__ == "__main__":

    # Run main program
    main()
