import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import os, sys, glob
import argparse

if __name__ == '__main__':

    # Parsing arguments
    parser = argparse.ArgumentParser(description='Plotting LPGBT EYE')
    parser.add_argument("-d", "--dir", action="store", dest="dir", help="dir = DIRECTORY for EYE SCAN RESULTS")
    args = parser.parse_args()

    current_dir = os.path.abspath(os.getcwd())
    if args.dir is None:
        print ("Give a directory for eye scan results")
        sys.exit()
    if not os.path.isdir(os.path.join(current_dir, args.dir)):
        print ("Give a valid directory")
        sys.exit()
    eye_data_dir = os.path.join(current_dir, args.dir)
    os.system("rm -rf " + eye_data_dir + "/*_out.txt")
    for eye_data_filepath in glob.glob(os.path.join(eye_data_dir, "*.txt")):
        print ("File: " + eye_data_filepath.split("/")[-1])
        eye_data_file = open(eye_data_filepath)
        eye_data = []
        for line in eye_data_file.readlines():
            if "eye_data" in line:
                continue
            line = line.split("[")[1]
            if "]," in line:
                line = line.split("],")[0]
            elif "]]" in line:
                line = line.split("]]")[0]
            data_list = line.split(",")
            data_int =  []
            for data in data_list:
                data_int.append(int(data))
            eye_data.append(data_int)
        eye_data_file.close()

        n_total = 0
        n_open = 0
        for y in eye_data:
            n_total += len(y)
            for x in y:
                if x<10:
                    n_open+=1
        frac_open = float(n_open)/float(n_total)
        print ("Fraction of eye open = " + str(frac_open) + "\n")
        file_output = open(os.path.join(eye_data_dir, eye_data_filepath.split(".txt")[0]+"_out.txt"), "w")
        file_output.write("Fraction of eye open = " + str(frac_open) + "\n")
        file_output.close()

        (fig, axs) = plt.subplots(1, 1, figsize=(10, 8))
        print ("fig type = " + str(type(fig)))
        print ("axs type = " + str(type(axs)))
        axs.set_title("LpGBT 2.56 Gbps RX Eye Opening Monitor")
        plot = axs.imshow(eye_data, alpha=0.9, vmin=0, vmax=100, cmap='jet',interpolation="nearest", aspect="auto",extent=[-384.52/2,384.52/2,-0.6,0.6,])
        plt.xlabel('ps')
        plt.ylabel('volts')
        fig.colorbar(plot, ax=axs)
        plt.savefig(os.path.join(eye_data_dir, eye_data_filepath.split(".txt")[0]+".pdf"))
        print ("")
